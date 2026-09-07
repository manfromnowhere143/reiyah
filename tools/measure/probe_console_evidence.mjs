#!/usr/bin/env node
/* Offline source probes, not a browser test or validation of the console.
 * Execute the captured consumer implementations with fixed HTTP responses.
 * React scheduling, DOM layout, the publisher and network are not executed.
 * A reproduced violation is a successful probe, never an application pass.
 */
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import assert from "node:assert/strict";
import { createHash, webcrypto } from "node:crypto";
import { createRequire } from "node:module";

assert.ok([4, 5].includes(process.argv.length), "usage: node probe_console_evidence.mjs --task-root PATH [--repair]");
assert.equal(process.argv[2], "--task-root");
const repair = process.argv.length === 5;
if (repair) assert.equal(process.argv[4], "--repair");
const task = path.resolve(process.argv[3]);
const capture = JSON.parse(fs.readFileSync(path.join(task, "private/source-capture.json")));
const additional = JSON.parse(fs.readFileSync(path.join(task, "private/additional-capture.json")));
const origin = capture.sources["reiyah-console"];
const root = path.join(task, repair ? "private/console-repair" : "private/reiyah-console");
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const digest = (bytes) => "sha256:" + hash(bytes);
assert.equal(hash(fs.readFileSync(additional.typescript.path)), additional.typescript.sha256);
const ts = createRequire(import.meta.url)(additional.typescript.path);
assert.equal(ts.version, additional.typescript.version);
const expected = new Map([...origin.files, ...additional.files].map((r) => [r.path, r]));
if (repair) {
  const delta = JSON.parse(fs.readFileSync(path.join(task, "private/console-repair-delta.json")));
  for (const row of delta.changes) {
    assert.equal(expected.get(row.path).sha256, row.before_sha256);
    expected.set(row.path, { ...expected.get(row.path), sha256: row.after_sha256, bytes: fs.statSync(path.join(root, row.path)).size });
  }
}
const used = new Set();
function read(rel) {
  const row = expected.get(rel);
  assert.ok(row, `uncaptured source ${rel}`);
  const bytes = fs.readFileSync(path.join(root, rel));
  assert.equal(bytes.length, row.bytes);
  assert.equal(hash(bytes), row.sha256, `capture changed ${rel}`);
  used.add(rel);
  return bytes;
}
const gateManifestPath = "/snapshot/gateb/manifest.json";
const lanePath = "evidence/measurement/result_l.txt";
const laneRaw = "/snapshot/gateb/raw/" + lanePath.replaceAll("/", "__");
const laneOriginal = read("public" + laneRaw).toString("utf8");
const laneManifest = JSON.parse(read("public" + gateManifestPath));
const manifestOriginal = JSON.parse(read("public/snapshot/manifest.json"));
const changedLane = laneOriginal.replaceAll("1.151", "9.999");
assert.notEqual(changedLane, laneOriginal);

function createRuntime(overrides = new Map()) {
  const calls = [];
  const cache = new Map();
  let assembledState = { phase: "loading" };
  let loader = null;
  const stats = [];
  const component = (name) => (props) => ({ type: name, props });
  const primitives = {
    useSurfaceState: (fn) => { loader = fn; return assembledState; },
    primeSurface: async () => {},
    Stat: (props) => { stats.push(props); return { type: "Stat", props }; },
    Station: component("Station"), Blocked: component("Blocked"),
    Digest: component("Digest"), Mark: component("Mark"), FitList: component("FitList"),
  };
  const react = {
    useEffect: () => {}, useLayoutEffect: () => {},
    useRef: (v) => ({ current: v }),
    useState: (v) => [typeof v === "function" ? v() : v, () => {}],
  };
  const jsx = (type, props) => typeof type === "function" ? type(props) : { type, props };
  const context = vm.createContext({
    TextDecoder, TextEncoder, crypto: webcrypto, __BUILD_ID__: "isolated-source-probe",
    fetch: async (url) => {
      const pathname = new URL(url, "https://offline.invalid").pathname;
      calls.push(pathname);
      if (overrides.has(pathname)) {
        const value = overrides.get(pathname);
        return value === null ? new Response(null, { status: 404 }) : new Response(value);
      }
      if (pathname.startsWith("/api/")) return new Response(null, { status: 404 });
      if (!pathname.startsWith("/snapshot/")) throw new Error(`unmocked_request:${pathname}`);
      return expected.has("public" + pathname)
        ? new Response(read("public" + pathname)) : new Response(null, { status: 404 });
    },
  });
  const allowed = new Set([
    "src/lib/evidence.ts", "src/lib/gateb.ts", "src/boot/ProofBoot.tsx",
    ...["Measurement", "SameHazard", "Monitor", "Law"].map((n) => `src/stations/${n}.tsx`),
  ]);
  function load(rel) {
    assert.ok(allowed.has(rel), `module outside probe scope: ${rel}`);
    if (cache.has(rel)) return cache.get(rel).exports;
    const code = ts.transpileModule(read(rel).toString("utf8"), {
      fileName: rel,
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX },
    }).outputText;
    const module = { exports: {} }; cache.set(rel, module);
    const req = (id) => {
      if (id === "react") return react;
      if (id === "react/jsx-runtime") return { jsx, jsxs: jsx, Fragment: "Fragment" };
      if (id.endsWith("/components/primitives")) return primitives;
      if (id.endsWith("/stations/Harbor")) return { loadHarborInstruments: async () => ({}) };
      if (id.endsWith("/lib/ground")) return { useGround: () => "light" };
      if (id.endsWith("/lib/roadScene")) return { MONO: "mock-mono", tones: {} };
      assert.ok(id.startsWith("."), `unmocked import ${id}`);
      const stem = path.posix.normalize(path.posix.join(path.posix.dirname(rel), id));
      const target = [stem + ".ts", stem + ".tsx"].find((p) => allowed.has(p));
      assert.ok(target, `unmocked module ${stem}`);
      return load(target);
    };
    const fn = new vm.Script(`(function(require,module,exports){\n${code}\n})`, { filename: rel }).runInContext(context, { timeout: 1000 });
    fn(req, module, module.exports);
    return module.exports;
  }
  return {
    load, calls, overrides,
    async init() { await load("src/lib/evidence.ts").fetchSummary(); },
    async station(name) {
      assembledState = { phase: "loading" }; loader = null; stats.length = 0;
      const fn = load(`src/stations/${name}.tsx`)[name];
      fn(); assert.ok(loader, `station ${name} did not expose its loader`);
      const data = await loader();
      assembledState = { phase: "ready", data }; stats.length = 0;
      fn();
      return { data, stats: [...stats] };
    },
    render(name, data) {
      assembledState = { phase: "ready", data }; stats.length = 0;
      load(`src/stations/${name}.tsx`)[name](); return [...stats];
    },
  };
}

const findings = [];
function retain(id, result, details) { findings.push({ id, result, ...details }); }

// Unchanged supplied bytes remain usable: establish the positive control.
{
  const rt = createRuntime(); await rt.init();
  const gate = rt.load("src/lib/gateb.ts");
  const raw = await gate.fetchLaneText(lanePath);
  assert.equal(digest(Buffer.from(raw.text)), raw.file.sha256);
  const rows = gate.parseConvergence(raw.text).rows;
  assert.equal(rows.length, 6); assert.equal(rows.at(-1).c, 1.151);
  retain("C01", "positive_control", { row_count: rows.length, terminal_c: rows.at(-1).c });
}
// A mismatch is accepted before any press-to-prove interaction.
{
  const rt = createRuntime(new Map([[laneRaw, changedLane]])); await rt.init();
  const gate = rt.load("src/lib/gateb.ts");
  if (repair) {
    await assert.rejects(() => gate.fetchLaneText(lanePath), /lane_digest_mismatch/);
    const { stats } = await rt.station("Measurement");
    const headline = stats.find((s) => s.label === "coefficient · conditional");
    assert.equal(headline.value, "∅");
    retain("F01", "repair_control_passed", { altered_bytes_rejected: true, headline: headline.value });
  } else {
    const raw = await gate.fetchLaneText(lanePath);
    assert.notEqual(digest(Buffer.from(raw.text)), raw.file.sha256);
    const { stats } = await rt.station("Measurement");
    const headline = stats.find((s) => s.label === "coefficient · conditional");
    assert.ok(JSON.stringify(headline.value).includes("9.999"));
    retain("F01", "contract_violation_reproduced", {
      supplied_digest_matches: false, parsed_terminal_c: gate.parseConvergence(raw.text).rows.at(-1).c,
      station_headline_contains_changed_c: true,
    });
  }
}
// An invalid report body can survive the actual non-UI boot verifier.
{
  const reportPath = "/snapshot/raw/report-1.2.3";
  const replacement = JSON.stringify({ status: "probe_fabricated_pass", marker: "not_a_report" });
  const rt = createRuntime(new Map([[reportPath, replacement]]));
  const verified = await rt.load("src/boot/ProofBoot.tsx").verifyEvidenceOnce();
  assert.equal(verified.report.marker, "not_a_report");
  assert.notEqual(digest(Buffer.from(replacement)), verified.reportMeta.sha256);
  retain("F02", "contract_violation_reproduced", {
    index_digest_check_passed: true, report_digest_matches: false,
    invalid_report_returned_by_boot_verifier: true,
  });
}
// Positive control: the same verifier really does reject an index mismatch.
{
  const rt = createRuntime(new Map([["/snapshot/raw/index", "{}"]]));
  await assert.rejects(() => rt.load("src/boot/ProofBoot.tsx").verifyEvidenceOnce(), /index_digest_mismatch/);
  retain("C02", "positive_control", { altered_index_rejected: true });
}
// Path-addressed records receive a digest of themselves without an expected-digest comparison.
{
  const rel = "gate/decisions/probe-only.json";
  const body = JSON.stringify({ probe: "this_record_is_not_in_the_snapshot" });
  const rt = createRuntime(new Map([["/snapshot/p/" + rel.replaceAll("/", "__"), body]]));
  await rt.init();
  const got = await rt.load("src/lib/evidence.ts").fetchSurfaceByPath(rel);
  assert.equal(got.state, "observed"); assert.equal(got.meta.sha256, digest(Buffer.from(body)));
  retain("F03", "contract_violation_reproduced", {
    uncatalogued_mock_record: true, state: got.state, self_computed_digest: true,
    scope: "client API; no assertion this fabricated record exists on the deployed server",
  });
}
// Proving a later version does not prove the earlier parsed version.
{
  const rt = createRuntime(); await rt.init();
  const gate = rt.load("src/lib/gateb.ts");
  const earlier = await gate.fetchLaneText(lanePath);
  const nextManifest = structuredClone(laneManifest);
  // Stay within the retained numerical interval so this isolates version
  // binding rather than the separate parser-range rejection.
  const nextLane = laneOriginal.replaceAll("1.151", "1.159");
  const id = lanePath.replaceAll("/", "__");
  const row = nextManifest.files.find((r) => r.id === id);
  row.sha256 = digest(Buffer.from(nextLane)); row.bytes = Buffer.byteLength(nextLane);
  rt.overrides.set(laneRaw, nextLane); rt.overrides.set(gateManifestPath, JSON.stringify(nextManifest));
  const proof = await rt.load("src/lib/evidence.ts").prove("gateb/" + id);
  const again = await gate.fetchLaneText(lanePath);
  assert.equal(proof.equal, true); assert.notEqual(proof.clientSha256, earlier.file.sha256);
  assert.equal(again.text, earlier.text);
  retain("F04", "contract_violation_reproduced", {
    earlier_parsed_c: gate.parseConvergence(again.text).rows.at(-1).c,
    later_byte_c: gate.parseConvergence(nextLane).rows.at(-1).c,
    later_proof_equal: proof.equal, later_proof_matches_earlier_digest: false,
    scope: "consumer and proof functions; React receipt timing not exercised",
  });
}
// Register selection is exercised through each actual station loader.
for (const name of ["Measurement", "SameHazard", "Monitor", "Law"]) {
  const rt = createRuntime(); await rt.init();
  const latest = await rt.load("src/lib/gateb.ts").registerPath();
  const { data } = await rt.station(name);
  const reg = (data.data ?? data.d).reg;
  const affected = ["Measurement", "SameHazard"].includes(name);
  const old = affected && !repair;
  assert.equal(reg.file.path, old ? "evidence/claim-status-register-2026-08-29.json" : latest);
  retain(affected ? `F05-${name}` : `C03-${name}`, old ? "contract_violation_reproduced" : affected ? "repair_control_passed" : "positive_control", {
    latest_available_path: latest, selected_path: reg.file.path,
    selected_version: reg.version, selected_claims: reg.claims.length,
  });
}
// Missing AA is not a measured zero improvement.
{
  const rt = createRuntime(new Map([["/snapshot/gateb/raw/evidence__measurement__result_aa.txt", null]]));
  await rt.init(); const { data, stats } = await rt.station("Monitor");
  assert.equal(data.d.aa, null);
  const sub = stats.find((s) => s.label === "two sensors · scene monitor").sub;
  assert.ok(sub.includes(repair ? "AUC ∅, context adds ∅" : "AUC ∅, context adds 0.000"));
  retain("F06", repair ? "repair_control_passed" : "contract_violation_reproduced", { missing_aa: true, generated_stat_subtitle: sub });
}
// Pattern matching alone neither constrains numbers nor enforces table completeness.
{
  const rt = createRuntime(); const gate = rt.load("src/lib/gateb.ts");
  const removed = laneOriginal.split("\n").filter((line) => !/^\s*L5 \+ motion state\s{2,}/.test(line)).join("\n");
  if (repair) {
    assert.throws(() => gate.parseConvergence(laneOriginal.replaceAll("1.151", "1..151")), /convergence_table_invalid/);
    assert.throws(() => gate.parseConvergence(removed), /convergence_table_invalid/);
    assert.throws(() => gate.parseH4(""), /h4_counts_unavailable/);
    retain("F07", "repair_control_passed", { malformed_number_rejected: true, missing_terminal_row_rejected: true, empty_h4_rejected: true });
  } else {
    const malformed = gate.parseConvergence(laneOriginal.replaceAll("1.151", "1..151"));
    assert.ok(Number.isNaN(malformed.rows.at(-1).c));
    const shortened = gate.parseConvergence(removed);
    assert.equal(shortened.rows.length, 5); assert.equal(shortened.rows.at(-1).level, "L4");
    const noTrials = gate.parseH4("");
    assert.equal(noTrials.trials, 0); assert.equal(noTrials.participants, 0);
    retain("F07", "contract_violation_reproduced", {
      malformed_number_became_nan: true, missing_terminal_row_returned_rows: shortened.rows.length,
      substituted_terminal_level: shortened.rows.at(-1).level,
      empty_h4_trial_count: noTrials.trials, empty_h4_participant_count: noTrials.participants,
    });
  }
}

if (repair) {
  const rt = createRuntime(); await rt.init();
  const { data } = await rt.station("Monitor");
  const originalAa = structuredClone(data.d.aa);
  for (const r of data.d.aa.rows) r.a = 0.75;
  let sub = rt.render("Monitor", data).find((s) => s.label === "two sensors · scene monitor").sub;
  assert.ok(sub.includes("AUC 0.750, context adds 0.000"));
  data.d.aa = originalAa;
  data.d.aa.rows = data.d.aa.rows.filter((r) => r.name !== "own + context");
  sub = rt.render("Monitor", data).find((s) => s.label === "two sensors · scene monitor").sub;
  assert.ok(sub.includes("context adds ∅"));
  const gate = rt.load("src/lib/gateb.ts");
  const h4 = gate.parseH4(read("public/snapshot/gateb/raw/human-channel__evidence__h4_dcpt_takeover.txt").toString("utf8"));
  assert.ok(h4.trials > 0 && h4.participants > 0);
  retain("C04", "positive_control", { supplied_equal_auc_difference: 0, missing_comparator_remains_unknown: true, retained_h4_trials: h4.trials, retained_h4_participants: h4.participants });
  for (const mutation of ["missing_digest", "invalid_digest", "wrong_byte_count", "negative_byte_count"]) {
    const manifest = structuredClone(laneManifest);
    const row = manifest.files.find((r) => r.path === lanePath);
    if (mutation === "missing_digest") delete row.sha256;
    if (mutation === "invalid_digest") row.sha256 = "unknown";
    if (mutation === "wrong_byte_count") row.bytes += 1;
    if (mutation === "negative_byte_count") row.bytes = -1;
    const runtime = createRuntime(new Map([[gateManifestPath, JSON.stringify(manifest)]]));
    await runtime.init();
    await assert.rejects(() => runtime.load("src/lib/gateb.ts").fetchLaneText(lanePath), /lane_binding_invalid|lane_digest_mismatch/);
  }
  retain("C05", "positive_control", { invalid_binding_controls_rejected: 4 });
}

// Bind all executed/cited bytes once more; the producer did not modify its sources.
const sources = [...used].sort().map((rel) => { read(rel); return expected.get(rel); });
const report = {
  artifact_id: "reiyah.console-evidence-source-probes.0.1.0", version: "0.1.0",
  status: "completed", mode: "offline_source_probe", console_validation_status: "not_established",
  variant: repair ? "private_four_file_repair" : "captured_source",
  source_head: origin.state_before.head,
  source_worktree_clean_at_capture: origin.state_before.status === "",
  source_snapshot_identity: laneManifest.identity,
  gate_a_snapshot_identity: manifestOriginal.identity,
  controls: findings, bound_sources: sources,
  toolchain: { node: process.version, typescript: ts.version, typescript_sha256: additional.typescript.sha256 },
  limits: ["Mocked HTTP responses; no live network or deployment read", "React effects and DOM are not executed", "No independent human usability study", "Owner worktree unchanged; repair variant exists only in private review custody", "F02, F03 and F04 are outside the four-file repair and remain reproduced", "Digest equality would not establish scientific truth or operator acceptance"],
};
process.stdout.write(JSON.stringify(report, null, 2) + "\n");
