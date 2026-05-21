// ---------- Step 2: 模擬流量產生器 ----------
// 每 1 秒產生一批 API 請求事件，可被後續步驟訂閱使用。

const ENDPOINTS = [
  { path: "/api/login",    weight: 3 },
  { path: "/api/users",    weight: 5 },
  { path: "/api/orders",   weight: 4 },
  { path: "/api/products", weight: 6 },
  { path: "/api/checkout", weight: 2 },
  { path: "/api/search",   weight: 5 },
  { path: "/api/health",   weight: 8 },
];

const METHODS = ["GET", "GET", "GET", "POST", "POST", "PUT", "DELETE"];

// 大多回 200，少量錯誤碼；用於後續錯誤率統計
const STATUS_POOL = [
  ...Array(85).fill(200),
  ...Array(5).fill(201),
  ...Array(3).fill(304),
  ...Array(3).fill(400),
  ...Array(2).fill(401),
  ...Array(1).fill(404),
  ...Array(1).fill(500),
];

function weightedPick(items) {
  const total = items.reduce((s, it) => s + it.weight, 0);
  let r = Math.random() * total;
  for (const it of items) {
    r -= it.weight;
    if (r <= 0) return it;
  }
  return items[items.length - 1];
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randomClientIp() {
  return `${rndOctet()}.${rndOctet()}.${rndOctet()}.${rndOctet()}`;
}
function rndOctet() { return Math.floor(Math.random() * 255) + 1; }

function generateEvent() {
  const status = pick(STATUS_POOL);
  // 錯誤回應通常比較久
  const baseLatency = status >= 500 ? 400 : status >= 400 ? 120 : 40;
  const latencyMs = Math.round(baseLatency + Math.random() * 180);
  return {
    ts: Date.now(),
    method: pick(METHODS),
    path: weightedPick(ENDPOINTS).path,
    status,
    latencyMs,
    clientIp: randomClientIp(),
  };
}

// 訂閱機制：後續圖表、KPI、表格都會經由這裡拿事件
const subscribers = [];
function onTraffic(fn) { subscribers.push(fn); }

function tick() {
  // 每秒 5~50 個事件，偶爾爆衝（讓後面異常偵測有東西可顯示）
  const spike = Math.random() < 0.05;
  const n = spike ? 80 + Math.floor(Math.random() * 60)
                  : 5 + Math.floor(Math.random() * 45);
  const events = [];
  for (let i = 0; i < n; i++) events.push(generateEvent());
  subscribers.forEach((fn) => fn(events));
}

setInterval(tick, 1000);

// ---------- Step 1: Chart.js 空殼折線圖 ----------
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

// ---------- Step 2 驗證：把每秒事件數印到 console ----------
onTraffic((events) => {
  console.log(`[traffic] +${events.length} events, sample:`, events[0]);
});

console.log("Step 2 OK: traffic generator running, see console for events.");
