#!/usr/bin/env python3
"""Build private, reference-closed nuScenes metadata subsets from frozen logs.

This produces real SDK tables, not trained models or an object point database.
Map pixels and static taxonomies remain shared context. Only map.log_tokens is
projected; all other selected row values, including decimals, are preserved.
"""
from __future__ import annotations

import argparse
import ast
from decimal import Decimal
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tarfile

from audit_cache_selection import rows_from_tables
from inventory_training_sensors import CHANNELS, digest, relative_file
from prepare_training_overlap_probe import literal
from replay_reference_population_audit import read_json

VERSION = "0.1.1"
# Indexed scalar columns are duplicated from the preserved JSON, never inferred.
FIELDS = {
    "category": (), "attribute": (), "visibility": (),
    "sensor": ("channel",), "calibrated_sensor": ("sensor_token",),
    "ego_pose": (), "log": (), "map": (),
    "scene": ("log_token", "name", "nbr_samples", "first_sample_token", "last_sample_token"),
    "sample": ("scene_token", "timestamp", "prev", "next"),
    "instance": ("category_token", "nbr_annotations", "first_annotation_token", "last_annotation_token"),
    "sample_data": ("sample_token", "ego_pose_token", "calibrated_sensor_token", "timestamp",
                    "is_key_frame", "filename", "prev", "next"),
    "sample_annotation": ("sample_token", "instance_token", "visibility_token", "prev", "next"),
}
INTEGERS = {"nbr_samples", "nbr_annotations", "timestamp", "is_key_frame"}
FOREIGN = {
    "scene": {"log_token": "log", "first_sample_token": "sample", "last_sample_token": "sample"},
    "sample": {"scene_token": "scene", "prev": "sample", "next": "sample"},
    "instance": {"category_token": "category", "first_annotation_token": "sample_annotation",
                 "last_annotation_token": "sample_annotation"},
    "sample_data": {"sample_token": "sample", "ego_pose_token": "ego_pose",
                    "calibrated_sensor_token": "calibrated_sensor", "prev": "sample_data", "next": "sample_data"},
    "sample_annotation": {"sample_token": "sample", "instance_token": "instance",
                          "visibility_token": "visibility", "prev": "sample_annotation", "next": "sample_annotation"},
    "calibrated_sensor": {"sensor_token": "sensor"},
}
OPTIONAL = {"prev", "next", "visibility_token"}


def exact_json(value):
    """Encode finite decimal values without binary float conversion."""
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("nonfinite decimal")
        return str(value)
    if type(value) in (str, int, bool) or value is None:
        return json.dumps(value, ensure_ascii=True, allow_nan=False)
    if isinstance(value, list):
        return "[" + ",".join(exact_json(v) for v in value) + "]"
    if isinstance(value, dict) and all(isinstance(k, str) for k in value):
        return "{" + ",".join(exact_json(k) + ":" + exact_json(value[k]) for k in sorted(value)) + "}"
    raise ValueError("unsupported JSON value")


def reject_rows(db, sql, reason, args=()):
    if db.execute(sql + " LIMIT 1", args).fetchone() is not None:
        raise ValueError(reason)


def reference_checks(db, prefix=""):
    for table, columns in FOREIGN.items():
        for field, target in columns.items():
            permitted_empty = f"a.{field} != '' AND " if field in OPTIONAL else ""
            reject_rows(db, f"SELECT a.token FROM {prefix}{table} a LEFT JOIN {prefix}{target} b "
                        f"ON a.{field}=b.token WHERE {permitted_empty}b.token IS NULL",
                        f"reference outside subset: {table}.{field}")
    reject_rows(db, f"SELECT a.token FROM {prefix}sample_annotation a, "
                f"json_each(a.body, '$.attribute_tokens') e LEFT JOIN {prefix}attribute b ON e.value=b.token "
                "WHERE b.token IS NULL", "reference outside subset: annotation attribute")


def structural_checks(db):
    reference_checks(db)
    for child, parent, key, number, first, last in (
        ("sample", "scene", "scene_token", "nbr_samples", "first_sample_token", "last_sample_token"),
        ("sample_annotation", "instance", "instance_token", "nbr_annotations", "first_annotation_token", "last_annotation_token"),
    ):
        reject_rows(db, f"SELECT p.token FROM {parent} p LEFT JOIN "
                    f"(SELECT {key} k, count(*) n FROM {child} GROUP BY {key}) c ON c.k=p.token "
                    f"LEFT JOIN {child} f ON f.token=p.{first} LEFT JOIN {child} l ON l.token=p.{last} "
                    f"WHERE c.n IS NULL OR c.n!=p.{number} OR f.{key}!=p.token OR l.{key}!=p.token "
                    "OR f.prev!='' OR l.next!=''", f"invalid {parent} count or endpoints")
        reject_rows(db, f"SELECT {key} FROM {child} GROUP BY {key} "
                    "HAVING sum(prev='')!=1 OR sum(next='')!=1", f"disconnected {child} chain")
    for table, key in (("sample", "scene_token"), ("sample_annotation", "instance_token"),
                       ("sample_data", "calibrated_sensor_token")):
        for field, reverse in (("prev", "next"), ("next", "prev")):
            reject_rows(db, f"SELECT a.token FROM {table} a JOIN {table} b ON a.{field}=b.token "
                        f"WHERE b.{reverse}!=a.token OR a.{key}!=b.{key}", f"invalid {table} {field} chain")
        if table != "sample_annotation":
            reject_rows(db, f"SELECT a.token FROM {table} a JOIN {table} b ON a.next=b.token "
                        "WHERE b.timestamp<=a.timestamp", f"nonincreasing {table} time")
    reject_rows(db, "SELECT a.token FROM sample_annotation a JOIN sample_annotation b ON a.next=b.token "
                "JOIN sample s ON s.token=a.sample_token JOIN sample t ON t.token=b.sample_token "
                "WHERE s.scene_token!=t.scene_token OR s.timestamp>=t.timestamp", "annotation crosses scene or time")
    reject_rows(db, "SELECT a.token FROM sample_data a JOIN sample_data b ON a.next=b.token "
                "JOIN sample s ON s.token=a.sample_token JOIN sample t ON t.token=b.sample_token "
                "WHERE s.scene_token!=t.scene_token", "sample-data chain crosses scene")
    reject_rows(db, "SELECT instance_token FROM sample_annotation GROUP BY instance_token, sample_token "
                "HAVING count(*)!=1", "duplicate instance in sample")
    reject_rows(db, "SELECT d.sample_token FROM sample_data d JOIN calibrated_sensor c "
                "ON c.token=d.calibrated_sensor_token JOIN sensor s ON s.token=c.sensor_token "
                "WHERE d.is_key_frame=1 GROUP BY d.sample_token,s.channel HAVING count(*)!=1",
                "duplicate keyframe channel")
    names = ",".join("?" for _ in CHANNELS)
    reject_rows(db, "SELECT f.token FROM sample f LEFT JOIN (SELECT d.sample_token,count(*) n FROM sample_data d "
                "JOIN calibrated_sensor c ON c.token=d.calibrated_sensor_token JOIN sensor s ON s.token=c.sensor_token "
                f"WHERE d.is_key_frame=1 AND s.channel IN ({names}) GROUP BY d.sample_token) k "
                "ON k.sample_token=f.token WHERE k.n IS NULL OR k.n!=7", "missing keyframe channel", CHANNELS)


def filename_aliases(db):
    """Retain the source's radar boundary aliases; reject other filename reuse.

    A scene-ending radar acquisition can be the next scene's first acquisition
    within one collection log. This is two metadata identities for one path.
    The rule does not permit camera/lidar duplicates or cross-log exposure.
    """
    def row(table, token):
        return json.loads(db.execute(f"SELECT body FROM {table} WHERE token=?", (token,)).fetchone()[0],
                          parse_float=Decimal)

    groups, counts = 0, {}
    for _, tokens in db.execute("SELECT filename,json_group_array(token) FROM sample_data GROUP BY filename HAVING count(*)>1"):
        records = [row("sample_data", t) for t in json.loads(tokens)]
        if len(records) != 2:
            raise ValueError("unsupported filename alias multiplicity")
        scenes = [row("scene", row("sample", r["sample_token"])["scene_token"]) for r in records]
        cal = [row("calibrated_sensor", r["calibrated_sensor_token"]) for r in records]
        sensors = [row("sensor", c["sensor_token"]) for c in cal]
        poses = [row("ego_pose", r["ego_pose_token"]) for r in records]
        same_values = lambda values: {k: v for k, v in values[0].items() if k != "token"} == {k: v for k, v in values[1].items() if k != "token"}
        ends = sum(r["next"] == "" and r["sample_token"] == s["last_sample_token"] for r, s in zip(records, scenes))
        starts = sum(r["prev"] == "" and r["sample_token"] == s["first_sample_token"] for r, s in zip(records, scenes))
        if (any(s.get("modality") != "radar" for s in sensors) or sensors[0] != sensors[1]
                or any(not r["is_key_frame"] for r in records) or records[0]["timestamp"] != records[1]["timestamp"]
                or scenes[0]["log_token"] != scenes[1]["log_token"] or scenes[0]["token"] == scenes[1]["token"]
                or ends != 1 or starts != 1 or not same_values(cal) or not same_values(poses)):
            raise ValueError("unsupported filename alias boundary or exposure")
        groups += 1
        channel = sensors[0]["channel"]
        counts[channel] = counts.get(channel, 0) + 2
    return {"scope": "complete source metadata", "radar_boundary_filename_aliases": groups,
            "preserved_reference_rows": 2 * groups, "by_channel": counts, "cross_log_aliases": 0,
            "policy": "Two radar keyframes at different scene endpoints in one log, equal timestamp, sensor, pose and calibration values"}


def create_index(path, rows, inputs):
    # The complete marker is written only after the archive and checks finish.
    Path(path).touch(exist_ok=False)
    db = sqlite3.connect(path)
    try:
        db.execute("PRAGMA cache_size=-262144")
        db.execute("PRAGMA temp_store=FILE")
        for table, fields in FIELDS.items():
            cols = ",".join(f'{f} {"INTEGER" if f in INTEGERS else "TEXT"} NOT NULL' for f in fields)
            # Append payload rows and index their tokens separately. A large
            # JSON payload in the primary-key B-tree causes needless rewrites.
            db.execute(f"CREATE TABLE {table}(token TEXT PRIMARY KEY,body TEXT NOT NULL{',' + cols if cols else ''})")
        seen, count = set(), 0
        for name, row in rows:
            table = name.removesuffix(".json")
            if table not in FIELDS:
                raise ValueError("unexpected metadata table")
            seen.add(table)
            if not isinstance(row.get("token"), str) or not row["token"]:
                raise ValueError("invalid token")
            values = []
            for field in FIELDS[table]:
                v = row[field]
                if field == "is_key_frame":
                    if type(v) is not bool:
                        raise ValueError("invalid keyframe flag")
                elif field in INTEGERS:
                    if type(v) is not int or v <= 0:
                        raise ValueError("invalid count or timestamp")
                elif not isinstance(v, str) or (not v and field not in OPTIONAL):
                    raise ValueError("invalid metadata field")
                values.append(v)
            if table in ("sample_data", "map"):
                relative_file(row["filename"])
            if table in ("sample_annotation", "map"):
                key = "attribute_tokens" if table == "sample_annotation" else "log_tokens"
                v = row[key]
                if not isinstance(v, list) or any(not isinstance(t, str) or not t for t in v) or len(v) != len(set(v)):
                    raise ValueError("invalid reference list")
            placeholders = ",".join("?" for _ in range(2 + len(values)))
            db.execute(f"INSERT INTO {table} VALUES({placeholders})", (row["token"], exact_json(row), *values))
            count += 1
            if count % 50000 == 0:
                db.commit()
                print("indexed", count, table, file=sys.stderr, flush=True)
        if seen != set(FIELDS):
            raise ValueError("missing metadata table")
        db.commit()
        for table, fields in FIELDS.items():
            for field in fields:
                if field.endswith("_token") and not field.startswith(("first_", "last_")):
                    db.execute(f"CREATE INDEX {table}_{field} ON {table}({field})")
        db.execute("CREATE UNIQUE INDEX scene_name ON scene(name)")
        db.execute("CREATE UNIQUE INDEX sensor_channel ON sensor(channel)")
        db.execute("CREATE INDEX sample_data_filename ON sample_data(filename)")
        db.commit()
        print("checking source reference graph", file=sys.stderr, flush=True)
        structural_checks(db)
        aliases = filename_aliases(db)
        db.execute("CREATE TABLE provenance(body TEXT NOT NULL)")
        db.execute("INSERT INTO provenance VALUES(?)", (exact_json(dict(inputs, version=VERSION, complete=True, filename_aliases=aliases)),))
        db.commit()
    finally:
        db.close()


def select_subset(db, logs, scene_names):
    if not logs or not scene_names or len(logs) != len(set(logs)) or len(scene_names) != len(set(scene_names)):
        raise ValueError("invalid or duplicate partition member")
    db.execute("CREATE TEMP TABLE selected_logs(token TEXT PRIMARY KEY)")
    db.executemany("INSERT INTO selected_logs VALUES(?)", ((v,) for v in logs))
    reject_rows(db, "SELECT s.token FROM selected_logs s LEFT JOIN log l ON l.token=s.token WHERE l.token IS NULL",
                "unknown partition log")
    queries = {
        "log": "SELECT l.* FROM log l JOIN selected_logs s ON s.token=l.token",
        "scene": "SELECT r.* FROM scene r JOIN selected_logs l ON r.log_token=l.token",
        "sample": "SELECT r.* FROM sample r JOIN s_scene s ON r.scene_token=s.token",
        "sample_data": "SELECT r.* FROM sample_data r JOIN s_sample s ON r.sample_token=s.token",
        "sample_annotation": "SELECT r.* FROM sample_annotation r JOIN s_sample s ON r.sample_token=s.token",
        "instance": "SELECT * FROM instance WHERE token IN (SELECT instance_token FROM s_sample_annotation)",
        "ego_pose": "SELECT * FROM ego_pose WHERE token IN (SELECT ego_pose_token FROM s_sample_data)",
        "calibrated_sensor": "SELECT * FROM calibrated_sensor WHERE token IN (SELECT calibrated_sensor_token FROM s_sample_data)",
        "sensor": "SELECT * FROM sensor WHERE token IN (SELECT sensor_token FROM s_calibrated_sensor)",
        "category": "SELECT * FROM category", "attribute": "SELECT * FROM attribute", "visibility": "SELECT * FROM visibility",
    }
    # Small token tables let every cross-reference check use an index. The body
    # remains in the read-only source index rather than copied into another DB.
    for table, query in queries.items():
        db.execute(f"CREATE TEMP TABLE allowed_{table}(token TEXT PRIMARY KEY) WITHOUT ROWID")
        db.execute(f"INSERT INTO allowed_{table} SELECT token FROM ({query})")
        db.execute(f"CREATE TEMP VIEW s_{table} AS SELECT r.* FROM {table} r JOIN allowed_{table} a USING(token)")
    actual = {r[0] for r in db.execute("SELECT name FROM s_scene")}
    if actual != set(scene_names):
        raise ValueError("partition scene names differ from whole-log selection")
    reference_checks(db, "s_")
    return queries


def write_array(path, bodies):
    with path.open("x", encoding="utf8", newline="\n") as out:
        out.write("[\n")
        count = 0
        for body in bodies:
            if count:
                out.write(",\n")
            out.write(body)
            count += 1
        out.write("\n]\n")
    return {"rows": count, "bytes": path.stat().st_size, "sha256": digest(path)}


def materialize(index, index_sha, logs, scene_names, output, binding):
    if digest(index) != index_sha:
        raise ValueError("index identity differs")
    db = sqlite3.connect(Path(index).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        provenance = [json.loads(r[0]) for r in db.execute("SELECT body FROM provenance")]
        if len(provenance) != 1 or provenance[0].get("complete") is not True or provenance[0].get("version") != VERSION:
            raise ValueError("incomplete or unsupported index")
        select_subset(db, logs, scene_names)
        output.mkdir(exist_ok=False)
        tables = output / "v1.0-trainval"
        tables.mkdir()
        files = {}
        for table in FIELDS:
            if table == "map":
                continue
            files[table] = write_array(tables / (table + ".json"),
                                      (r[0] for r in db.execute(f"SELECT body FROM s_{table} ORDER BY token")))
        selected = set(logs)
        map_bodies, assigned, projections = [], set(), []
        for (body,) in db.execute("SELECT body FROM map ORDER BY token"):
            row = json.loads(body)
            kept = [v for v in row["log_tokens"] if v in selected]
            if not kept:
                continue
            if assigned & set(kept):
                raise ValueError("ambiguous log to map reference")
            assigned.update(kept)
            before = len(row["log_tokens"])
            row["log_tokens"] = kept
            map_bodies.append(exact_json(row))
            projections.append({"original_log_references": before, "selected_log_references": len(kept)})
        if assigned != selected:
            raise ValueError("missing log to map reference")
        files["map"] = write_array(tables / "map.json", map_bodies)
        if digest(index) != index_sha:
            raise ValueError("index changed during materialization")
        result = {"artifact_id": "reiyah.nuscenes-training-subset." + VERSION, "version": VERSION,
                  "lifecycle_status": "exploratory", "binding": binding, "index_sha256": index_sha,
                  "producer_sha256": digest(__file__), "source": provenance[0], "tables": files,
                  "log_count": len(logs), "scene_count": len(scene_names), "outside_subset_references": 0,
                  "map_reference_projection": projections,
                  "row_changes": "map.log_tokens projection only; selected non-map values preserved exactly",
                  "limits": ["Metadata only; no sensor decoding, detector fitting or object point database",
                             "Shared maps and taxonomies are not disjoint empirical exposure",
                             "Instance identities do not track physical objects across scenes",
                             "All sensor metadata retained; earlier file census covers only six camera keyframes and lidar",
                             "Prospective training/calibration/initialization protocol remains unresolved"]}
        (output / "result.json").write_text(exact_json(result) + "\n")
        return result
    finally:
        db.close()


def extract_maps(meta, meta_sha, output):
    if digest(meta) != meta_sha:
        raise ValueError("metadata identity differs")
    output.mkdir(exist_ok=False)
    result = {}
    with tarfile.open(meta, "r|gz") as archive:
        for member in archive:
            if not member.name.startswith("maps/") or not member.name.endswith(".png"):
                continue
            name = relative_file(member.name)
            if not member.isfile() or len(name.parts) != 2 or member.name in result:
                raise ValueError("invalid map payload member")
            dest = output / name
            dest.parent.mkdir(exist_ok=True)
            with dest.open("xb") as target:
                shutil.copyfileobj(archive.extractfile(member), target)
            result[member.name] = {"bytes": dest.stat().st_size, "sha256": digest(dest)}
    if not result or digest(meta) != meta_sha:
        raise ValueError("missing maps or changed archive")
    (output / "result.json").write_text(exact_json({"metadata_sha256": meta_sha, "files": result}) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    idx = subs.add_parser("index")
    maps = subs.add_parser("maps")
    for p in (idx, maps):
        p.add_argument("--meta", type=Path, required=True)
        p.add_argument("--meta-sha256", required=True)
        p.add_argument("--output", type=Path, required=True)
    sub = subs.add_parser("subset")
    sub.add_argument("--index", type=Path, required=True)
    sub.add_argument("--index-sha256", required=True)
    sub.add_argument("--splits", type=Path, required=True)
    sub.add_argument("--splits-sha256", required=True)
    sub.add_argument("--proposal", type=Path)
    sub.add_argument("--proposal-sha256")
    sub.add_argument("--partition", choices=("1", "2", "val"), required=True)
    sub.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    if a.command == "maps":
        extract_maps(a.meta, a.meta_sha256, a.output)
    elif a.command == "index":
        if digest(a.meta) != a.meta_sha256:
            raise ValueError("metadata identity differs")
        inputs = {"metadata_sha256": a.meta_sha256, "producer_sha256": digest(__file__),
                  "reader_sha256": digest(Path(__file__).with_name("audit_cache_selection.py")),
                  "array_reader_sha256": digest(Path(__file__).with_name("replay_reference_population_audit.py"))}
        def bound_rows():
            yield from rows_from_tables(a.meta, {t + ".json" for t in FIELDS})
            if digest(a.meta) != a.meta_sha256:
                raise ValueError("metadata changed during indexing")
        create_index(a.output, bound_rows(), inputs)
        print(exact_json({"inputs": inputs, "index_sha256": digest(a.output)}))
    else:
        if digest(a.splits) != a.splits_sha256 or digest(a.index) != a.index_sha256:
            raise ValueError("input identity differs")
        train, val = (literal(ast.parse(a.splits.read_text()), n) for n in ("train", "val"))
        if train & val:
            raise ValueError("official scene overlap")
        db = sqlite3.connect(a.index.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            scenes = {n: log for n, log in db.execute("SELECT name,log_token FROM scene")}
            sample_counts = dict(db.execute("SELECT name,nbr_samples FROM scene"))
        finally:
            db.close()
        if not train | val <= scenes.keys():
            raise ValueError("official scene missing")
        val_logs = {scenes[n] for n in val}
        binding = {"splits_sha256": a.splits_sha256, "partition": a.partition}
        if a.partition == "val":
            logs, names = sorted(val_logs), sorted(val)
        else:
            if not a.proposal or digest(a.proposal) != a.proposal_sha256:
                raise ValueError("proposal identity differs")
            proposal = read_json(a.proposal)
            parts = proposal["partitions"]
            if len(parts) != 2 or [p["partition"] for p in parts] != [1, 2]:
                raise ValueError("invalid proposal partitions")
            u, v = (set(p["logs"]) for p in parts)
            eligible = {scenes[n] for n in train} - val_logs
            if u & v or (u | v) != eligible or set(proposal["validation_logs"]) != val_logs:
                raise ValueError("proposal log overlap or population differs")
            for part in parts:
                expected = {n for n in train if scenes[n] in part["logs"]}
                if (len(part["logs"]) != len(set(part["logs"])) or len(part["scene_names"]) != len(set(part["scene_names"]))
                        or set(part["scene_names"]) != expected or part["scene_count"] != len(expected)
                        or part["sample_count"] != sum(sample_counts[n] for n in expected)):
                    raise ValueError("proposal scene population differs")
            part = parts[int(a.partition) - 1]
            logs, names = part["logs"], part["scene_names"]
            binding.update(proposal_sha256=a.proposal_sha256, seed=proposal["seed"])
        print(exact_json(materialize(a.index, a.index_sha256, logs, names, a.output, binding)))


if __name__ == "__main__":
    main()
