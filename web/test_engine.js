// Compares the browser engine with the Python implementation. Exit code 1 on any mismatch, NaN or missing value.
// Regenerate fixtures first: python scripts/gerar_fixtures_web.py
const path = require("path");
const E = require("./engine.js");
const data = require(path.join(__dirname, "fixtures", "caso.json"));
const exp = require(path.join(__dirname, "fixtures", "expected.json"));
const map = {alt_frac_cont: "cont", alt_frac_avg: "avg", breaker_frac: "bk", i_pre: "iPre", i_shed: "iShed", i_app: "iApp",
  endurance_casa_min: "eCasa", endurance_peukert_min: "eP", margin_min: "margin", casa_profile_feasible: "feasible"};
let bad = 0, n = 0;
const same = (a, b) => (typeof a === "boolean" || typeof b === "boolean") ? a === b
  : (Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a)));
for (const r of exp) {
  if ("garmin" in r) { n++; const g = E.garmin(data[r.m]).net; if (!same(g, r.garmin)) { bad++; console.log("garmin", r.m, r.garmin, g); } continue; }
  const j = E.analyze(data[r.m], !!r.inst, r.p);
  for (const [a, b] of Object.entries(map)) {
    n++;
    if (!(a in r) || !(b in j) || !same(r[a], j[b])) { bad++; console.log("MISMATCH", r.m, r.inst, JSON.stringify(r.p), a, r[a], j[b]); }
  }
}
console.log(`checks ${n}, mismatches ${bad}`);
process.exit(bad === 0 && n > 0 ? 0 : 1);
