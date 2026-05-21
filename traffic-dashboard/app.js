// Step 1: 先把 Chart.js 的折線圖空殼掛起來，後續步驟再餵資料。
const rpsCtx = document.getElementById("rps-chart").getContext("2d");

const rpsChart = new Chart(rpsCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [{
      label: "RPS",
      data: [],
      borderColor: "#4cc9f0",
      backgroundColor: "rgba(76, 201, 240, 0.15)",
      borderWidth: 2,
      tension: 0.3,
      fill: true,
      pointRadius: 0,
    }],
  },
  options: {
    responsive: true,
    animation: false,
    scales: {
      x: { ticks: { color: "#8a96b0" }, grid: { color: "rgba(255,255,255,0.05)" } },
      y: { beginAtZero: true, ticks: { color: "#8a96b0" }, grid: { color: "rgba(255,255,255,0.05)" } },
    },
    plugins: {
      legend: { labels: { color: "#e6ecf5" } },
    },
  },
});

console.log("Step 1 OK: Chart.js loaded, empty chart mounted.");
