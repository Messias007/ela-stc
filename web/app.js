// ELA-STC web: project editor. Project = loader-compatible JSON (aml + installation) plus "ela_web" UI state.
const PT = {ground: "Solo", taxi: "Táxi", takeoff_climb: "Decolagem", cruise: "Cruzeiro", landing: "Pouso", emergency: "Emergência"};
const PHS = ["ground", "taxi", "takeoff_climb", "cruise", "landing", "emergency"];
const ROLES = {none: "—", tx: "Transmissão", landing: "Farol de pouso", flap: "Motor do flap", pitot: "Pitot aquecido"};
const ON = {taxi: 1, takeoff_climb: 1, cruise: 1, landing: 1};
const G = "Garmin 190-01007-A3 Rev 4, Table 1-5; disjuntores Fig. E-4";

// Equipment catalog: currents by bus voltage {t: typical, m: maximum, bk: breaker}. Sources in each row.
const CATALOG = [
  {id: "gtn650", label: "Garmin GTN 650 (GPS/NAV/COM)", rows: [
    {n: "main + NAV", byV: {14: {t: 2.20, m: 3.96, bk: 7.5}, 28: {t: 1.10, m: 2.08, bk: 5}}, src: G + " (1.6+0.60 / 2.8+1.16 A; 0.8+0.30 / 1.5+0.58 A)"},
    {n: "COM RX", com: true, byV: {14: {t: 0.45, m: 0.45, bk: 10}, 28: {t: 0.21, m: 0.21, bk: 5}}, src: G},
    {n: "COM TX", com: true, role: "tx", byV: {14: {t: 4.02, m: 4.02}, 28: {t: 1.76, m: 1.76}}, src: G + " (10 W)"}]},
  {id: "gtn750", label: "Garmin GTN 750 (GPS/NAV/COM)", rows: [
    {n: "main + NAV", byV: {14: {t: 3.00, m: 4.56, bk: 7.5}, 28: {t: 1.50, m: 2.38, bk: 5}}, src: G + " (2.4+0.60 / 3.4+1.16 A; 1.2+0.30 / 1.8+0.58 A)"},
    {n: "COM RX", com: true, byV: {14: {t: 0.45, m: 0.45, bk: 10}, 28: {t: 0.21, m: 0.21, bk: 5}}, src: G},
    {n: "COM TX", com: true, role: "tx", byV: {14: {t: 4.02, m: 4.02}, 28: {t: 1.76, m: 1.76}}, src: G + " (10 W)"}]},
  {id: "gtn635", label: "Garmin GTN 635 (GPS/COM)", rows: [
    {n: "main", byV: {14: {t: 1.6, m: 2.8, bk: 7.5}, 28: {t: 0.8, m: 1.5, bk: 5}}, src: G},
    {n: "COM RX", com: true, byV: {14: {t: 0.45, m: 0.45, bk: 10}, 28: {t: 0.21, m: 0.21, bk: 5}}, src: G},
    {n: "COM TX", com: true, role: "tx", byV: {14: {t: 4.02, m: 4.02}, 28: {t: 1.76, m: 1.76}}, src: G + " (10 W)"}]},
  {id: "gtn625", label: "Garmin GTN 625 (GPS)", rows: [{n: "main", byV: {14: {t: 1.6, m: 2.8, bk: 7.5}, 28: {t: 0.8, m: 1.5, bk: 5}}, src: G}]},
  {id: "gtn725", label: "Garmin GTN 725 (GPS)", rows: [{n: "main", byV: {14: {t: 2.4, m: 3.4, bk: 7.5}, 28: {t: 1.2, m: 1.8, bk: 5}}, src: G}]},
  {id: "gma35", label: "Garmin GMA 35 (áudio remoto)", rows: [{n: "", byV: {14: {t: 0.80, m: 1.50}, 28: {t: 0.40, m: 1.0}}, src: "Garmin 190-01007-A3 Rev 4, Table 1-5 (disjuntor na Fig. F-2, não lido)"}]},
  {id: "gma345", label: "Garmin GMA 345 (painel de áudio)", rows: [{n: "", byV: {14: {t: 0.83, m: 1.19, bk: 5}, 28: {t: 0.43, m: 0.90, bk: 5}}, src: "Garmin 190-01878-02 Rev 6, Table 1-7 (máx. sem USB); disjuntor 5 A"}]},
  {id: "gtx345", label: "Garmin GTX 345 (transponder ADS-B)", rows: [{n: "", byV: {14: {t: 0.72, m: 1.30, bk: 3}, 28: {t: 0.36, m: 0.65, bk: 3}}, src: "Garmin 190-01499-02 Rev 9, Table 1-12; disjuntor 3 A, Fig. D-1"}]},
  {id: "g5", label: "Garmin G5 (atitude)", rows: [{n: "", byV: {14: {t: 0.20, m: 0.25, bk: 5}, 28: {t: 0.10, m: 0.125, bk: 5}}, src: "Garmin 190-01112-10 Rev 28, Table 1-4; 3.2.1"}]},
];
const SHORT = {gtn650: "GTN 650", gtn750: "GTN 750", gtn635: "GTN 635", gtn625: "GTN 625", gtn725: "GTN 725", gma35: "GMA 35", gma345: "GMA 345", gtx345: "GTX 345", g5: "G5"};

let P = null;            // project
let UI = {tab: "res", sel: 0, flt: "all"};
const $ = id => document.getElementById(id);
function setProject(x) { P = x; }
const uid = () => Math.random().toString(36).slice(2, 9);
const num = (v, d = 0) => { const x = parseFloat(String(v).replace(",", ".")); return isFinite(x) ? x : d; };
const pct = x => (x * 100).toFixed(1).replace(".", ",") + " %";
const f1 = x => (Math.abs(x) < 1e6 ? x.toFixed(1) : "∞").replace(".", ",");
const f2 = x => x.toFixed(2).replace(".", ",");
const fmin = x => (x >= 0 ? "+" : "") + f1(x) + " min";
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]));
const css = v => (typeof getComputedStyle === "undefined") ? "" : getComputedStyle(document.documentElement).getPropertyValue(v).trim();

function roleOf(name, cls) {
  const n = name.toLowerCase();
  if (/\bTX\b/.test(name)) return "tx";
  if (n.includes("landing") && cls === "intermittent") return "landing";
  if (n.includes("flap motor")) return "flap";
  if (n.includes("pitot")) return "pitot";
  return "none";
}
const pick = (d, V) => d ? (d[V] ?? d[String(V)] ?? d[V + ".0"]) : undefined;

// ---------- import / export (loader format: python -m ela_stc projeto.json rules.yaml saida) ----------
function fromLoader(d) {
  if (d.ela_web) return JSON.parse(JSON.stringify(d.ela_web));
  const inst = d.installation || {added: [], removed: [], removed_by_model: {}};
  const models = d.aml.map(a => ({
    id: uid(), model: a.model, tcds: a.tcds || "", cert: a.cert_basis || "", V: a.voltage, Vb: a.battery_v || a.voltage,
    alt: a.alternator_a, req: a.required_endurance_min ?? 30, src: a.source || "",
    bat: {nom: a.battery.capacity_ah, basis: "1h", H: a.battery.rated_hours ?? 1, n: a.battery.peukert_n ?? 1.2,
      soh: a.battery.soh ?? 1, soc: a.battery.soc ?? 1, kt: a.battery.temp_factor ?? 1},
    base: a.baseline_loads.map(l => ({id: uid(), n: l.name, bus: l.bus || "main", cls: l.cls || "continuous",
      i: pick(l.current_by_v, a.voltage) ?? l.current_a ?? 0, ib: l.current_batt_a ?? null,
      bk: pick(l.breaker_by_v, a.voltage) ?? l.breaker_a ?? null, cp: l.constant_power ?? (l.bus === "avionics"),
      duty: Object.assign({}, l.duty), src: l.source || "", role: roleOf(l.name, l.cls || "continuous"),
      radio: l.radio ?? null, circuit: l.circuit ?? null})),
    removed: [...(inst.removed || []), ...((inst.removed_by_model || {})[a.model] || [])],
  }));
  const volts = [...new Set(d.aml.map(a => String(parseFloat(a.voltage))))];
  const added = (inst.added || []).map(l => {
    let byV;
    if (l.current_by_v) byV = Object.fromEntries(Object.entries(l.current_by_v).map(([v, m]) => [String(parseFloat(v)),
      {m, t: pick(l.typical_by_v, v) ?? m, bk: pick(l.breaker_by_v, v) ?? l.breaker_a ?? null}]));
    else byV = Object.fromEntries(volts.map(v => [v, {m: l.current_a ?? 0, t: l.current_a ?? 0, bk: pick(l.breaker_by_v, v) ?? l.breaker_a ?? null}]));
    return {id: uid(), cat: "custom", label: l.name, unit: 1, essential: (l.duty || {}).emergency > 0,
      rows: [{n: "", role: roleOf(l.name, l.cls || "continuous"), cls: l.cls || "continuous", src: l.source || "",
        duty: Object.assign({}, l.duty), radio: l.radio ?? null, circuit: l.circuit ?? null, bus: l.bus || "avionics",
        cp: l.constant_power ?? ((l.bus || "avionics") === "avionics"), byV}]};
  });
  return {name: inst.name || "Projeto ELA", models, added, params: Object.assign(defaultParams(), d.analysis_params || {})};
}

function suffix(name, role, cls) {
  if (role === "tx" && !/\bTX\b/.test(name)) return name + " [TX]";
  if (role === "landing" && !name.toLowerCase().includes("landing")) return name + " (landing light)";
  if (role === "flap" && !name.toLowerCase().includes("flap motor")) return name + " (flap motor)";
  if (role === "pitot" && !name.toLowerCase().includes("pitot")) return name + " (pitot)";
  return name;
}

function toLoader() {
  const removed_by_model = {}, aml = P.models.map(m => {
    removed_by_model[m.model] = m.base.filter(r => m.removed.includes(r.n)).map(r => suffix(r.n, r.role, r.cls));
    return {model: m.model, tcds: m.tcds, cert_basis: m.cert, voltage: m.V, battery_v: m.Vb, alternator_a: m.alt,
      required_endurance_min: m.req, source: m.src,
      battery: {capacity_ah: c1(m), chemistry: "lead-acid", rated_hours: 1, peukert_n: m.bat.n, soh: m.bat.soh,
        soc: m.bat.soc ?? 1, temp_factor: m.bat.kt},
      buses: [...new Set(["main", "avionics", ...m.base.map(r => r.bus)])].map(name => ({name})),
      baseline_loads: m.base.map(r => Object.assign({name: suffix(r.n, r.role, r.cls), bus: r.bus, current_a: r.i, duty: r.duty, cls: r.cls,
        constant_power: !!r.cp, source: r.src}, r.bk ? {breaker_a: r.bk} : {}, r.ib != null ? {current_batt_a: r.ib} : {},
        r.radio ? {radio: r.radio} : {}, r.circuit ? {circuit: r.circuit} : {}))};
  });
  const added = [];
  for (const e of P.added) for (const r of e.rows) {
    const cur = {}, typ = {}, bk = {};
    for (const [v, x] of Object.entries(r.byV)) { cur[v] = x.m; typ[v] = x.t ?? x.m; if (x.bk) bk[v] = x.bk; }
    const ids = rowIds(e, r);
    added.push(Object.assign({name: suffix(rowName(e, r), r.role, r.cls), bus: r.bus || "avionics", current_by_v: cur, typical_by_v: typ,
      duty: dutyOf(e, r), cls: r.cls || (r.role === "tx" ? "intermittent" : "continuous"), constant_power: r.cp ?? true, source: r.src},
      Object.keys(bk).length ? {breaker_by_v: bk} : {}, ids.radio ? {radio: ids.radio} : {}, ids.circuit ? {circuit: ids.circuit} : {}));
  }
  const analysis_params = Object.fromEntries(Object.entries(P.params).filter(([, v]) => v != null));
  return {aml, installation: {name: P.name, removed: [], removed_by_model, added}, analysis_params, ela_web: P};
}

// ---------- engine input ----------
const c1 = m => m.bat.nom * (m.bat.basis === "5h" ? 0.85 : 1);
const rowName = (e, r) => {
  const base = e.cat === "custom" ? e.label : SHORT[e.cat] || e.label;
  const unit = P.added.filter(x => x.cat === e.cat && e.cat !== "custom").length > 1 || e.unit > 1 ? ` #${e.unit}` : "";
  return [base + unit, r.n].filter(Boolean).join(" ");
};
const rowIds = (e, r) => ({
  radio: r.radio || (r.com ? `${e.id}_com` : null),
  circuit: r.circuit || (r.com ? `${rowName(e, {n: "COM"})}` : null)});
const dutyOf = (e, r) => {
  if (r.duty) return Object.assign({}, r.duty);
  const d = Object.assign({}, ON);
  if (r.role === "tx") for (const k in d) d[k] = 0.1;
  d.emergency = e.essential ? (r.role === "tx" ? 0.1 : 1) : 0;
  return d;
};
function engineModel(m) {
  const items = m.base.map(r => ({n: r.n, bus: r.bus, cls: r.cls, st: m.removed.includes(r.n) ? "removed" : "base", imax: r.i, ityp: null,
    ibat: r.ib, bk: r.bk || null, cp: !!r.cp, duty: r.duty, src: r.src, tx: r.role === "tx", ll: r.role === "landing" && r.cls === "intermittent",
    flap: r.role === "flap", pitot: r.role === "pitot", radio: r.radio || null, circuit: r.circuit || null}));
  const missing = [];
  for (const e of P.added) for (const r of e.rows) {
    const x = r.byV[String(m.V)];
    if (!x) { missing.push(rowName(e, r)); continue; }
    const cls = r.cls || (r.role === "tx" ? "intermittent" : "continuous");
    const ids = rowIds(e, r);
    items.push({n: rowName(e, r), bus: r.bus || "avionics", cls, st: "added", imax: x.m, ityp: x.t ?? x.m, ibat: null, bk: x.bk || null, cp: r.cp ?? true,
      duty: dutyOf(e, r), src: r.src, tx: r.role === "tx", ll: false, flap: false, pitot: false, radio: ids.radio, circuit: ids.circuit});
  }
  return {model: m.model, V: m.V, Vb: m.Vb, alt: m.alt, req: m.req,
    bat: {C: c1(m), H: 1, n: m.bat.n, soh: m.bat.soh, soc: m.bat.soc ?? 1, kt: m.bat.kt, scen: false}, items, missing};
}
function defaultParams() { return {use_typical: 1, tx_duty: 0.10, landing_light_duty: 1.0, preshed_min: 5, pitot_em: 1, cp_scaling: 1, casa_fraction: 0.72, soh: null, soc: null, temp_factor: null, peukert_n: null}; }
const prm = () => Object.assign({}, P.params);

// ---------- persistence (this browser) ----------
function save() { try { localStorage.setItem("ela_stc_project_v3", JSON.stringify(P)); } catch (e) {} }
function load() { try { const s = localStorage.getItem("ela_stc_project_v3"); return s ? JSON.parse(s) : null; } catch (e) { return null; } }

function defaultProject() {
  const p = fromLoader(DEFAULT_CASE);
  p.models[1].bat = Object.assign(p.models[1].bat, {nom: 12.75, basis: "5h"});
  p.models[0].bat.nom = 22;
  p.models[0].src += " · bateria: Concorde RG-25, 22 Ah C1";
  p.models[1].src += " · bateria 12,75 Ah na taxa de 5 h";
  p.added = ["gtn650", "gma345", "gtx345", "g5"].map(c => newEquip(c));
  p.name = "GTN 650 + GMA 345 + GTX 345 + G5";
  return p;
}
function newEquip(cat) {
  const c = CATALOG.find(x => x.id === cat);
  const unit = P ? P.added.filter(x => x.cat === cat).length + 1 : 1;
  return {id: uid(), cat, label: c.label, unit, essential: unit === 1,
    rows: c.rows.map(r => ({n: r.n, role: r.role || "none", com: !!r.com, cls: r.role === "tx" ? "intermittent" : "continuous", src: r.src, byV: JSON.parse(JSON.stringify(r.byV))}))};
}

// ---------- rendering ----------
function render() {
  document.querySelectorAll("[data-tab]").forEach(b => b.setAttribute("aria-selected", b.dataset.tab === UI.tab ? "true" : "false"));
  document.querySelectorAll(".view").forEach(v => v.hidden = v.id !== "v-" + UI.tab);
  UI.sel = Math.min(UI.sel, P.models.length - 1);
  $("pname").value = P.name;
  renderParams();
  if (UI.tab === "res") renderResults();
  if (UI.tab === "inst") renderInst();
  if (UI.tab === "base") renderBase();
  if (UI.tab === "acft") renderAcft();
  save();
}

function modelPicker(target) {
  $(target).innerHTML = P.models.map((m, i) => `<button data-sel="${i}" aria-pressed="${i === UI.sel}">${esc(m.model)}</button>`).join("");
}

function renderParams() {
  const p = P.params;
  const seg = (k, a, b, la, lb) => `<div class="seg"><button data-p="${k}" data-v="${a}" aria-pressed="${p[k] == a}">${la}</button><button data-p="${k}" data-v="${b}" aria-pressed="${p[k] == b}">${lb}</button></div>`;
  const sl = (k, label, min, max, step, val, fmt, note, def) => `<div class="ctl"><label for="p_${k}">${label} <span class="num">${fmt(val)}</span></label>
    <input type="range" id="p_${k}" data-r="${k}" min="${min}" max="${max}" step="${step}" value="${val}">${note ? `<small>${note}</small>` : ""}</div>`;
  const m = P.models[UI.sel];
  $("params").innerHTML = `
    <div class="ctl"><label>Corrente dos equipamentos novos</label>${seg("use_typical", 1, 0, "Típica", "Máxima")}<small>Típica: CASA AC 21-38 4.3.2 e Garmin 3.7.2. R2 sempre usa a máxima.</small></div>
    ${sl("tx_duty", "Transmissão COM", 0.05, 0.2, 0.01, p.tx_duty, x => Math.round(x * 100) + " %", "Cessna nota J: 1 min a cada 10.")}
    ${sl("landing_light_duty", "Farol na decolagem e no pouso", 0.3, 1, 0.01, p.landing_light_duty, x => Math.round(x * 100) + " %", "")}
    <hr>
    ${sl("soh", "Saúde da bateria (SOH)", 0.5, 1, 0.01, p.soh ?? m.bat.soh, x => Math.round(x * 100) + " %", "Concorde: retirar abaixo de 80 %.")}
    ${sl("soc", "Estado de carga (SOC)", 0.6, 1, 0.01, p.soc ?? (m.bat.soc ?? 1), x => Math.round(x * 100) + " %", "CASA 4.5.12.6 assume 90 %.")}
    ${sl("temp_factor", "Fator de temperatura", 0.6, 1, 0.01, p.temp_factor ?? m.bat.kt, f2, "1,0 = referência da capacidade; 0,7 = frio.")}
    ${sl("peukert_n", "Expoente de Peukert", 1.05, 1.35, 0.01, p.peukert_n ?? m.bat.n, f2, "")}
    <div class="ctl"><label>Tempo até o corte de cargas</label>${seg("preshed_min", 5, 10, "5 min", "10 min")}</div>
    <div class="ctl"><label>Pitot aquecido na emergência</label>${seg("pitot_em", 1, 0, "Ligado", "Desligado")}</div>
    <div class="ctl"><label>Correntes na tensão da bateria</label>${seg("cp_scaling", 1, 0, "Sim", "Não")}</div>
    <div class="ctl"><label>Fração disponível CASA</label>${seg("casa_fraction", 0.72, 0.75, "72 % (v2.1)", "75 % (exemplo B.2)")}</div>
    <button class="ghost" id="preset">Voltar às premissas-base</button>`;
}

function ruleCard(id, ok, big, what, src, delta) {
  const ne = ok === null;
  return `<div class="rule ${ne ? "ne" : ok ? "" : "fail"}"><div class="id">${id}<span class="chip">${ne ? "NÃO AVALIADO" : ok ? "ATENDE" : "NÃO ATENDE"}</span></div>
    <div class="big num">${big}</div><div class="what">${what}</div>${delta ? `<div class="delta">${delta}</div>` : ""}<div class="src">${src}</div></div>`;
}

function renderResults() {
  const p = prm();
  // AML matrix
  const rows = P.models.map((m, i) => {
    const em = engineModel(m), b = analyze(em, false, p), a = analyze(em, true, p), g = garmin(em);
    const c = (ok, t) => `<td class="num ${ok ? "ok" : "bad"}">${t}</td>`;
    return `<tr data-sel="${i}" class="${i === UI.sel ? "cur" : ""}"><th scope="row">${esc(m.model)}${em.missing.length ? ` <span class="warn" title="Sem dados para ${m.V} V: ${esc(em.missing.join(", "))}">⚠ dados faltando</span>` : ""}</th>
      ${c(a.cont <= 0.8, pct(a.cont))}${c(a.avg <= 0.8, pct(a.avg))}${a.bkMissing.length ? `<td class="num ne" title="Sem disjuntor: ${esc(a.bkMissing.join(", "))}">não avaliado</td>` : c(a.bk <= 0.85, a.bkName ? pct(a.bk) : "—")}${c(a.margin >= 0, fmin(a.margin))}
      <td class="num">${fmin(b.margin)}</td><td class="num">${g.net >= 0 ? "+" : "−"}${f2(Math.abs(g.net))} A · ${g.net <= 0 ? "dispensa" : "ELA completa"}</td></tr>`;
  }).join("");
  $("aml").innerHTML = `<thead><tr><th>Modelo (clique para detalhar)</th><th class="num">R1a contínua</th><th class="num">R1b média</th><th class="num">R2 disjuntor</th><th class="num">R3 margem</th><th class="num">Margem antes</th><th class="num">Atalho Garmin</th></tr></thead><tbody>${rows}</tbody>`;

  const m = P.models[UI.sel], em = engineModel(m), before = analyze(em, false, p), after = analyze(em, true, p), r = after;
  $("detail-title").textContent = m.model;
  $("rules").innerHTML =
    ruleCard("R1a", r.cont <= 0.8, pct(r.cont), `Carga contínua no ${PT[r.contPh].toLowerCase()}: ${f1(r.contA)} A de ${m.alt} A. Limite 80 %.`, "AC 43.13-1B CHG 1, 11-35a/e", `antes ${pct(before.cont)}`) +
    ruleCard("R1b", r.avg <= 0.8, pct(r.avg), `Média da fase de ${PT[r.avgPh].toLowerCase()} com intermitentes: ${f1(r.avgA)} A. Limite 80 % (NZ: 85 %).`, "CASA AC 21-38 2.1.1 e 4.4.3; CAA NZ AC21-11", `antes ${pct(before.avg)}`) +
    ruleCard("R2", r.bkMissing.length ? null : r.bk <= 0.85, r.bkMissing.length ? "—" : pct(r.bk),
      r.bkMissing.length ? `Sem disjuntor informado para: ${esc(r.bkMissing.join(", "))}.` : `Maior carga contínua por circuito novo: ${esc(r.bkName)} (corrente máxima; ${r.bkN} circuitos avaliados). Limite 85 %.`,
      "CASA AWB 24-007; AC 21-38 4.6.4. Não avalia bitola nem proteção contra falha.", "") +
    ruleCard("R3", r.margin >= 0, fmin(r.margin), `Autonomia ${f1(Math.min(r.eCasa, r.eP))} min contra ${m.req} min (menor entre CASA e Peukert).`, "14 CFR 23.1353(h) emenda 62; AC 21-38 4.5.8", `antes ${fmin(before.margin)}`);
  const g = garmin(em), gok = g.net <= 0;
  $("garmin").innerHTML = `<div class="box"><h3>Atalho: variação líquida</h3><div class="kv"><span>Adicionado (típica, sem transmitir)</span><span class="num">+${f2(g.added)} A</span>
      <span>Removido (valores da linha de base)</span><span class="num">−${f2(g.removed)} A</span><span><b>Variação líquida</b></span><span class="num"><b>${g.net >= 0 ? "+" : "−"}${f2(Math.abs(g.net))} A</b></span></div>
      <div class="verdict" style="color:var(${gok ? "--good" : "--bad"})">${gok ? "Dispensa análise adicional" : "Exige ELA completa"}</div><small class="muted">GTN IM 3.7.2: dispensa se a carga cai, "assumindo que o sistema estava dentro dos limites".</small></div>
    <div class="box"><h3>ELA completa: a premissa confere?</h3><div class="kv"><span>Margem da bateria antes</span><span class="num">${fmin(before.margin)}</span><span>Margem depois</span><span class="num">${fmin(after.margin)}</span>
      <span>Carga média antes → depois</span><span class="num">${pct(before.avg)} → ${pct(after.avg)}</span></div>
      <div class="callout">${before.margin < 0 && gok ? "O atalho acerta a direção, mas o avião já estava abaixo do tempo exigido antes da instalação. Só a ELA completa mostra isso."
        : !gok ? "O atalho manda fazer a ELA completa; os cartões acima são essa análise." : "A premissa do atalho confere com estas entradas: o sistema estava dentro dos limites antes."}</div></div>`;
  $("missing").hidden = !em.missing.length;
  $("missing").textContent = em.missing.length ? `Itens sem dados para ${m.V} V ficaram fora do cálculo: ${em.missing.join(", ")}. Preencha na aba Instalação.` : "";
  drawPhase(em, before, after); drawBattery(em, r); drawTornado(em); drawTable(em);
}

function drawPhase(m, b, a) {
  const W = 520, H = 280, L = 44, R = 10, T = 14, B = 36, phs = ["ground", "taxi", "takeoff_climb", "cruise", "landing"];
  const vals = phs.flatMap(ph => [b.avgBy[ph], a.avgBy[ph]]).map(x => x / m.alt);
  const ymax = Math.max(1.0, Math.ceil(Math.max(...vals) * 10) / 10);
  const y = v => T + (H - T - B) * (1 - v / ymax), gw = (W - L - R) / phs.length, bw = gw * 0.3;
  let s = "";
  for (let t = 0; t <= ymax + 1e-9; t += 0.2) s += `<line x1="${L}" x2="${W - R}" y1="${y(t)}" y2="${y(t)}" stroke="${css("--line")}"/><text x="${L - 6}" y="${y(t) + 4}" text-anchor="end">${Math.round(t * 100)}%</text>`;
  phs.forEach((ph, i) => {
    const x0 = L + i * gw + gw / 2 - bw - 2;
    [[b, "--before", 0], [a, "--after", 1]].forEach(([r, c, j]) => {
      const v = r.avgBy[ph] / m.alt, vc = r.contBy[ph] / m.alt, x = x0 + j * (bw + 4);
      s += `<rect x="${x}" y="${y(v)}" width="${bw}" height="${y(0) - y(v)}" fill="${css(c)}"><title>${PT[ph]} ${j ? "depois" : "antes"}: média ${pct(v)}, contínua ${pct(vc)}</title></rect>`;
      s += `<line x1="${x + 2}" x2="${x + bw - 2}" y1="${y(vc)}" y2="${y(vc)}" stroke="${css("--surface")}" stroke-width="2"/>`;
    });
    s += `<text class="lbl" x="${L + i * gw + gw / 2}" y="${H - B + 18}" text-anchor="middle">${PT[ph]}</text>`;
  });
  s += `<line x1="${L}" x2="${W - R}" y1="${y(0.8)}" y2="${y(0.8)}" stroke="${css("--accent")}" stroke-width="2" stroke-dasharray="6 4"/><text x="${W - R}" y="${y(0.8) - 5}" text-anchor="end" style="fill:${css("--accent")}">80 %</text>`;
  $("phase").innerHTML = s;
}

function drawBattery(m, r) {
  const p = Object.assign({}, BASE, P.params), W = 520, H = 280, L = 48, R = 14, T = 14, B = 40;
  const avail = r.C1 * 60 * p.casa_fraction, tPre = p.preshed_min, tApp = p.approach_min;
  const pre = r.iPre * tPre * (r.iPre > 2 * r.C1 ? 1.2 : 1), E = r.eCasa, tEnd = E - tApp;
  const xmax = Math.max(40, Math.ceil((Math.min(E, 200) + 5) / 10) * 10);
  const x = t => L + (W - L - R) * Math.min(t, xmax) / xmax, y = q => T + (H - T - B) * (1 - q / avail);
  let s = "";
  for (let q = 0; q <= 1.0001; q += 0.25) s += `<line x1="${L}" x2="${W - R}" y1="${y(q * avail)}" y2="${y(q * avail)}" stroke="${css("--line")}"/><text x="${L - 6}" y="${y(q * avail) + 4}" text-anchor="end">${Math.round(q * 100)}%</text>`;
  for (let t = 0; t <= xmax; t += xmax > 100 ? 20 : 10) s += `<text x="${x(t)}" y="${H - B + 16}" text-anchor="middle">${t}</text>`;
  s += `<text x="${(L + W - R) / 2}" y="${H - 6}" text-anchor="middle">minutos após a perda do alternador</text>`;
  const pts = [[0, avail], [Math.min(tPre, E), avail - pre * Math.min(tPre, E) / tPre]];
  if (E > tPre) { pts.push([tEnd, r.iApp * tApp]); pts.push([E, 0]); }
  const P2 = pts.map(([t, q]) => `${x(t)},${y(Math.max(q, 0))}`).join(" ");
  s += `<polygon points="${x(0)},${y(0)} ${P2} ${x(pts[pts.length - 1][0])},${y(0)}" fill="${css("--after")}" opacity="0.15"/><polyline points="${P2}" fill="none" stroke="${css("--after")}" stroke-width="2.5"/>`;
  s += `<line x1="${x(m.req)}" x2="${x(m.req)}" y1="${T}" y2="${y(0)}" stroke="${css("--accent")}" stroke-width="2" stroke-dasharray="6 4"/><text x="${x(m.req) + 4}" y="${T + 12}" style="fill:${css("--accent")}">${m.req} min</text>`;
  if (E > tPre + tApp) [[tPre / 2, r.iPre], [tPre + (tEnd - tPre) / 2, r.iShed], [tEnd + tApp / 2, r.iApp]].forEach(([t, v], i) => { s += `<text x="${x(t)}" y="${y(0) - 8 - (i % 2) * 14}" text-anchor="middle" class="lbl">${f1(v)} A</text>`; });
  s += `<circle cx="${x(E)}" cy="${y(0)}" r="4" fill="${css(r.margin >= 0 ? "--good" : "--bad")}"/>`;
  $("bat").innerHTML = s;
  $("batkv").innerHTML = `<span>Disponível (${f2(r.C1)} Ah × 60 × ${Math.round(p.casa_fraction * 100)} %)</span><span class="num">${f1(avail)} A·min</span>
    <span>Até o corte: ${tPre} min a ${f2(r.iPre)} A${r.iPre > 2 * r.C1 ? " (+20 %)" : ""}</span><span class="num">${f1(pre)} A·min</span>
    <span>Reserva da aproximação: ${tApp} min a ${f2(r.iApp)} A</span><span class="num">${f1(r.iApp * tApp)} A·min</span>
    <span>Cruzeiro de emergência a ${f2(r.iShed)} A</span><span class="num">${f1(Math.max(0, E - tPre - tApp))} min</span>
    <span><b>Autonomia CASA / Peukert</b></span><span class="num"><b>${f1(r.eCasa)} / ${f1(r.eP)} min</b></span>`;
}

function drawTornado(m) {
  const p = prm(), base = analyze(m, true, p).margin;
  const rows = PARAMS.filter(q => q.key !== "bat_capacity_factor").map(q => ({label: q.label,
    lo: analyze(m, true, Object.assign({}, p, {[q.key]: q.low})).margin, hi: analyze(m, true, Object.assign({}, p, {[q.key]: q.high})).margin}))
    .filter(r => Math.abs(r.lo - base) > 0.05 || Math.abs(r.hi - base) > 0.05)
    .sort((a, b) => Math.max(Math.abs(b.lo - base), Math.abs(b.hi - base)) - Math.max(Math.abs(a.lo - base), Math.abs(a.hi - base)));
  const W = 760, rowH = 30, T = 26, H = T + rows.length * rowH + 30, Lx = 250, R = 20;
  const all = rows.flatMap(r => [r.lo, r.hi]).concat([base, 0]);
  const mn = Math.floor(Math.min(...all) / 5) * 5, mx = Math.ceil(Math.max(...all) / 5) * 5 || 5;
  const x = v => Lx + (W - Lx - R) * (v - mn) / (mx - mn || 1), step = (mx - mn) > 40 ? 10 : 5;
  let s = "";
  for (let t = mn; t <= mx; t += step) s += `<line x1="${x(t)}" x2="${x(t)}" y1="${T - 6}" y2="${H - 24}" stroke="${css("--line")}"/><text x="${x(t)}" y="${H - 8}" text-anchor="middle">${t}</text>`;
  s += `<line x1="${x(0)}" x2="${x(0)}" y1="${T - 6}" y2="${H - 24}" stroke="${css("--bad")}" stroke-width="2"/><text x="${x(0) + 4}" y="${H - 28}" style="fill:${css("--bad")}">margem 0</text>`;
  rows.forEach((r, i) => {
    const yy = T + i * rowH, a = Math.min(r.lo, r.hi, base), b = Math.max(r.lo, r.hi, base);
    s += `<text class="lbl" x="${Lx - 10}" y="${yy + 18}" text-anchor="end">${esc(r.label)}</text><rect x="${x(a)}" y="${yy + 6}" width="${Math.max(1, x(b) - x(a))}" height="${rowH - 12}" fill="${css("--after")}" opacity="0.25"/>`;
    [r.lo, r.hi].forEach(v => { s += `<circle cx="${x(v)}" cy="${yy + rowH / 2}" r="4.5" fill="${css(v < 0 ? "--bad" : "--after")}"><title>${esc(r.label)}: ${f1(v)} min</title></circle>`; });
  });
  s += `<line x1="${x(base)}" x2="${x(base)}" y1="${T - 2}" y2="${H - 24}" stroke="${css("--ink")}" stroke-width="1.5" stroke-dasharray="3 3"/><text x="${x(base)}" y="${T - 12}" text-anchor="middle" class="lbl">atual ${f1(base)}</text>`;
  const svg = $("tornado"); svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = s;
}

function drawTable(m) {
  const p = Object.assign({}, BASE, P.params), L = analyze(m, true, p).loads;
  let rows = L.concat(m.items.filter(it => it.st === "removed").map(it => Object.assign({}, it, {I: it.imax})));
  if (UI.flt === "chg") rows = rows.filter(r => r.st !== "base");
  if (UI.flt === "em") rows = rows.filter(r => (r.duty.emergency || 0) > 0);
  const bI = l => !p.cp_scaling ? l.I : (l.ibat != null && !l.useTyp) ? l.ibat : l.cp ? l.I * m.V / m.Vb : l.I;
  const ph = ["taxi", "takeoff_climb", "cruise", "landing", "emergency"];
  $("loads").innerHTML = `<thead><tr><th>Situação</th><th>Item</th><th>Classe</th><th class="num">I usada (A)</th><th class="num">I bateria (A)</th><th class="num">Disj. (A)</th>${ph.map(x => `<th class="num">k ${PT[x]}</th>`).join("")}<th>Fonte</th></tr></thead><tbody>` +
    rows.map(r => `<tr class="${r.st}"><td class="st"><span class="${r.st}">${r.st === "added" ? "ENTRA" : r.st === "removed" ? "SAI" : "BASE"}</span></td><td>${esc(r.n)}</td><td>${r.cls === "continuous" ? "contínua" : "intermitente"}</td>
      <td class="num">${f2(r.I)}${r.useTyp ? " <small class='muted'>típ.</small>" : ""}</td><td class="num">${r.st === "removed" ? "" : f2(bI(r))}</td><td class="num">${r.bk ?? ""}</td>
      ${ph.map(x => `<td class="num">${(r.duty[x] || 0) ? f2(r.duty[x]) : ""}</td>`).join("")}<td><small>${esc(r.src)}</small></td></tr>`).join("") + "</tbody>";
}

// ---------- Instalação ----------
function renderInst() {
  $("cat").innerHTML = CATALOG.map(c => `<option value="${c.id}">${esc(c.label)}</option>`).join("");
  const Vs = [...new Set(P.models.map(m => String(m.V)))].sort();
  $("equip").innerHTML = P.added.length ? P.added.map((e, ei) => `<div class="equip">
    <div class="ehead"><input aria-label="Nome do equipamento" data-e="${ei}" data-f="label" value="${esc(e.label)}" ${e.cat !== "custom" ? "readonly" : ""}>
      <span class="muted">${e.cat !== "custom" ? `Unidade #${e.unit}` : "Personalizado"}</span>
      <label class="check"><input type="checkbox" data-e="${ei}" data-f="essential" ${e.essential ? "checked" : ""}> Ligado na emergência</label>
      <button class="ghost danger" data-del="${ei}">Remover</button></div>
    <div class="tablewrap flat"><table class="edit"><thead><tr><th>Parte</th><th>Papel</th>${Vs.map(v => `<th class="num">${v} V típica</th><th class="num">${v} V máxima</th><th class="num">${v} V disj.</th>`).join("")}<th>Fonte</th><th></th></tr></thead><tbody>
    ${e.rows.map((r, ri) => `<tr><td><input data-e="${ei}" data-r="${ri}" data-f="n" value="${esc(r.n)}" placeholder="(unidade)"></td>
      <td><select data-e="${ei}" data-r="${ri}" data-f="role"><option value="none" ${r.role === "none" ? "selected" : ""}>Contínua</option><option value="tx" ${r.role === "tx" ? "selected" : ""}>Transmissão</option></select></td>
      ${Vs.map(v => { const x = r.byV[v] || {}; return ["t", "m", "bk"].map(k => `<td><input class="n" inputmode="decimal" data-e="${ei}" data-r="${ri}" data-v="${v}" data-k="${k}" value="${x[k] ?? ""}" placeholder="—"></td>`).join(""); }).join("")}
      <td><input class="src" data-e="${ei}" data-r="${ri}" data-f="src" value="${esc(r.src)}"></td><td><button class="ghost" data-delrow="${ei}:${ri}" aria-label="Apagar linha">×</button></td></tr>`).join("")}
    </tbody></table></div><button class="ghost" data-addrow="${ei}">+ Linha</button></div>`).join("") : `<p class="muted">Nenhum equipamento adicionado ainda. Escolha no catálogo acima ou crie um personalizado.</p>`;

  modelPicker("rm-pick");
  const m = P.models[UI.sel];
  $("rm-list").innerHTML = m.base.map(r => `<label class="check"><input type="checkbox" data-rm="${esc(r.n)}" ${m.removed.includes(r.n) ? "checked" : ""}> ${esc(r.n)} <span class="muted num">${f2(r.i)} A</span></label>`).join("");
}

// ---------- Linha de base ----------
function renderBase() {
  modelPicker("base-pick");
  const m = P.models[UI.sel];
  $("base-tbl").innerHTML = `<thead><tr><th>Item</th><th>Barra</th><th>Classe</th><th>Papel</th><th class="num">I (A) a ${m.V} V</th><th class="num">I na bateria (A)</th><th class="num">Disj. (A)</th>${PHS.map(p => `<th class="num">k ${PT[p]}</th>`).join("")}<th>Fonte</th><th></th></tr></thead><tbody>` +
    m.base.map((r, i) => `<tr><td><input data-b="${i}" data-f="n" value="${esc(r.n)}"></td>
      <td><select data-b="${i}" data-f="bus"><option ${r.bus === "main" ? "selected" : ""}>main</option><option ${r.bus === "avionics" ? "selected" : ""}>avionics</option><option ${r.bus === "essential" ? "selected" : ""}>essential</option></select></td>
      <td><select data-b="${i}" data-f="cls"><option value="continuous" ${r.cls === "continuous" ? "selected" : ""}>contínua</option><option value="intermittent" ${r.cls === "intermittent" ? "selected" : ""}>intermitente</option></select></td>
      <td><select data-b="${i}" data-f="role">${Object.entries(ROLES).map(([k, v]) => `<option value="${k}" ${r.role === k ? "selected" : ""}>${v}</option>`).join("")}</select></td>
      <td><input class="n" inputmode="decimal" data-b="${i}" data-f="i" value="${r.i}"></td><td><input class="n" inputmode="decimal" data-b="${i}" data-f="ib" value="${r.ib ?? ""}" placeholder="auto"></td>
      <td><input class="n" inputmode="decimal" data-b="${i}" data-f="bk" value="${r.bk ?? ""}" placeholder="—"></td>
      ${PHS.map(p => `<td><input class="n k" inputmode="decimal" data-b="${i}" data-d="${p}" value="${r.duty[p] ?? ""}" placeholder="0"></td>`).join("")}
      <td><input class="src" data-b="${i}" data-f="src" value="${esc(r.src)}"></td><td><button class="ghost" data-delb="${i}" aria-label="Apagar carga">×</button></td></tr>`).join("") + "</tbody>";
}

// ---------- Aeronaves ----------
function renderAcft() {
  $("acft-list").innerHTML = P.models.map((m, i) => `<div class="acft">
    <div class="ehead"><input aria-label="Modelo" data-m="${i}" data-f="model" value="${esc(m.model)}"><button class="ghost" data-dup="${i}">Duplicar</button>${P.models.length > 1 ? `<button class="ghost danger" data-delm="${i}">Remover</button>` : ""}</div>
    <div class="grid">
      <label>TCDS<input data-m="${i}" data-f="tcds" value="${esc(m.tcds)}"></label>
      <label>Base de certificação<input data-m="${i}" data-f="cert" value="${esc(m.cert)}"></label>
      <label>Tensão da barra (V)<input class="n" data-m="${i}" data-f="V" value="${m.V}"></label>
      <label>Tensão da bateria (V)<input class="n" data-m="${i}" data-f="Vb" value="${m.Vb}"></label>
      <label>Alternador (A)<input class="n" data-m="${i}" data-f="alt" value="${m.alt}"></label>
      <label>Autonomia exigida (min)<input class="n" data-m="${i}" data-f="req" value="${m.req}"></label>
      <label>Bateria nominal (Ah)<input class="n" data-m="${i}" data-bat="nom" value="${m.bat.nom}"></label>
      <label>Taxa da capacidade<select data-m="${i}" data-bat="basis"><option value="1h" ${m.bat.basis === "1h" ? "selected" : ""}>1 h (C1)</option><option value="5h" ${m.bat.basis === "5h" ? "selected" : ""}>5 h (× 0,85)</option></select></label>
      <label>SOH<input class="n" data-m="${i}" data-bat="soh" value="${m.bat.soh}"></label>
      <label>Fator de temperatura<input class="n" data-m="${i}" data-bat="kt" value="${m.bat.kt}"></label>
      <label>Expoente de Peukert<input class="n" data-m="${i}" data-bat="n" value="${m.bat.n}"></label>
      <label class="wide">Fonte<input data-m="${i}" data-f="src" value="${esc(m.src)}"></label>
    </div><small class="muted">Capacidade usada: ${f2(c1(m))} Ah na taxa de 1 h · ${m.base.length} cargas na linha de base · ${m.removed.length} removidas</small></div>`).join("");
}

// ---------- events ----------
function bind() {
  document.addEventListener("click", async ev => {
    const t = ev.target.closest("button, tr[data-sel]"); if (!t) return;
    const d = t.dataset;
    if (d.tab) { UI.tab = d.tab; return render(); }
    if (d.sel != null) { UI.sel = +d.sel; return render(); }
    if (d.p) { P.params[d.p] = num(d.v); return render(); }
    if (t.id === "preset") { P.params = defaultParams(); return render(); }
    if (t.id === "add-cat") { P.added.push(newEquip($("cat").value)); return render(); }
    if (t.id === "add-custom") { P.added.push({id: uid(), cat: "custom", label: "Equipamento novo", unit: 1, essential: false, rows: [{n: "", role: "none", cls: "continuous", src: "Informar fonte", byV: {}}]}); return render(); }
    if (d.del != null) { P.added.splice(+d.del, 1); renumber(); return render(); }
    if (d.addrow != null) { P.added[+d.addrow].rows.push({n: "", role: "none", cls: "continuous", src: "", byV: {}}); return render(); }
    if (d.delrow) { const [e, r] = d.delrow.split(":").map(Number); P.added[e].rows.splice(r, 1); return render(); }
    if (d.delb != null) { const m = P.models[UI.sel]; const [x] = m.base.splice(+d.delb, 1); m.removed = m.removed.filter(n => n !== x.n); return render(); }
    if (t.id === "add-base") { P.models[UI.sel].base.push({id: uid(), n: "Carga nova", bus: "main", cls: "continuous", i: 0, ib: null, bk: null, cp: false, duty: Object.assign({}, ON), src: "Informar fonte", role: "none"}); return render(); }
    if (d.dup != null) { const c = JSON.parse(JSON.stringify(P.models[+d.dup])); c.id = uid(); c.model += " (cópia)"; P.models.push(c); return render(); }
    if (d.delm != null) { P.models.splice(+d.delm, 1); UI.sel = 0; return render(); }
    if (t.id === "new-blank") { P.models.push({id: uid(), model: "Modelo novo", tcds: "", cert: "", V: 28, Vb: 24, alt: 60, req: 30, src: "Informar fonte", bat: {nom: 10, basis: "1h", n: 1.2, soh: 0.8, kt: 0.9}, base: [], removed: []}); UI.sel = P.models.length - 1; return render(); }
    if (t.id === "reset-all") { if (t.dataset.armed) { P = defaultProject(); UI.sel = 0; t.dataset.armed = ""; t.textContent = "Recomeçar com o exemplo C172"; return render(); }
      t.dataset.armed = "1"; t.textContent = "Clique de novo para apagar o projeto atual"; return; }
    if (t.id === "exp-json") return exportFile(slug() + ".json", JSON.stringify(toLoader(), null, 2));
    if (t.id === "exp-csv") return exportFile(slug() + "_matriz.csv", csvMatrix());
    if (t.id === "copy-json") { const s = JSON.stringify(toLoader(), null, 2); try { await navigator.clipboard.writeText(s); note("Projeto copiado."); } catch (e) { $("paste").value = s; $("paste").select(); note("Texto selecionado: copie com Ctrl+C."); } return; }
    if (t.id === "imp-paste") { try { P = fromLoader(JSON.parse($("paste").value)); UI.sel = 0; note("Projeto importado."); render(); } catch (e) { note("Não consegui ler o texto. Cole um JSON exportado por esta ferramenta."); } return; }
  });
  document.addEventListener("input", ev => {
    const el = ev.target, d = el.dataset;
    if (d.r && el.type === "range") { P.params[d.r] = num(el.value); return render(); }
  });
  document.addEventListener("change", ev => {
    const el = ev.target, d = el.dataset;
    if (el.id === "pname") { P.name = el.value; return save(); }
    if (el.id === "flt") { UI.flt = el.value; return render(); }
    if (d.e != null) {
      const e = P.added[+d.e];
      if (d.f === "label") e.label = el.value;
      else if (d.f === "essential") e.essential = el.checked;
      else if (d.r != null) {
        const r = e.rows[+d.r];
        if (d.f === "n" || d.f === "src") r[d.f] = el.value;
        else if (d.f === "role") { r.role = el.value; r.cls = el.value === "tx" ? "intermittent" : "continuous"; }
        else if (d.v) { r.byV[d.v] = r.byV[d.v] || {}; if (el.value.trim() === "") delete r.byV[d.v][d.k]; else r.byV[d.v][d.k] = num(el.value);
          if (r.byV[d.v].m == null && r.byV[d.v].t != null) r.byV[d.v].m = r.byV[d.v].t; if (r.byV[d.v].m == null) delete r.byV[d.v]; }
      }
      return render();
    }
    if (d.rm != null) { const m = P.models[UI.sel]; m.removed = el.checked ? [...m.removed, d.rm] : m.removed.filter(n => n !== d.rm); return render(); }
    if (d.b != null) {
      const r = P.models[UI.sel].base[+d.b];
      if (d.d) { const v = num(el.value, 0); if (v > 0) r.duty[d.d] = Math.min(v, 1); else delete r.duty[d.d]; }
      else if (d.f === "n") { const m = P.models[UI.sel]; m.removed = m.removed.map(n => n === r.n ? el.value : n); r.n = el.value; }
      else if (["i"].includes(d.f)) r.i = num(el.value);
      else if (["ib", "bk"].includes(d.f)) r[d.f] = el.value.trim() === "" ? null : num(el.value);
      else { r[d.f] = el.value; if (d.f === "bus") r.cp = el.value === "avionics"; }
      return render();
    }
    if (d.m != null) {
      const m = P.models[+d.m];
      if (d.bat) m.bat[d.bat] = d.bat === "basis" ? el.value : num(el.value, m.bat[d.bat]);
      else if (["V", "Vb", "alt", "req"].includes(d.f)) m[d.f] = num(el.value, m[d.f]);
      else m[d.f] = el.value;
      return render();
    }
  });
  $("imp-file").addEventListener("change", ev => {
    const f = ev.target.files[0]; if (!f) return;
    const rd = new FileReader();
    rd.onload = () => { try { P = fromLoader(JSON.parse(rd.result)); UI.sel = 0; note("Projeto importado de " + f.name + "."); render(); } catch (e) { note("Arquivo inválido. Use um .json exportado por esta ferramenta ou no formato do ELA-STC em Python."); } };
    rd.readAsText(f); ev.target.value = "";
  });
  if (window.matchMedia) matchMedia("(prefers-color-scheme: dark)").addEventListener?.("change", render);
  new MutationObserver(render).observe(document.documentElement, {attributes: true, attributeFilter: ["data-theme"]});
}
function renumber() { const c = {}; for (const e of P.added) if (e.cat !== "custom") { c[e.cat] = (c[e.cat] || 0) + 1; e.unit = c[e.cat]; } }
const slug = () => (P.name || "projeto").normalize("NFD").replace(/[^\w]+/g, "_").replace(/^_|_$/g, "").slice(0, 60) || "projeto";
function note(t) { $("note").textContent = t; }
function csvMatrix() {
  const p = prm(), q = s => `"${String(s).replace(/"/g, '""')}"`;
  const lines = [["Modelo", "R1a carga contínua", "R1b carga média", "R2 disjuntor", "R3 margem (min)", "Margem antes (min)", "Autonomia CASA (min)", "Autonomia Peukert (min)", "Variação líquida Garmin (A)"].map(q).join(",")];
  for (const m of P.models) { const em = engineModel(m), a = analyze(em, true, p), b = analyze(em, false, p), g = garmin(em);
    lines.push([m.model, a.cont.toFixed(4), a.avg.toFixed(4), a.bk.toFixed(4), a.margin.toFixed(2), b.margin.toFixed(2), a.eCasa.toFixed(2), a.eP.toFixed(2), g.net.toFixed(3)].map(q).join(",")); }
  return lines.join("\n");
}
let DL = null;
async function exportFile(name, text) {
  if (!DL) { note("Este visualizador não permite salvar arquivos. Use Copiar projeto."); return; }
  try { await DL.save({filename: name, data: text}); note("Arquivo salvo: " + name); }
  catch (e) { note(e && e.code === "declined" ? "Download cancelado." : "Não foi possível salvar o arquivo aqui. Use Copiar projeto."); }
}

if (typeof module !== "undefined" && typeof document === "undefined") {
  module.exports = {fromLoader, toLoader, engineModel, defaultProject, newEquip, defaultParams, setProject, getProject: () => P, CATALOG};
} else {
  P = load() || null;
  if (!P || !P.models) { P = null; P = defaultProject(); }
  bind(); render();
  (async () => { try { DL = window.claude?.use ? await window.claude.use("downloads") : null; } catch (e) { DL = null; }
    document.querySelectorAll(".needs-dl").forEach(b => b.hidden = !DL); })();
}
