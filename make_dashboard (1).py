import json
from pathlib import Path

data = json.loads(Path('reports/dashboard_data.json').read_text(encoding='utf-8'))

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Patent Intelligence Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; background: #f5f5f0; color: #1a1a1a; padding: 2rem; }
h1 { font-size: 22px; font-weight: 500; margin-bottom: 0.25rem; }
.subtitle { font-size: 13px; color: #888; margin-bottom: 2rem; }
.metrics { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 1.5rem; }
.metric { background: #fff; border-radius: 10px; padding: 16px 18px; border: 0.5px solid #e0e0d8; }
.metric-label { font-size: 12px; color: #888; margin-bottom: 6px; }
.metric-value { font-size: 24px; font-weight: 500; }
.metric-sub { font-size: 12px; color: #aaa; margin-top: 2px; }
.chart-card { background: #fff; border-radius: 12px; border: 0.5px solid #e0e0d8; padding: 1.25rem; margin-bottom: 1.25rem; }
.chart-title { font-size: 14px; font-weight: 500; margin-bottom: 16px; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 1.25rem; }
.tab-bar { display: flex; gap: 4px; margin-bottom: 16px; }
.tab { font-size: 12px; padding: 5px 12px; border-radius: 8px; border: 0.5px solid #ddd; background: transparent; color: #666; cursor: pointer; }
.tab.active { background: #f0f0ea; color: #1a1a1a; font-weight: 500; }
.legend { display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 10px; font-size: 12px; color: #666; }
.legend span { display: flex; align-items: center; gap: 5px; }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; flex-shrink: 0; }
@media (max-width: 700px) { .metrics { grid-template-columns: 1fr 1fr; } .grid-2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>

<h1>Global Patent Intelligence Dashboard</h1>
<p class="subtitle">9.45 million patents &middot; 1976 &ndash; 2025 &middot; PatentsView data</p>

<div class="metrics">
  <div class="metric"><div class="metric-label">Total patents</div><div class="metric-value">9.45M</div><div class="metric-sub">1976 &ndash; 2025</div></div>
  <div class="metric"><div class="metric-label">Unique inventors</div><div class="metric-value">4.29M</div><div class="metric-sub">disambiguated</div></div>
  <div class="metric"><div class="metric-label">Companies</div><div class="metric-value">565K</div><div class="metric-sub">assignees</div></div>
  <div class="metric"><div class="metric-label">Peak year</div><div class="metric-value">2025</div><div class="metric-sub">378,741 patents</div></div>
</div>

<div class="chart-card">
  <div class="chart-title">Annual patent filings &amp; cumulative total (1976 &ndash; 2025)</div>
  <div class="tab-bar">
    <button class="tab active" onclick="showTrend('filed',this)">Annual filings</button>
    <button class="tab" onclick="showTrend('cumul',this)">Cumulative</button>
  </div>
  <div style="position:relative;width:100%;height:260px;"><canvas id="trendChart"></canvas></div>
</div>

<div class="grid-2">
  <div class="chart-card">
    <div class="chart-title">Top 10 countries by inventor patents</div>
    <div style="position:relative;width:100%;height:320px;"><canvas id="countryChart"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">Patent type breakdown</div>
    <div class="legend" id="typeLegend"></div>
    <div style="position:relative;width:100%;height:260px;"><canvas id="typeChart"></canvas></div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Top 15 companies by patent count</div>
  <div style="position:relative;width:100%;height:420px;"><canvas id="compChart"></canvas></div>
</div>

<div class="grid-2">
  <div class="chart-card">
    <div class="chart-title">Top 15 inventors globally</div>
    <div style="position:relative;width:100%;height:420px;"><canvas id="invChart"></canvas></div>
  </div>
  <div class="chart-card">
    <div class="chart-title">Dominant countries by decade</div>
    <div style="position:relative;width:100%;height:420px;"><canvas id="decadeChart"></canvas></div>
  </div>
</div>

<div class="chart-card">
  <div class="chart-title">Patent type trends over time</div>
  <div class="legend">
    <span><span class="legend-dot" style="background:#378ADD"></span>Utility</span>
    <span><span class="legend-dot" style="background:#D85A30"></span>Design</span>
    <span><span class="legend-dot" style="background:#1D9E75"></span>Plant</span>
    <span><span class="legend-dot" style="background:#BA7517"></span>Reissue</span>
  </div>
  <div style="position:relative;width:100%;height:280px;"><canvas id="techChart"></canvas></div>
</div>

<div class="chart-card">
  <div class="chart-title">Average claims by patent type</div>
  <div style="position:relative;width:100%;height:220px;"><canvas id="claimsChart"></canvas></div>
</div>

<script>
const DATA = """ + json.dumps(data) + """;

const yearly = DATA.yearly;
const countries = DATA.countries.slice(0,10);
const typeData = DATA.types;
const techRaw = DATA.tech;
const decadeRaw = DATA.decades;
const claimsData = DATA.claims;

const companies = [
  {n:"IBM",v:4748},{n:"Samsung Display",v:4617},{n:"LG Electronics",v:1640},
  {n:"Canon",v:1584},{n:"Intel",v:1345},{n:"Qualcomm",v:1119},
  {n:"Microsoft",v:1100},{n:"Sony",v:1089},{n:"TSMC",v:1070},
  {n:"Apple",v:1049},{n:"Toyota",v:997},{n:"Yoder Brother",v:995},
  {n:"Google",v:989},{n:"Amazon",v:899},{n:"BOE Technology",v:860}
];

const inventors = DATA.inventors.slice(0,15);
const typeColors = ["#378ADD","#D85A30","#1D9E75","#BA7517","#888780"];
const decadeColors = {US:"#378ADD",JP:"#D85A30",DE:"#1D9E75",KR:"#BA7517",CN:"#7F77DD",GB:"#D4537E",FR:"#639922",NL:"#E24B4A"};

let trendChart;
function showTrend(mode, btn) {
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  btn.classList.add("active");
  if (!trendChart) return;
  const isCumul = mode === "cumul";
  trendChart.data.datasets[0].data = yearly.map(d => isCumul ? d.cumulative_total : d.patents_filed);
  trendChart.options.scales.y.ticks.callback = v => isCumul ? (v/1e6).toFixed(1)+"M" : (v/1e3).toFixed(0)+"K";
  trendChart.update();
}

trendChart = new Chart(document.getElementById("trendChart"), {
  type: "line",
  data: {
    labels: yearly.map(d => d.year),
    datasets: [{
      label: "Annual filings",
      data: yearly.map(d => d.patents_filed),
      borderColor: "#378ADD", backgroundColor: "rgba(55,138,221,0.08)",
      borderWidth: 2, pointRadius: 0, fill: true, tension: 0.3
    }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { maxTicksLimit: 10, color: "#888" }, grid: { display: false } },
      y: { ticks: { callback: v => (v/1e3).toFixed(0)+"K", color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } }
    }
  }
});

new Chart(document.getElementById("countryChart"), {
  type: "bar",
  data: {
    labels: countries.map(d => d.country + " (" + d.pct_share + "%)"),
    datasets: [{ label: "Patents", data: countries.map(d => d.patent_count), backgroundColor: "#378ADD", borderRadius: 3 }]
  },
  options: {
    indexAxis: "y", responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { callback: v => (v/1e3).toFixed(0)+"K", color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } },
      y: { ticks: { color: "#888", font: { size: 12 } }, grid: { display: false } }
    }
  }
});

const legendEl = document.getElementById("typeLegend");
typeData.forEach((d, i) => {
  legendEl.innerHTML += '<span><span class="legend-dot" style="background:' + typeColors[i] + '"></span>' + d.patent_type + ' ' + d.pct_share + '%</span>';
});
new Chart(document.getElementById("typeChart"), {
  type: "doughnut",
  data: {
    labels: typeData.map(d => d.patent_type),
    datasets: [{ data: typeData.map(d => d.patent_count), backgroundColor: typeColors, borderWidth: 2 }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    cutout: "60%"
  }
});

new Chart(document.getElementById("compChart"), {
  type: "bar",
  data: {
    labels: companies.map(d => d.n),
    datasets: [{ label: "Patents", data: companies.map(d => d.v), backgroundColor: "#7F77DD", borderRadius: 3 }]
  },
  options: {
    indexAxis: "y", responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { callback: v => v.toLocaleString(), color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } },
      y: { ticks: { color: "#888", font: { size: 12 } }, grid: { display: false } }
    }
  }
});

new Chart(document.getElementById("invChart"), {
  type: "bar",
  data: {
    labels: inventors.map(d => d.inventor_name + " (" + d.country + ")"),
    datasets: [{ label: "Patents", data: inventors.map(d => d.patent_count), backgroundColor: "#1D9E75", borderRadius: 3 }]
  },
  options: {
    indexAxis: "y", responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } },
      y: { ticks: { color: "#888", font: { size: 11 } }, grid: { display: false } }
    }
  }
});

const decades = [...new Set(decadeRaw.map(d => d.decade))];
const dCountries = [...new Set(decadeRaw.map(d => d.country))];
new Chart(document.getElementById("decadeChart"), {
  type: "bar",
  data: {
    labels: decades.map(d => d + "s"),
    datasets: dCountries.map(c => ({
      label: c,
      data: decades.map(dec => { const r = decadeRaw.find(d => d.decade === dec && d.country === c); return r ? r.patent_count : 0; }),
      backgroundColor: decadeColors[c] || "#888",
      borderRadius: 2
    }))
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { position: "bottom", labels: { font: { size: 11 }, boxWidth: 12, padding: 8 } } },
    scales: {
      x: { ticks: { color: "#888" }, grid: { display: false } },
      y: { ticks: { callback: v => (v/1e3).toFixed(0)+"K", color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } }
    }
  }
});

const techYears = [...new Set(techRaw.map(d => d.year))].sort();
const techTypes = ["utility","design","plant","reissue"];
const techColors = ["#378ADD","#D85A30","#1D9E75","#BA7517"];
new Chart(document.getElementById("techChart"), {
  type: "line",
  data: {
    labels: techYears,
    datasets: techTypes.map((t, i) => ({
      label: t,
      data: techYears.map(y => { const r = techRaw.find(d => d.year === y && d.patent_type === t); return r ? r.patent_count : 0; }),
      borderColor: techColors[i], backgroundColor: "transparent",
      borderWidth: 2, pointRadius: 3, tension: 0.3
    }))
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#888" }, grid: { display: false } },
      y: { ticks: { callback: v => (v/1e3).toFixed(0)+"K", color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } }
    }
  }
});

new Chart(document.getElementById("claimsChart"), {
  type: "bar",
  data: {
    labels: claimsData.map(d => d.patent_type),
    datasets: [{ label: "Avg claims", data: claimsData.map(d => d.avg_claims), backgroundColor: "#BA7517", borderRadius: 3 }]
  },
  options: {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#888" }, grid: { display: false } },
      y: { ticks: { color: "#888" }, grid: { color: "rgba(0,0,0,0.06)" } }
    }
  }
});
</script>
</body>
</html>"""

Path('reports/dashboard.html').write_text(html, encoding='utf-8')
print('Saved to reports/dashboard.html')