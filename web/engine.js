// ELA-STC method v2, port of ela_stc/analysis.py (checked against Python by test_engine.js)
const PHASES = ["ground", "taxi", "takeoff_climb", "cruise", "landing", "emergency"];
const NORMAL = ["ground", "taxi", "takeoff_climb", "cruise", "landing"];
const BASE = {use_typical: 1, tx_duty: 0.10, landing_light_duty: 1.0, soh: null, soc: null, temp_factor: null, peukert_n: null,
  casa_fraction: 0.72, preshed_min: 5, approach_min: 5, approach_flap_duty: 0.10, cp_scaling: 1, pitot_em: 1,
  bat_capacity_factor: 1.0};

function k(l, ph) { return l.duty[ph] || 0; }

function adjusted(m, installed, p) {
  const typ = p.use_typical >= 0.5;
  const txDuty = {};
  const out = m.items.filter(it => installed ? it.st !== "removed" : it.st !== "added").map(it => {
    const useTyp = typ && it.ityp != null;
    const duty = Object.assign({}, it.duty);
    if (it.tx) { for (const ph in duty) duty[ph] = duty[ph] > 0 ? p.tx_duty : 0; if (it.radio) txDuty[it.radio] = duty; }
    if (it.ll) for (const ph of ["takeoff_climb", "landing"]) if ((duty[ph] || 0) > 0) duty[ph] = p.landing_light_duty;
    if (it.pitot) duty.emergency = Number(p.pitot_em);
    return Object.assign({}, it, {I: useTyp ? it.ityp : it.imax, duty, useTyp});
  });
  // receive and transmit of one radio are mutually exclusive
  return out.map(l => {
    if (!l.radio || l.tx || !txDuty[l.radio]) return l;
    const tx = txDuty[l.radio], duty = {};
    for (const ph in l.duty) duty[ph] = Math.max(0, l.duty[ph] - (tx[ph] || 0));
    return Object.assign({}, l, {duty});
  });
}

function breakerCheck(m, installed, p) {
  const L = adjusted(m, installed, Object.assign({}, p, {use_typical: 0}));
  const circ = {};
  for (const l of L) (circ[l.circuit || l.n] = circ[l.circuit || l.n] || []).push(l);
  const rd = {};
  for (const l of L) if (l.radio) { rd[l.radio] = rd[l.radio] || {}; for (const [ph, v] of Object.entries(l.duty)) rd[l.radio][ph] = (rd[l.radio][ph] || 0) + v; }
  const full = l => Math.max(0, ...Object.values(l.duty)) >= 1 || (!!l.radio && Math.max(0, ...Object.values(rd[l.radio])) >= 1 - 1e-9);
  let worst = 0, worstId = null, n = 0; const missing = [];
  for (const [cid, ls] of Object.entries(circ)) {
    if (!ls.some(l => l.st === "added")) continue;
    const cont = ls.filter(l => l.cls === "continuous" && full(l));
    if (!cont.length) continue;
    const ratings = [...new Set(ls.map(l => l.bk).filter(Boolean))];
    if (!ratings.length) { missing.push(cid); continue; }
    const f = cont.reduce((s, l) => s + l.I, 0) / ratings[0];
    n++; if (f > worst) { worst = f; worstId = cid; }
  }
  return {frac: worst, circuit: worstId, n, missing};
}

function battI(l, m, p) {
  if (!p.cp_scaling) return l.I;
  if (l.ibat != null && !l.useTyp) return l.ibat;
  if (l.cp) return l.I * m.V / m.Vb;
  return l.I;
}

function peukert(b, I) {
  if (I <= 0) return Infinity;
  return 60 * b.H * Math.pow(b.C * b.soh * b.soc * b.kt / (I * b.H), b.n);
}

function casa(b, iPre, tPre, iShed, iApp, tApp, frac) {
  const avail = b.C * 60 * frac;
  const ratePre = iPre * (iPre > 2 * b.C ? 1.2 : 1);
  const pre = ratePre * tPre;
  if (pre >= avail) return ratePre > 0 ? avail / ratePre : Infinity;
  const rem = avail - pre - iApp * tApp;
  if (rem < 0) return tPre + (iApp > 0 ? (avail - pre) / iApp : Infinity);
  return tPre + (iShed > 0 ? rem / iShed : Infinity) + tApp;
}

function casaFeasible(b, iPre, tPre, iApp, tApp, frac) {
  const ratePre = iPre * (iPre > 2 * b.C ? 1.2 : 1);
  return b.C * 60 * frac - ratePre * tPre - iApp * tApp >= 0;
}

function peukertProfile(b, iPre, tPre, iShed, iApp, tApp) {
  const tp = peukert(b, iPre), fPre = tPre / tp;
  if (fPre >= 1) return tp;
  const ta = peukert(b, iApp), fApp = tApp / ta;
  if (fPre + fApp > 1) return tPre + (1 - fPre) * ta;
  return tPre + (1 - fPre - fApp) * peukert(b, iShed) + tApp;
}

function analyze(m, installed, params) {
  const p = Object.assign({}, BASE, params || {});
  const L = adjusted(m, installed, p);
  const avg = {}, cont = {};
  for (const ph of PHASES) {
    avg[ph] = L.reduce((s, l) => s + k(l, ph) * l.I, 0);
    cont[ph] = L.reduce((s, l) => s + (l.cls === "continuous" ? k(l, ph) * l.I : 0), 0);
  }
  const phAvg = NORMAL.reduce((a, b) => avg[b] > avg[a] ? b : a, NORMAL[0]);
  const phCont = NORMAL.reduce((a, b) => cont[b] > cont[a] ? b : a, NORMAL[0]);
  const B = breakerCheck(m, installed, p);
  const iPre = L.reduce((s, l) => s + k(l, "cruise") * battI(l, m, p), 0);
  const iShed = L.reduce((s, l) => s + k(l, "emergency") * battI(l, m, p), 0);
  let iApp = iShed;
  for (const l of L) {
    if (l.ll && k(l, "landing") > 0) iApp += battI(l, m, p);
    if (l.flap) iApp += (p.approach_flap_duty - k(l, "emergency")) * battI(l, m, p);
  }
  const b = {C: m.bat.C * (m.bat.scen ? p.bat_capacity_factor : 1), H: m.bat.H,
    soh: p.soh != null ? p.soh : m.bat.soh, soc: p.soc != null ? p.soc : (m.bat.soc ?? 1), kt: p.temp_factor != null ? p.temp_factor : m.bat.kt,
    n: p.peukert_n != null ? p.peukert_n : m.bat.n};
  const tPre = p.preshed_min, tApp = p.approach_min;
  const eCasa = casa(b, iPre, tPre, iShed, iApp, tApp, p.casa_fraction);
  const feasible = casaFeasible(b, iPre, tPre, iApp, tApp, p.casa_fraction);
  const eP = peukertProfile(b, iPre, tPre, iShed, iApp, tApp);
  return {
    cont: cont[phCont] / m.alt, contA: cont[phCont], contPh: phCont,
    avg: avg[phAvg] / m.alt, avgA: avg[phAvg], avgPh: phAvg, avgBy: avg, contBy: cont,
    bk: B.frac, bkName: B.circuit, bkN: B.n, bkMissing: B.missing, feasible, iPre, iShed, iApp, eCasa, eP, margin: Math.min(eCasa, eP) - m.req, C1: b.C, loads: L
  };
}

function garmin(m) {
  const added = m.items.filter(it => it.st === "added" && !it.tx);
  const removed = m.items.filter(it => it.st === "removed" && !it.tx);
  const a = added.reduce((s, it) => s + (it.ityp != null ? it.ityp : it.imax), 0);
  const r = removed.reduce((s, it) => s + it.imax, 0);
  return {added: a, removed: r, net: a - r, addedItems: added, removedItems: removed};
}

const PARAMS = [
  {key: "use_typical", label: "Installed current (typical/max)", low: 0, base: 1, high: 1, group: "method"},
  {key: "casa_fraction", label: "CASA fraction (72/75 %)", low: 0.72, base: 0.72, high: 0.75, group: "method"},
  {key: "preshed_min", label: "Pre-shed time (5/10 min)", low: 10, base: 5, high: 5, group: "method"},
  {key: "pitot_em", label: "Pitot heat in emergency", low: 1, base: 1, high: 0, group: "method"},
  {key: "cp_scaling", label: "Currents at battery voltage", low: 1, base: 1, high: 0, group: "method"},
  {key: "bat_capacity_factor", label: "14 V battery (22/24/25 Ah)", low: 1, base: 1, high: 25 / 22, group: "method"},
  {key: "tx_duty", label: "Transmit duty", low: 0.05, base: 0.10, high: 0.20, group: "physical"},
  {key: "landing_light_duty", label: "Landing-light duty", low: 0.3, base: 1.0, high: 1.0, group: "physical"},
  {key: "soh", label: "Battery state of health", low: 0.8, base: 0.8, high: 1.0, group: "physical"},
  {key: "soc", label: "State of charge", low: 0.8, base: 0.9, high: 1.0, group: "physical"},
  {key: "temp_factor", label: "Temperature factor", low: 0.7, base: 1.0, high: 1.0, group: "physical"},
  {key: "peukert_n", label: "Peukert exponent", low: 1.3, base: 1.2, high: 1.1, group: "physical"},
];

if (typeof module !== "undefined") module.exports = {analyze, garmin, PARAMS, BASE, PHASES};
