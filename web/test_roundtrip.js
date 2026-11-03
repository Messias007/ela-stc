// Round trip: browser project -> exported JSON -> browser import, results must be identical; also writes the
// exported files so that tests/test_web_roundtrip.py can check the Python results against the browser results.
const fs = require("fs"), path = require("path");
const E = require("./engine.js");
Object.assign(global, {analyze: E.analyze, garmin: E.garmin, BASE: E.BASE, PARAMS: E.PARAMS});
global.DEFAULT_CASE = require(path.join(__dirname, "fixtures", "caso_loader.json"));
const A = require("./app.js");
let bad = 0;
const res = () => A.getProject().models.map(m => { const e = A.engineModel(m), p = Object.assign({}, A.getProject().params);
  const a = E.analyze(e, true, p), b = E.analyze(e, false, p);
  return {cont: a.cont, avg: a.avg, bk: a.bk, margin: a.margin, before: b.margin, net: E.garmin(e).net}; });
function scenario(name, mutate) {
  A.setProject(null); A.setProject(A.defaultProject()); mutate(A.getProject());
  const r1 = res(), exp = A.toLoader();
  const plain = JSON.parse(JSON.stringify(exp)); delete plain.ela_web;     // simulate a file written by another tool
  A.setProject(A.fromLoader(plain)); const r2 = res();
  if (JSON.stringify(r1.map(x => Object.values(x).map(v => +v.toFixed(9)))) !== JSON.stringify(r2.map(x => Object.values(x).map(v => +v.toFixed(9))))) {
    bad++; console.log("ROUND TRIP MISMATCH", name, r1, r2); }
  fs.writeFileSync(path.join(__dirname, "fixtures", `rt_${name}.json`), JSON.stringify(plain));
  fs.writeFileSync(path.join(__dirname, "fixtures", `rt_${name}_js.json`), JSON.stringify(r1));
}
scenario("base", P => {});
scenario("params", P => { P.params.tx_duty = 0.2; P.params.preshed_min = 10; P.params.use_typical = 0; P.params.soc = 0.85; });
scenario("two_gtn750", P => { P.added.shift(); P.added.push(A.newEquip("gtn750")); A.getProject().added.push(A.newEquip("gtn750")); });
scenario("custom", P => { P.added.push({id: "c1", cat: "custom", label: "Custom constant load", unit: 1, essential: false,
  rows: [{n: "", role: "none", cls: "continuous", src: "test", byV: {"14": {m: 2.5, t: 2.0, bk: 5}, "28": {m: 1.2, t: 1.0, bk: 5}},
          duty: {taxi: 1, cruise: 0.5, landing: 1}}]}); });
console.log(bad ? `round trip mismatches: ${bad}` : "round trip OK (4 scenarios)");
process.exit(bad ? 1 : 0);
