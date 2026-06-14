"""Escriptura de les sortides: CSVs, resum en Markdown i HTML interactiu."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import fields
from pathlib import Path

from .process import (
    NEVER_RUN,
    DataSourceRow,
    InventoryRow,
    ReportRow,
    row_to_dict,
)

INVENTORY_CSV = "inventory_by_data_source.csv"
REPORTS_CSV = "reports_by_staleness.csv"
DATA_SOURCES_CSV = "data_sources.csv"
SUMMARY_MD = "summary.md"
REPORT_HTML = "index.html"


def _write_csv(path: Path, rows: list, row_type) -> None:
    headers = [f.name for f in fields(row_type)]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_dict(row))


def write_data_sources(
    rows: list[DataSourceRow], output_dir: str | Path
) -> Path:
    """Escriu l'inventari de fonts de dades. Retorna el path generat."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / DATA_SOURCES_CSV
    _write_csv(path, rows, DataSourceRow)
    return path


def write_outputs(
    inventory: list[InventoryRow],
    reports: list[ReportRow],
    output_dir: str | Path,
    *,
    top_n: int = 20,
) -> dict[str, Path]:
    """Escriu els dos CSV i el resum. Retorna els paths generats."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    inventory_path = out / INVENTORY_CSV
    reports_path = out / REPORTS_CSV
    summary_path = out / SUMMARY_MD
    html_path = out / REPORT_HTML

    _write_csv(inventory_path, inventory, InventoryRow)
    _write_csv(reports_path, reports, ReportRow)
    summary_path.write_text(
        _build_summary(inventory, reports, top_n), encoding="utf-8"
    )
    html_path.write_text(_build_html(inventory, reports), encoding="utf-8")

    return {
        "inventory": inventory_path,
        "reports": reports_path,
        "summary": summary_path,
        "html": html_path,
    }


def _build_summary(
    inventory: list[InventoryRow], reports: list[ReportRow], top_n: int
) -> str:
    total_reports = len(reports)
    total_queries = len(inventory)
    dead_queries = sum(1 for r in inventory if r.data_source_alive == "no")
    never_run = sum(1 for r in reports if r.days_since_last_run == NEVER_RUN)

    # Recompte de queries per font de dades.
    by_source = Counter(r.data_source_name for r in inventory)

    lines = [
        "# Resum — Inventari de reports/queries de MODE",
        "",
        f"- Reports totals: **{total_reports}**",
        f"- Queries totals (files d'inventari): **{total_queries}**",
        f"- Queries 'from definition' (sense font de dades real): **{dead_queries}**",
        f"- Reports mai executats: **{never_run}**",
        "",
        "## Queries per font de dades",
        "",
        "| Font de dades | Queries |",
        "| --- | --- |",
    ]
    for name, count in by_source.most_common():
        lines.append(f"| {name} | {count} |")

    lines += [
        "",
        f"## Top {top_n} reports més antics (o mai executats)",
        "",
        "| Report | Espai | Últim run | Dies | Arxivat |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in reports[:top_n]:
        last = row.last_run_at or NEVER_RUN
        lines.append(
            f"| {row.report_name} | {row.space_name} | {last} | "
            f"{row.days_since_last_run} | {row.is_archived} |"
        )

    return "\n".join(lines) + "\n"


def _build_html(
    inventory: list[InventoryRow], reports: list[ReportRow]
) -> str:
    """HTML autònom amb taula filtrable/ordenable de reports."""
    data = [row_to_dict(r) for r in reports]
    by_source = Counter(r.data_source_name for r in inventory)
    stats = {
        "reports": len(reports),
        "queries": len(inventory),
        "pure": sum(1 for r in reports if r.purity == "pure"),
        "mixed": sum(1 for r in reports if r.purity == "mixed"),
        "with_dead": sum(1 for r in reports if r.has_dead_source == "si"),
        "by_source": by_source.most_common(),
    }
    payload = json.dumps(
        {"reports": data, "stats": stats}, ensure_ascii=False
    )
    return _HTML_TEMPLATE.replace("__DATA__", payload)


_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='88'>&#129529;</text></svg>">
<title>MODE reports inventory</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 1.5rem; color: #1a1a2e; background: #f5f6fa; }
  h1 { margin: 0 0 .5rem; font-size: 1.4rem; }
  .cards { display: flex; flex-wrap: wrap; gap: .75rem; margin-bottom: 1rem; }
  .card { background: #fff; border-radius: 8px; padding: .6rem 1rem; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .card b { display: block; font-size: 1.4rem; }
  .controls { display: flex; flex-wrap: nowrap; gap: .4rem; margin-bottom: 1rem; overflow-x: auto; align-items: center; }
  input, select { padding: .4rem .5rem; border: 1px solid #ccc; border-radius: 6px; font-size: .82rem; }
  input#q { flex: 1 1 160px; min-width: 140px; }
  .controls select { flex: 0 0 auto; min-width: 0; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  th, td { padding: .5rem .6rem; text-align: left; border-bottom: 1px solid #eee; font-size: .85rem; vertical-align: top; }
  th { background: #1a1a2e; color: #fff; cursor: pointer; white-space: nowrap; position: sticky; top: 0; }
  th:hover { background: #2d2d4e; }
  tr:hover td { background: #f0f1f8; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }
  .tag { display: inline-block; padding: .1rem .45rem; border-radius: 4px; font-size: .72rem; font-weight: 600; }
  .pure { background: #dcfce7; color: #166534; }
  .mixed { background: #fef3c7; color: #92400e; }
  .sense_queries { background: #e5e7eb; color: #374151; }
  .dead { background: #fee2e2; color: #991b1b; }
  .sched { background: #dbeafe; color: #1e40af; }
  .muted { color: #888; }
  #count { color: #555; font-size: .85rem; margin-bottom: .4rem; }
</style>
</head>
<body>
<h1>MODE reports inventory</h1>
<div class="cards" id="cards"></div>
<div class="controls">
  <input id="q" placeholder="Search by report, collection or creator...">
  <select id="source"><option value="">All data sources</option></select>
  <select id="creator"><option value="">All creators</option></select>
  <select id="purity">
    <option value="">Pure and mixed</option>
    <option value="pure">Pure only</option>
    <option value="mixed">Mixed only</option>
    <option value="sense_queries">No queries</option>
  </select>
  <select id="dead">
    <option value="">From definition: all</option>
    <option value="si">Has from definition</option>
    <option value="no">No from definition</option>
  </select>
  <select id="sched">
    <option value="">Scheduled: all</option>
    <option value="si">Scheduled</option>
    <option value="no">Not scheduled</option>
  </select>
  <select id="ageop">
    <option value="">Any last run</option>
    <option value="gt">Last run more than</option>
    <option value="lt">Last run less than</option>
  </select>
  <select id="agerange">
    <option value="30">1 month</option>
    <option value="90">3 months</option>
    <option value="180">6 months</option>
    <option value="365">1 year</option>
    <option value="730" selected>2 years</option>
    <option value="1095">3 years</option>
  </select>
</div>
<div id="count"></div>
<table>
  <thead><tr>
    <th data-k="space_name">Collection</th>
    <th data-k="report_name">Report</th>
    <th data-k="data_sources">Data sources</th>
    <th data-k="purity">Purity</th>
    <th data-k="query_count">Queries</th>
    <th data-k="days_since_last_run">Time since last run</th>
    <th data-k="schedule">Schedule</th>
    <th data-k="creator">Creator</th>
    <th data-k="is_archived">Archived</th>
  </tr></thead>
  <tbody id="rows"></tbody>
</table>
<script>
const DATA = __DATA__;
const reports = DATA.reports;
let sortKey = "days_since_last_run", sortAsc = false;

function daysNum(v){ return v === "mai" ? Infinity : Number(v); }

function fmtAge(v){
  if (v === "mai") return "never";
  let d = Number(v);
  if (isNaN(d)) return v;
  const y = Math.floor(d / 365.25);
  let rem = d - y * 365.25;
  const m = Math.floor(rem / 30.44);
  const days = Math.round(rem - m * 30.44);
  const parts = [];
  if (y) parts.push(y + "y");
  if (m || y) parts.push(m + "m");
  parts.push(days + "d");
  return parts.join(" ");
}

function purityLabel(p){ return p === "sense_queries" ? "no queries" : p; }

function schedCell(r){
  if (r.has_schedule !== "si") return '<span class="muted">—</span>';
  const dl = r.schedule_delivery ? ` <span class="tag sched">${esc(r.schedule_delivery)}</span>` : "";
  return `${esc(r.schedule)}${dl}`;
}

function renderCards(rows){
  const queries = rows.reduce((a,r)=>a+Number(r.query_count||0),0);
  const pure = rows.filter(r=>r.purity==="pure").length;
  const mixed = rows.filter(r=>r.purity==="mixed").length;
  const dead = rows.filter(r=>r.has_dead_source==="si").length;
  const sched = rows.filter(r=>r.has_schedule==="si").length;
  document.getElementById("cards").innerHTML = [
    ["Reports", rows.length], ["Queries", queries],
    ["Pure", pure], ["Mixed", mixed], ["From definition", dead], ["Scheduled", sched]
  ].map(([k,v])=>`<div class="card"><b>${v}</b>${k}</div>`).join("");
}

function initFilters(){
  const sel = document.getElementById("source");
  DATA.stats.by_source.forEach(([name])=>{
    const o = document.createElement("option"); o.value = name; o.textContent = name; sel.appendChild(o);
  });
  const creators = [...new Set(reports.map(r=>r.creator).filter(Boolean))].sort();
  const csel = document.getElementById("creator");
  creators.forEach(c=>{
    const o = document.createElement("option"); o.value = c; o.textContent = c; csel.appendChild(o);
  });
}

function rowsFiltered(){
  const q = document.getElementById("q").value.toLowerCase();
  const src = document.getElementById("source").value;
  const cre = document.getElementById("creator").value;
  const pur = document.getElementById("purity").value;
  const dead = document.getElementById("dead").value;
  const sched = document.getElementById("sched").value;
  const ageop = document.getElementById("ageop").value;
  const agethr = Number(document.getElementById("agerange").value);
  return reports.filter(r=>{
    if (q && !(`${r.report_name} ${r.space_name} ${r.creator}`.toLowerCase().includes(q))) return false;
    if (src && !r.data_sources.split("; ").includes(src)) return false;
    if (cre && r.creator !== cre) return false;
    if (pur && r.purity !== pur) return false;
    if (dead && r.has_dead_source !== dead) return false;
    if (sched && r.has_schedule !== sched) return false;
    if (ageop){
      const n = daysNum(r.days_since_last_run);
      if (ageop === "gt" && !(n > agethr)) return false;
      if (ageop === "lt" && !(n < agethr)) return false;
    }
    return true;
  });
}

function render(){
  let rows = rowsFiltered();
  rows.sort((a,b)=>{
    let x = a[sortKey], y = b[sortKey];
    if (sortKey === "days_since_last_run"){ x = daysNum(x); y = daysNum(y); }
    if (sortKey === "query_count" || sortKey === "data_source_count"){ x = Number(x); y = Number(y); }
    if (x < y) return sortAsc ? -1 : 1;
    if (x > y) return sortAsc ? 1 : -1;
    return 0;
  });
  renderCards(rows);
  document.getElementById("count").textContent = `${rows.length} reports`;
  document.getElementById("rows").innerHTML = rows.map(r=>{
    const purClass = r.purity;
    const dead = r.has_dead_source === "si" ? ' <span class="tag dead">from definition</span>' : "";
    const name = r.report_url ? `<a href="${r.report_url}" target="_blank">${esc(r.report_name)}</a>` : esc(r.report_name);
    return `<tr>
      <td>${esc(r.space_name)}</td>
      <td>${name}${dead}</td>
      <td>${esc(r.data_sources)}</td>
      <td><span class="tag ${purClass}">${purityLabel(r.purity)}</span></td>
      <td>${r.query_count}</td>
      <td>${fmtAge(r.days_since_last_run)}</td>
      <td>${schedCell(r)}</td>
      <td class="muted">${esc(r.creator)}</td>
      <td>${r.is_archived}</td>
    </tr>`;
  }).join("");
}

function esc(s){ return String(s).replace(/[&<>"]/g, c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;"}[c])); }

document.querySelectorAll("th").forEach(th=>th.addEventListener("click",()=>{
  const k = th.dataset.k;
  if (sortKey === k) sortAsc = !sortAsc; else { sortKey = k; sortAsc = true; }
  render();
}));
["q","source","creator","purity","dead","sched","ageop","agerange"].forEach(id=>document.getElementById(id).addEventListener("input", render));
initFilters(); render();
</script>
</body>
</html>
"""
