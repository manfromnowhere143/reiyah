"""Bind original sensor assets to private offline review packets; report readiness.

Camera images are unmodified files with a separate SVG marker overlay. Lidar
plots are explicitly local views; full raw sweeps remain accessible. No learned
model, annotation overlay, fabricated review, or public payload is produced.
"""
import argparse
import collections
import html
import json
import os
import pathlib

import numpy as np

from reference_study import (VERSION, STRATA, bound_protocol, digest, read_json,
                             rotation_wxyz, safe_asset, write_new)
from reference_study_analysis import consensus_bounds, two_stage_bounds, stratified_srs_bounds


def asset_state(path, channel):
    if not path.is_file():
        return {'state': 'missing', 'asset_sha256': None, 'asset_bytes': None}
    before = digest(path)
    result = {'state': 'available', 'asset_sha256': before, 'asset_bytes': path.stat().st_size}
    try:
        if channel.startswith('CAM'):
            from PIL import Image
            with Image.open(path) as im:
                result['decoded_image_size'] = list(im.size)
                im.verify()
        else:
            data = np.fromfile(path, dtype='<f4')
            if data.size == 0 or data.size % 5 or not np.isfinite(data).all():
                raise ValueError('Invalid lidar record layout, empty payload, or nonfinite values')
            result['points'] = data.size // 5
    except (ValueError, OSError) as exc:
        result.update(state='sensor_invalid', invalid_reason=str(exc))
    if digest(path) != before:
        raise ValueError('Asset changed during inspection')
    return result


def lidar_svg(path, item, candidate):
    """All points in a +/-10m global XY neighborhood; unfiltered height data."""
    points = np.fromfile(path, dtype='<f4').reshape(-1, 5)[:, :3].astype(float)
    calibration, ego = item['calibration'], item['ego_pose']
    world = ((points @ rotation_wxyz(calibration['rotation']).T + calibration['translation'])
             @ rotation_wxyz(ego['rotation']).T + ego['translation'])
    delta = world - np.asarray(candidate)
    keep = (np.abs(delta[:, 0]) <= 10) & (np.abs(delta[:, 1]) <= 10)
    view = delta[keep]
    circles = []
    for x, y, z in view:
        color = '#525d6a' if abs(z) > 2 else '#95a9b5' if z < -1 else '#e2dfb5'
        circles.append(f'<circle cx="{200+20*x:.2f}" cy="{200-20*y:.2f}" r="0.8" fill="{color}"/>')
    return ('<svg viewBox="0 0 400 400" xmlns="http://www.w3.org/2000/svg">'
            '<rect width="400" height="400" fill="#101923"/>' + ''.join(circles) +
            '<circle cx="200" cy="200" r="40" fill="none" stroke="#00ffff" stroke-width="1"/>'
            '<path d="M190 200h20 M200 190v20" stroke="#00ffff"/>'
            '<text x="10" y="390" fill="white" font-size="10">Global XY; 20 m across; cyan radius 2 m</text></svg>')


def case_html(packet, raw_root, target_dir):
    chunks = ['<!doctype html><meta charset="utf-8"><title>Reference evidence packet</title>',
              '<style>body{background:#111820;color:#eee;font:16px system-ui;margin:24px;max-width:1450px}'
              '.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}'
              'figure{margin:0;background:#1a2631;padding:10px}svg{width:100%;height:auto}'
              'a{color:#79d8ff}small{color:#b5c2ce;overflow-wrap:anywhere}h2{margin-top:35px}</style>',
              '<h1>Case ' + packet['case_id'] + '</h1>',
              '<p>Assess whether sensor evidence supports an object with its center within 2 m XY of '
              'the candidate at the reference time. The cyan marker is a <b>fixed world location</b>, '
              'not an object trajectory. A marker can be misplaced by motion between sensor times. '
              'Do not infer physical absence from missing images, occlusion, no lidar return or no annotation.</p>',
              '<p>Keep unresolved when visibility, timing, or center localization is insufficient. '
              'Candidate motion, calibration error and per-point lidar acquisition time are unknown. '
              'The reference time is ' + str(packet['candidate_sample_timestamp_us']) + ' microseconds.</p>']
    for offset in (-1, 0, 1):
        chunks.append('<h2>' + {-1: 'Preceding keyframe', 0: 'Current keyframe', 1: 'Following keyframe'}[offset] + '</h2><div class="grid">')
        for item in packet['evidence']:
            if item['frame_offset'] != offset:
                continue
            chunks.append('<figure><b>' + item['channel'] + '</b><br>')
            if item['state'] != 'available':
                chunks.append(html.escape(item['state']) + '</figure>')
                continue
            path = safe_asset(raw_root, item['relative_asset_path'])
            rel = html.escape(os.path.relpath(path, target_dir), quote=True)
            if item['channel'].startswith('CAM'):
                w, h = item['image_width'], item['image_height']
                chunks.append(f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
                              f'<image href="{rel}" width="{w}" height="{h}"/>')
                projection = item['projection']
                if projection['state'] == 'inside_image':
                    x, y = projection['pixel_xy']
                    chunks.append(f'<circle cx="{x}" cy="{y}" r="18" fill="none" stroke="#00ffff" stroke-width="3"/>'
                                  f'<path d="M{x-26} {y}h52 M{x} {y-26}v52" stroke="#00ffff" stroke-width="2"/>')
                chunks.append('</svg><small>Center projection: ' + projection['state'] + '.</small><br>')
            else:
                chunks.append(lidar_svg(path, item, packet['candidate_global_center_m']))
            chunks.append(f'<small>Sensor Δt = {item["sample_time_offset_s"]:+.6f} s. '
                          f'V=30 m/s displacement scenario: {item["conditional_motion_displacement_m"][-1]:.3f} m. '
                          'This is not an error bound.</small><br>')
            chunks.append(f'<a href="{rel}">Original sensor asset</a><br><small>Evidence ID: '
                          + item['evidence_id'] + '<br>SHA256: ' + item['asset_sha256'] + '</small></figure>')
        chunks.append('</div>')
    chunks.append('<p>Offline research packet. No detector score, class, name, stratum or reference label is supplied. '
                  'Timestamps and dataset appearance may identify public scenes; blinding requires reviewers not to look them up. '
                  'A pair of agreeing judgments remains a fallible measurement.</p>')
    return '\n'.join(chunks)


def analyze(selection, packets, reviews, schema, confidence):
    packet_by_id = {p['case_id']: p for p in packets}
    expected = {c['case_id'] for c in selection['cases']}
    if len(packet_by_id) != len(packets) or set(packet_by_id) != expected:
        raise ValueError('Packet case population differs from frozen selection')
    by_case = collections.defaultdict(list)
    for review in reviews:
        if review['case_id'] not in expected:
            raise ValueError('Review outside selected population')
        by_case[review['case_id']].append(review)
    bounds = {ident: consensus_bounds(by_case[ident], packet, schema)
              for ident, packet in packet_by_id.items()}
    summaries = {}
    for group in STRATA:
        if selection.get('sampling_design') == 'within_stratum_srs':
            ids = [c['case_id'] for c in selection['cases'] if c['stratum'] == group]
            population_n = sum(r['population_n'] for r in selection['population_cells'] if r['stratum'] == group)
            expected_pi = len(ids) / population_n if population_n else None
            if any(c['inclusion_probability'] != expected_pi for c in selection['cases'] if c['stratum'] == group):
                raise ValueError('Selection inclusion probability differs from declared SRS design')
            summaries[group] = stratified_srs_bounds(population_n, ids, bounds, confidence)
            continue
        cells = []
        for row in selection['population_cells']:
            if row['stratum'] != group:
                continue
            ids = [c['case_id'] for c in selection['cases']
                   if c['scene_token'] == row['scene_token'] and c['stratum'] == group]
            if len(ids) != row['sample_n']:
                raise ValueError('Sample count does not match selection')
            cells.append({'population_n': row['population_n'], 'selected': row['scene_selected'],
                          'case_ids': ids})
        summaries[group] = two_stage_bounds(cells, bounds, confidence)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol-dir', type=pathlib.Path, required=True)
    parser.add_argument('--selection', type=pathlib.Path, required=True)
    parser.add_argument('--prepared-packets', type=pathlib.Path, required=True)
    parser.add_argument('--raw-root', type=pathlib.Path, required=True)
    parser.add_argument('--output-dir', type=pathlib.Path, required=True)
    parser.add_argument('--reviews', type=pathlib.Path, help='JSON array; omit before independent review')
    args = parser.parse_args()
    if args.output_dir.exists():
        raise ValueError('Output identity already exists; use a new directory')
    protocol, freeze = bound_protocol(args.protocol_dir)
    selection = read_json(args.selection)
    packets = read_json(args.prepared_packets)
    if selection['protocol_sha256'] != freeze['protocol_sha256'] or any(
            p['protocol_sha256'] != freeze['protocol_sha256'] for p in packets):
        raise ValueError('Mismatched packet or selection protocol')
    hashes = {str(p): digest(p) for p in (args.selection, args.prepared_packets,
                                         args.protocol_dir / 'review.schema.json')}
    if args.reviews:
        hashes[str(args.reviews)] = digest(args.reviews)
    states, unique_assets, current_offsets = collections.Counter(), {}, []
    current_outside, current_visible = 0, 0
    for packet in packets:
        inside = 0
        for item in packet['evidence']:
            if 'relative_asset_path' in item:
                path = safe_asset(args.raw_root, item['relative_asset_path'])
                if str(path) not in unique_assets:
                    unique_assets[str(path)] = asset_state(path, item['channel'])
                item.update(unique_assets[str(path)])
                if item['state'] == 'available' and item['channel'].startswith('CAM'):
                    if item['decoded_image_size'] != [item['image_width'], item['image_height']]:
                        item.update(state='sensor_invalid', invalid_reason='Image dimensions disagree with metadata')
                if item['frame_offset'] == 0 and item['channel'].startswith('CAM'):
                    current_offsets.append(abs(item['sample_time_offset_s']))
                    inside += item['state'] == 'available' and item['projection']['state'] == 'inside_image'
            states[item['state']] += 1
        current_visible += inside > 0
        current_outside += inside == 0
    reviews = read_json(args.reviews) if args.reviews else []
    schema = read_json(args.protocol_dir / 'review.schema.json')
    estimates = analyze(selection, packets, reviews, schema, protocol['confidence_level'])
    args.output_dir.mkdir(parents=True, mode=0o700)
    write_new(args.output_dir / 'packets.private.json', packets)
    for packet in packets:
        (args.output_dir / (packet['case_id'] + '.html')).write_text(
            case_html(packet, args.raw_root, args.output_dir))
    links = '\n'.join('<li><a href="' + p['case_id'] + '.html">Case ' + p['case_id'] + '</a></li>' for p in packets)
    (args.output_dir / 'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Reference study</title>'
        '<h1>Reference study: blinded evidence packets</h1><p>Read the frozen reviewer protocol first. '
        'Case order uses opaque identifiers. Raw inputs are private and must remain here.</p><ul>' + links + '</ul>')
    changed = [p for p, sha in hashes.items() if digest(pathlib.Path(p)) != sha]
    for p, item in unique_assets.items():
        if item['asset_sha256'] is not None and digest(pathlib.Path(p)) != item['asset_sha256']:
            changed.append(p)
    if changed:
        raise ValueError('Inputs changed while rendering; emitted packet directory is invalid')
    current = np.asarray(current_offsets)
    result = {'artifact_id': 'reiyah.reference-study.readiness.0.1.0', 'version': VERSION,
              'lifecycle_status': 'exploratory', 'protocol_sha256': freeze['protocol_sha256'],
              'selection_sha256': digest(args.selection),
              'prepared_packets_sha256': digest(args.prepared_packets),
              'bound_packets_sha256': digest(args.output_dir / 'packets.private.json'),
              'review_schema_sha256': digest(args.protocol_dir / 'review.schema.json'),
              'reviews_sha256': digest(args.reviews) if args.reviews else None,
              'reviews_received': len(reviews), 'independent_reviewer_identity_verification': 'not_established',
              'cases': len(packets), 'unique_assets': len(unique_assets),
              'unique_available_assets': sum(x['state'] == 'available' for x in unique_assets.values()),
              'unique_available_bytes': sum(x['asset_bytes'] for x in unique_assets.values() if x['state'] == 'available'),
              'evidence_slot_states': dict(states), 'cases_with_available_current_camera_center_in_image': current_visible,
              'cases_without_available_current_camera_center_in_image': current_outside,
              'projection_nonclaim': 'Geometric inclusion of a fixed point is not object visibility or existence',
              'current_camera_sample_abs_offset_seconds': {
                  'n_case_camera_slots': len(current),
                  'median': float(np.median(current)) if len(current) else None,
                  'p95': float(np.quantile(current, .95)) if len(current) else None,
                  'max': float(current.max()) if len(current) else None,
                  'conditional_displacement_exceeds_2m_at_30mps_slots': int(sum(current * 30 > 2))},
              'estimates': estimates, 'physical_performance_point_estimate': None,
              'status': 'evidence_prepared_awaiting_independent_review' if not reviews else 'review_protocol_analysis',
              'nonclaims': ['No physical false-positive rate', 'No missing-annotation correction inferred from image absence',
                            'No causal evidence-source ablation', 'No Gate A acceptance or deployment authority']}
    write_new(args.output_dir / 'readiness-aggregate.json', result)
    print(json.dumps({'cases': len(packets), 'unique_available_assets': result['unique_available_assets'],
                      'reviews_received': len(reviews), 'states': dict(states)}))


if __name__ == '__main__':
    main()
