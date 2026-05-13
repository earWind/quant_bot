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
  initialBalance: document.querySelector("#initialBalance"),
  backtestLimit: document.querySelector("#backtestLimit"),
  lastUpdate: document.querySelector("#lastUpdate"),
  nextCheck: document.querySelector("#nextCheck"),
  errorBox: document.querySelector("#errorBox"),
  logs: document.querySelector("#logs"),
  logCount: document.querySelector("#logCount"),
  startBtn: document.querySelector("#startBtn"),
  stopBtn: document.querySelector("#stopBtn"),
  runOnceBtn: document.querySelector("#runOnceBtn"),
  backtestBtn: document.querySelector("#backtestBtn"),
  settingsForm: document.querySelector("#settingsForm"),
  settingsStatus: document.querySelector("#settingsStatus"),
  saveBacktestBtn: document.querySelector("#saveBacktestBtn"),
  symbolInput: document.querySelector("#symbolInput"),
  timeframeInput: document.querySelector("#timeframeInput"),
  shortMaInput: document.querySelector("#shortMaInput"),
  longMaInput: document.querySelector("#longMaInput"),
  shortMaRange: document.querySelector("#shortMaRange"),
  longMaRange: document.querySelector("#longMaRange"),
  shortMaRangeValue: document.querySelector("#shortMaRangeValue"),
  longMaRangeValue: document.querySelector("#longMaRangeValue"),
  shortMaBuyLabel: document.querySelector("#shortMaBuyLabel"),
  longMaBuyLabel: document.querySelector("#longMaBuyLabel"),
  shortMaSellLabel: document.querySelector("#shortMaSellLabel"),
  longMaSellLabel: document.querySelector("#longMaSellLabel"),
  buyOperatorLabel: document.querySelector("#buyOperatorLabel"),
  sellOperatorLabel: document.querySelector("#sellOperatorLabel"),
  buyConditionInput: document.querySelector("#buyConditionInput"),
  sellConditionInput: document.querySelector("#sellConditionInput"),
  riskPercentInput: document.querySelector("#riskPercentInput"),
  initialBalanceInput: document.querySelector("#initialBalanceInput"),
  backtestLimitInput: document.querySelector("#backtestLimitInput"),
  backtestStatus: document.querySelector("#backtestStatus"),
  btEquity: document.querySelector("#btEquity"),
  btReturn: document.querySelector("#btReturn"),
  btBuyHold: document.querySelector("#btBuyHold"),
  btDrawdown: document.querySelector("#btDrawdown"),
  btTrades: document.querySelector("#btTrades"),
  btOpen: document.querySelector("#btOpen"),
  btTradeList: document.querySelector("#btTradeList"),
};

let formInitialized = false;

function syncStrategyPreview() {
  const shortMa = Number(els.shortMaInput.value || 0);
  const longMa = Number(els.longMaInput.value || 0);
  const shortLabel = `MA${shortMa || "--"}`;
  const longLabel = `MA${longMa || "--"}`;
  const buyOperator = els.buyConditionInput.value === "above" ? "高于" : "低于";
  const sellOperator = els.sellConditionInput.value === "above" ? "高于" : "低于";

  els.shortMaRange.value = Math.min(Math.max(shortMa || 1, 1), 100);
  els.longMaRange.value = Math.min(Math.max(longMa || 2, 2), 200);
  els.shortMaRangeValue.textContent = shortMa || "--";
  els.longMaRangeValue.textContent = longMa || "--";
  els.shortMaBuyLabel.textContent = shortLabel;
  els.longMaBuyLabel.textContent = longLabel;
  els.shortMaSellLabel.textContent = shortLabel;
  els.longMaSellLabel.textContent = longLabel;
  els.buyOperatorLabel.textContent = buyOperator;
  els.sellOperatorLabel.textContent = sellOperator;
}

function formatNumber(value, digits = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return Number(value).toLocaleString("en-US", {
    maximumFractionDigits: digits,
  });
}

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${formatNumber(value, 2)}%`;
}

function fillSettingsForm(state) {
  els.symbolInput.value = state.symbol;
  els.timeframeInput.value = state.timeframe;
  els.shortMaInput.value = state.short_ma;
  els.longMaInput.value = state.long_ma;
  els.buyConditionInput.value = state.buy_condition;
  els.sellConditionInput.value = state.sell_condition;
  els.riskPercentInput.value = state.risk_percent;
  els.initialBalanceInput.value = state.initial_balance;
  els.backtestLimitInput.value = state.backtest_limit;
  syncStrategyPreview();
}

function readSettingsForm() {
  return {
    symbol: els.symbolInput.value.trim().toUpperCase(),
    timeframe: els.timeframeInput.value,
    short_ma: Number(els.shortMaInput.value),
    long_ma: Number(els.longMaInput.value),
    buy_condition: els.buyConditionInput.value,
    sell_condition: els.sellConditionInput.value,
    risk_percent: Number(els.riskPercentInput.value),
    initial_balance: Number(els.initialBalanceInput.value),
    backtest_limit: Number(els.backtestLimitInput.value),
  };
}

function validateSettings(values) {
  if (!values.symbol.includes("/")) {
    throw new Error("交易对格式应类似 BTC/USDT");
  }
  if (values.short_ma >= values.long_ma) {
    throw new Error("短均线必须小于长均线");
  }
  if (values.buy_condition === values.sell_condition) {
    throw new Error("买入条件和卖出条件不能相同");
  }
}

function render(payload) {
  const state = payload.state;
  const logs = payload.logs || [];

  if (!formInitialized) {
    fillSettingsForm(state);
    formInitialized = true;
  }

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
  els.riskPercent.textContent = formatPercent(state.risk_percent * 100);
  els.initialBalance.textContent = `$${formatNumber(state.initial_balance, 2)}`;
  els.backtestLimit.textContent = state.backtest_limit;
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

function renderBacktest(result) {
  els.backtestStatus.textContent = "已更新";
  els.btEquity.textContent = `$${formatNumber(result.final_equity, 2)}`;
  els.btReturn.textContent = formatPercent(result.return_pct);
  els.btBuyHold.textContent = formatPercent(result.buy_hold_pct);
  els.btDrawdown.textContent = formatPercent(result.max_drawdown_pct);
  els.btTrades.textContent = result.trade_count;
  els.btOpen.textContent = result.position_open ? "持仓中" : "空仓";

  if (!result.trades.length) {
    els.btTradeList.innerHTML = "<p class=\"empty\">暂无交易记录</p>";
    return;
  }

  els.btTradeList.innerHTML = result.trades.map((trade) => `
    <div class="trade-row ${trade.side.toLowerCase()}">
      <span>${trade.side}</span>
      <span>$${formatNumber(trade.price, 2)}</span>
      <span>${formatNumber(trade.amount, 8)}</span>
      <span>$${formatNumber(trade.equity, 2)}</span>
    </div>
  `).join("");
}

async function request(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  render(payload);
  return payload;
}

async function saveSettings() {
  const values = readSettingsForm();
  validateSettings(values);
  els.settingsStatus.textContent = "保存中...";
  const payload = await request("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(values),
  });

  if (!payload.ok) {
    throw new Error(payload.error || "参数保存失败");
  }

  fillSettingsForm(payload.state);
  els.settingsStatus.textContent = "已保存";
  return payload;
}

async function refresh() {
  await request("/api/status");
}

async function runBacktest() {
  els.backtestStatus.textContent = "运行中...";
  const response = await fetch("/api/backtest", { method: "POST" });
  const payload = await response.json();

  if (payload.ok) {
    renderBacktest(payload.backtest);
  } else {
    els.backtestStatus.textContent = "失败";
    els.errorBox.textContent = payload.error || "回测失败";
  }
}

els.settingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await saveSettings();
  } catch (error) {
    els.settingsStatus.textContent = "保存失败";
    els.errorBox.textContent = error.message;
  }
});

els.settingsForm.addEventListener("input", () => {
  els.settingsStatus.textContent = "有未保存修改";
  syncStrategyPreview();
});

els.shortMaRange.addEventListener("input", () => {
  els.shortMaInput.value = els.shortMaRange.value;
  els.settingsStatus.textContent = "有未保存修改";
  syncStrategyPreview();
});

els.longMaRange.addEventListener("input", () => {
  els.longMaInput.value = els.longMaRange.value;
  els.settingsStatus.textContent = "有未保存修改";
  syncStrategyPreview();
});

els.saveBacktestBtn.addEventListener("click", async () => {
  try {
    await saveSettings();
    await runBacktest();
  } catch (error) {
    els.settingsStatus.textContent = "保存失败";
    els.errorBox.textContent = error.message;
  }
});

els.startBtn.addEventListener("click", () => {
  request("/api/start", { method: "POST" });
});

els.stopBtn.addEventListener("click", () => {
  request("/api/stop", { method: "POST" });
});

els.runOnceBtn.addEventListener("click", () => {
  request("/api/run-once", { method: "POST" });
});

els.backtestBtn.addEventListener("click", runBacktest);

refresh();
setInterval(refresh, 3000);
