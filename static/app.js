const els = {
  runningStatus: document.querySelector("#runningStatus"),
  symbol: document.querySelector("#symbol"),
  price: document.querySelector("#price"),
  signal: document.querySelector("#signal"),
  amount: document.querySelector("#amount"),
  testMode: document.querySelector("#testMode"),
  timeframe: document.querySelector("#timeframe"),
  shortMa: document.querySelector("#shortMa"),
  longMa: document.querySelector("#longMa"),
  riskPercent: document.querySelector("#riskPercent"),
  lastUpdate: document.querySelector("#lastUpdate"),
  nextCheck: document.querySelector("#nextCheck"),
  errorBox: document.querySelector("#errorBox"),
  logs: document.querySelector("#logs"),
  logCount: document.querySelector("#logCount"),
  startBtn: document.querySelector("#startBtn"),
  stopBtn: document.querySelector("#stopBtn"),
  runOnceBtn: document.querySelector("#runOnceBtn"),
};

function formatNumber(value, digits = 6) {
  if (value === null || value === undefined) {
    return "--";
  }
  return Number(value).toLocaleString("en-US", {
    maximumFractionDigits: digits,
  });
}

function render(payload) {
  const state = payload.state;
  const logs = payload.logs || [];

  els.runningStatus.textContent = state.running ? "运行中" : "已停止";
  els.runningStatus.classList.toggle("on", state.running);
  els.runningStatus.classList.toggle("off", !state.running);

  els.symbol.textContent = state.symbol;
  els.price.textContent = formatNumber(state.price, 2);
  els.signal.textContent = state.signal || "--";
  els.signal.className = "";
  els.signal.classList.add(String(state.signal).toLowerCase());
  els.amount.textContent = formatNumber(state.amount, 8);
  els.testMode.textContent = state.test_mode ? "测试模式" : "实盘模式";
  els.timeframe.textContent = state.timeframe;
  els.shortMa.textContent = state.short_ma;
  els.longMa.textContent = state.long_ma;
  els.riskPercent.textContent = `${formatNumber(state.risk_percent * 100, 2)}%`;
  els.lastUpdate.textContent = state.last_update || "--";
  els.nextCheck.textContent = state.running ? `${state.next_check_seconds}s` : "--";
  els.errorBox.textContent = state.error || "";
  els.logCount.textContent = `${logs.length} 条`;

  els.logs.innerHTML = logs.map((item) => `
    <div class="log-row">
      <span>${item.time}</span>
      <span class="log-level ${item.level}">${item.level}</span>
      <span class="log-message">${item.message}</span>
    </div>
  `).join("");
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  render(payload);
  return payload;
}

async function refresh() {
  await request("/api/status");
}

els.startBtn.addEventListener("click", () => {
  request("/api/start", { method: "POST" });
});

els.stopBtn.addEventListener("click", () => {
  request("/api/stop", { method: "POST" });
});

els.runOnceBtn.addEventListener("click", () => {
  request("/api/run-once", { method: "POST" });
});

refresh();
setInterval(refresh, 3000);
