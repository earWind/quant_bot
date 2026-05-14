const els = {
  runningStatus: document.querySelector("#runningStatus"),
  symbol: document.querySelector("#symbol"),
  price: document.querySelector("#price"),
  signal: document.querySelector("#signal"),
  amount: document.querySelector("#amount"),
  testMode: document.querySelector("#testMode"),
  strategyType: document.querySelector("#strategyType"),
  marketType: document.querySelector("#marketType"),
  timeframe: document.querySelector("#timeframe"),
  shortMa: document.querySelector("#shortMa"),
  longMa: document.querySelector("#longMa"),
  riskPercent: document.querySelector("#riskPercent"),
  initialBalance: document.querySelector("#initialBalance"),
  feeRate: document.querySelector("#feeRate"),
  backtestLimit: document.querySelector("#backtestLimit"),
  backtestDataSource: document.querySelector("#backtestDataSource"),
  cacheInfo: document.querySelector("#cacheInfo"),
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
  activeStrategyRule: document.querySelector("#activeStrategyRule"),
  saveBacktestBtn: document.querySelector("#saveBacktestBtn"),
  symbolInput: document.querySelector("#symbolInput"),
  strategyTypeInput: document.querySelector("#strategyTypeInput"),
  marketTypeInput: document.querySelector("#marketTypeInput"),
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
  feeRateInput: document.querySelector("#feeRateInput"),
  backtestLimitInput: document.querySelector("#backtestLimitInput"),
  backtestDataSourceInput: document.querySelector("#backtestDataSourceInput"),
  backtestStatus: document.querySelector("#backtestStatus"),
  btEquity: document.querySelector("#btEquity"),
  btReturn: document.querySelector("#btReturn"),
  btBuyHold: document.querySelector("#btBuyHold"),
  btDrawdown: document.querySelector("#btDrawdown"),
  btFees: document.querySelector("#btFees"),
  btTrades: document.querySelector("#btTrades"),
  btOpen: document.querySelector("#btOpen"),
  backtestChart: document.querySelector("#backtestChart"),
  chartZoomInput: document.querySelector("#chartZoomInput"),
  chartPanInput: document.querySelector("#chartPanInput"),
  chartZoomValue: document.querySelector("#chartZoomValue"),
  chartPanValue: document.querySelector("#chartPanValue"),
  btTradeList: document.querySelector("#btTradeList"),
};

let formInitialized = false;
let latestChart = null;
let chartDrag = null;

function getConditionText(condition) {
  return condition === "above" ? "高于" : "低于";
}

function describeStrategy(values) {
  const timeframe = values.timeframe || "--";
  const shortMa = values.short_ma || "--";
  const longMa = values.long_ma || "--";
  const marketName = values.market_type === "swap" ? "合约" : "现货";

  if (values.strategy_type === "ma_turn") {
    return `${marketName} / ${values.symbol} / ${timeframe} / 趋势交易：价格 > MA5 > MA10 > MA20 且 MA20 上行买入；价格跌破 MA20 或 MA5 跌破 MA10 卖出`;
  }
  if (values.strategy_type === "ma_reversion") {
    return `${marketName} / ${values.symbol} / ${timeframe} / 回归均线：MA5 > MA10 > MA20，上一根 K 线跌幅 >= 0.5% 且收盘价低于 MA5 买入；持有到下一根 K 线结束或再次跌超 0.5% 卖出`;
  }
  if (values.strategy_type === "martingale") {
    return `${marketName} / ${values.symbol} / ${timeframe} / 马丁格尔：单根 K 线跌幅 >= 0.5% 首买；每下跌 1% 按 2 倍加仓，最多 5 档；均价上方 0.8% 止盈`;
  }

  return `${marketName} / ${values.symbol} / ${timeframe} / MA${shortMa} ${getConditionText(values.buy_condition)} MA${longMa} 买入，MA${shortMa} ${getConditionText(values.sell_condition)} MA${longMa} 卖出`;
}

function syncActiveStrategyRule(values = readSettingsForm()) {
  els.activeStrategyRule.textContent = describeStrategy(values);
}

function syncStrategyPreview() {
  const strategyType = els.strategyTypeInput.value;
  const shortMa = Number(els.shortMaInput.value || 0);
  const longMa = Number(els.longMaInput.value || 0);
  const shortLabel = `MA${shortMa || "--"}`;
  const longLabel = `MA${longMa || "--"}`;
  const customPreview = {
    ma_turn: ["价格 > MA5 > MA10 > 且 MA20 上行", "价格跌破 MA20 或 MA5 跌破 MA10"],
    ma_reversion: ["MA5 > MA10 > MA20，上一根 K 线跌幅 >= 0.5% 且收盘价 < MA5", "持有到下一根 K 线结束或再次跌超 0.5%"],
    martingale: ["单根 K 线跌幅 >= 0.5% 首买；每跌 1% 加仓", "均价上方 0.8% 止盈"],
  };
  const usesCustomPreview = Boolean(customPreview[strategyType]);

  els.shortMaRange.value = Math.min(Math.max(shortMa || 1, 1), 100);
  els.longMaRange.value = Math.min(Math.max(longMa || 2, 2), 200);
  els.shortMaRangeValue.textContent = shortMa || "--";
  els.longMaRangeValue.textContent = longMa || "--";
  els.shortMaBuyLabel.textContent = usesCustomPreview ? "" : shortLabel;
  els.longMaBuyLabel.textContent = usesCustomPreview ? "" : longLabel;
  els.shortMaSellLabel.textContent = usesCustomPreview ? "" : shortLabel;
  els.longMaSellLabel.textContent = usesCustomPreview ? "" : longLabel;
  els.buyOperatorLabel.textContent = usesCustomPreview
    ? customPreview[strategyType][0]
    : (els.buyConditionInput.value === "above" ? "高于" : "低于");
  els.sellOperatorLabel.textContent = usesCustomPreview
    ? customPreview[strategyType][1]
    : (els.sellConditionInput.value === "above" ? "高于" : "低于");
  syncActiveStrategyRule();
}

function formatNumber(value, digits = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return Number(value).toLocaleString("en-US", { maximumFractionDigits: digits });
}

function formatPercent(value) {
  if (value === null || value === undefined) {
    return "--";
  }
  return `${formatNumber(value, 2)}%`;
}

function getVisibleChart(chart) {
  const candles = chart?.candles || [];
  if (!candles.length) {
    return { candles: [], markers: [] };
  }

  const requestedWindow = Number(els.chartZoomInput.value || 240);
  const windowSize = Math.min(Math.max(requestedWindow, 50), candles.length);
  const maxStart = Math.max(0, candles.length - windowSize);
  const start = Math.min(Number(els.chartPanInput.value || maxStart), maxStart);
  const end = start + windowSize;

  els.chartZoomInput.max = String(Math.max(50, candles.length));
  els.chartZoomInput.value = String(windowSize);
  els.chartPanInput.max = String(maxStart);
  els.chartPanInput.value = String(start);
  els.chartZoomValue.textContent = String(windowSize);
  els.chartPanValue.textContent = start === maxStart ? "最新" : `${start + 1}-${end}`;

  return {
    candles: candles.slice(start, end),
    markers: (chart.markers || [])
      .filter((marker) => marker.index >= start && marker.index < end)
      .map((marker) => ({ ...marker, index: marker.index - start })),
  };
}

function clampChartStart(start, windowSize, total) {
  return Math.min(Math.max(0, start), Math.max(0, total - windowSize));
}

function setChartView(windowSize, start) {
  if (!latestChart?.candles?.length) {
    return;
  }
  const total = latestChart.candles.length;
  const nextWindow = Math.min(Math.max(Math.round(windowSize), 50), total);
  const nextStart = clampChartStart(Math.round(start), nextWindow, total);
  els.chartZoomInput.max = String(Math.max(50, total));
  els.chartZoomInput.value = String(nextWindow);
  els.chartPanInput.max = String(Math.max(0, total - nextWindow));
  els.chartPanInput.value = String(nextStart);
  drawBacktestChart(latestChart);
}

function handleChartWheel(event) {
  if (!latestChart?.candles?.length) {
    return;
  }
  event.preventDefault();
  const total = latestChart.candles.length;
  const rect = els.backtestChart.getBoundingClientRect();
  const currentWindow = Number(els.chartZoomInput.value || 240);
  const currentStart = Number(els.chartPanInput.value || 0);
  const cursorRatio = Math.min(Math.max((event.clientX - rect.left) / rect.width, 0), 1);
  const focalIndex = currentStart + currentWindow * cursorRatio;
  const zoomFactor = event.deltaY < 0 ? 0.82 : 1.22;
  const nextWindow = Math.min(Math.max(currentWindow * zoomFactor, 50), total);
  const nextStart = focalIndex - nextWindow * cursorRatio;
  setChartView(nextWindow, nextStart);
}

function handleChartPointerDown(event) {
  if (!latestChart?.candles?.length) {
    return;
  }
  els.backtestChart.setPointerCapture(event.pointerId);
  chartDrag = {
    pointerId: event.pointerId,
    startX: event.clientX,
    startPan: Number(els.chartPanInput.value || 0),
    windowSize: Number(els.chartZoomInput.value || 240),
    total: latestChart.candles.length,
  };
  els.backtestChart.classList.add("dragging");
}

function handleChartPointerMove(event) {
  if (!chartDrag || chartDrag.pointerId !== event.pointerId) {
    return;
  }
  const rect = els.backtestChart.getBoundingClientRect();
  const plotWidth = Math.max(1, rect.width - 10 - 58);
  const candlesPerPixel = chartDrag.windowSize / plotWidth;
  const nextStart = chartDrag.startPan - (event.clientX - chartDrag.startX) * candlesPerPixel;
  setChartView(chartDrag.windowSize, nextStart);
}

function endChartDrag(event) {
  if (!chartDrag || chartDrag.pointerId !== event.pointerId) {
    return;
  }
  chartDrag = null;
  els.backtestChart.classList.remove("dragging");
}

function drawBacktestChart(chart) {
  const canvas = els.backtestChart;
  if (!canvas || !chart?.candles?.length) {
    return;
  }
  const visibleChart = getVisibleChart(chart);
  if (!visibleChart.candles.length) {
    return;
  }

  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  const cssWidth = Math.max(rect.width, 320);
  const cssHeight = 360;
  canvas.width = Math.floor(cssWidth * ratio);
  canvas.height = Math.floor(cssHeight * ratio);
  canvas.style.height = `${cssHeight}px`;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, cssWidth, cssHeight);

  const padding = { top: 18, right: 58, bottom: 28, left: 10 };
  const plotWidth = cssWidth - padding.left - padding.right;
  const plotHeight = cssHeight - padding.top - padding.bottom;
  const candles = visibleChart.candles;
  const prices = candles.flatMap((c) => [c.high, c.low, c.ma5, c.ma10, c.ma20]).filter((v) => v !== null);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const priceRange = maxPrice - minPrice || 1;
  const step = plotWidth / candles.length;
  const bodyWidth = Math.max(2, Math.min(9, step * 0.58));
  const yFor = (price) => padding.top + ((maxPrice - price) / priceRange) * plotHeight;
  const xFor = (index) => padding.left + step * index + step / 2;

  ctx.strokeStyle = "#d8e1e8";
  ctx.lineWidth = 1;
  ctx.font = "12px Segoe UI, Microsoft YaHei, Arial";
  ctx.fillStyle = "#667481";
  for (let i = 0; i <= 4; i += 1) {
    const y = padding.top + (plotHeight / 4) * i;
    const price = maxPrice - (priceRange / 4) * i;
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(cssWidth - padding.right, y);
    ctx.stroke();
    ctx.fillText(formatNumber(price, 2), cssWidth - padding.right + 8, y + 4);
  }

  candles.forEach((candle, index) => {
    const x = xFor(index);
    const openY = yFor(candle.open);
    const closeY = yFor(candle.close);
    const rising = candle.close >= candle.open;
    ctx.strokeStyle = rising ? "#18794e" : "#c24130";
    ctx.fillStyle = rising ? "rgba(24, 121, 78, 0.76)" : "rgba(194, 65, 48, 0.76)";
    ctx.beginPath();
    ctx.moveTo(x, yFor(candle.high));
    ctx.lineTo(x, yFor(candle.low));
    ctx.stroke();
    ctx.fillRect(x - bodyWidth / 2, Math.min(openY, closeY), bodyWidth, Math.max(1, Math.abs(openY - closeY)));
  });

  [
    { key: "ma5", color: "#2563eb" },
    { key: "ma10", color: "#a15c00" },
    { key: "ma20", color: "#0b6f75" },
  ].forEach((line) => {
    ctx.strokeStyle = line.color;
    ctx.lineWidth = line.key === "ma20" ? 2.2 : 1.6;
    ctx.beginPath();
    let started = false;
    candles.forEach((candle, index) => {
      const value = candle[line.key];
      if (value === null) return;
      const x = xFor(index);
      const y = yFor(value);
      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();
  });

  (visibleChart.markers || []).forEach((marker) => {
    if (marker.index < 0 || marker.index >= candles.length) return;
    const x = xFor(marker.index);
    const y = yFor(marker.price);
    const isBuy = marker.side === "BUY";
    ctx.fillStyle = isBuy ? "#18794e" : "#c24130";
    ctx.beginPath();
    if (isBuy) {
      ctx.moveTo(x, y - 14);
      ctx.lineTo(x - 7, y - 2);
      ctx.lineTo(x + 7, y - 2);
    } else {
      ctx.moveTo(x, y + 14);
      ctx.lineTo(x - 7, y + 2);
      ctx.lineTo(x + 7, y + 2);
    }
    ctx.closePath();
    ctx.fill();
    ctx.font = "11px Segoe UI, Microsoft YaHei, Arial";
    ctx.fillText(marker.side, x + 8, isBuy ? y - 5 : y + 14);
  });
}

function fillSettingsForm(state) {
  els.symbolInput.value = state.symbol;
  els.strategyTypeInput.value = state.strategy_type || "ma_turn";
  els.marketTypeInput.value = state.market_type || "spot";
  els.timeframeInput.value = state.timeframe;
  els.shortMaInput.value = state.short_ma;
  els.longMaInput.value = state.long_ma;
  els.buyConditionInput.value = state.buy_condition;
  els.sellConditionInput.value = state.sell_condition;
  els.riskPercentInput.value = state.risk_percent;
  els.initialBalanceInput.value = state.initial_balance;
  els.feeRateInput.value = state.fee_rate;
  els.backtestLimitInput.value = state.backtest_limit;
  els.backtestDataSourceInput.value = state.backtest_data_source || "fetch";
  syncStrategyPreview();
  syncActiveStrategyRule(readSettingsForm());
}

function readSettingsForm() {
  return {
    symbol: els.symbolInput.value.trim().toUpperCase(),
    strategy_type: els.strategyTypeInput.value,
    market_type: els.marketTypeInput.value,
    timeframe: els.timeframeInput.value,
    short_ma: Number(els.shortMaInput.value),
    long_ma: Number(els.longMaInput.value),
    buy_condition: els.buyConditionInput.value,
    sell_condition: els.sellConditionInput.value,
    risk_percent: Number(els.riskPercentInput.value),
    initial_balance: Number(els.initialBalanceInput.value),
    fee_rate: Number(els.feeRateInput.value),
    backtest_limit: Number(els.backtestLimitInput.value),
    backtest_data_source: els.backtestDataSourceInput.value,
  };
}

function validateSettings(values) {
  if (!values.symbol.includes("/")) throw new Error("交易对格式应类似 BTC/USDT");
  if (values.strategy_type === "ma_cross" && values.short_ma >= values.long_ma) {
    throw new Error("短均线必须小于长均线");
  }
  if (values.strategy_type === "ma_cross" && values.buy_condition === values.sell_condition) {
    throw new Error("买入条件和卖出条件不能相同");
  }
}

function render(payload) {
  const state = payload.state;
  const logs = payload.logs || [];
  const strategyNames = {
    ma_turn: "趋势交易",
    ma_reversion: "回归均线",
    martingale: "马丁格尔",
    ma_cross: "双均线位置",
  };
  const dataSourceNames = { local: "使用本地数据", fetch: "拉取最新并保存" };
  const marketTypeNames = { spot: "现货", swap: "合约" };

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
  els.strategyType.textContent = strategyNames[state.strategy_type] || state.strategy_type || "--";
  els.marketType.textContent = marketTypeNames[state.market_type] || state.market_type || "--";
  els.activeStrategyRule.textContent = describeStrategy(state);
  els.timeframe.textContent = state.timeframe;
  els.shortMa.textContent = state.short_ma;
  els.longMa.textContent = state.long_ma;
  els.riskPercent.textContent = formatPercent(state.risk_percent * 100);
  els.initialBalance.textContent = `$${formatNumber(state.initial_balance, 2)}`;
  els.feeRate.textContent = formatPercent(state.fee_rate * 100);
  els.backtestLimit.textContent = state.backtest_limit;
  els.backtestDataSource.textContent = dataSourceNames[state.backtest_data_source] || "--";
  els.cacheInfo.textContent = state.cache_info?.exists ? `${formatNumber(state.cache_info.count, 0)} 条` : "暂无缓存";
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
  els.btFees.textContent = `$${formatNumber(result.total_fees, 2)}`;
  els.btTrades.textContent = result.trade_count;
  els.btOpen.textContent = result.position_open ? "持仓中" : "空仓";
  latestChart = result.chart;
  if (latestChart?.candles?.length) {
    const defaultWindow = Math.min(240, latestChart.candles.length);
    els.chartZoomInput.max = String(Math.max(50, latestChart.candles.length));
    els.chartZoomInput.value = String(defaultWindow);
    els.chartPanInput.value = String(Math.max(0, latestChart.candles.length - defaultWindow));
  }
  drawBacktestChart(latestChart);
  if (!result.trades.length) {
    els.btTradeList.innerHTML = "<p class=\"empty\">暂无交易记录</p>";
    return;
  }
  els.btTradeList.innerHTML = result.trades.map((trade) => `
    <div class="trade-row ${trade.side.toLowerCase()}">
      <span>${trade.side}</span>
      <span>$${formatNumber(trade.price, 2)}</span>
      <span>${formatNumber(trade.amount, 8)}</span>
      <span>$${formatNumber(trade.fee, 4)}</span>
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
  if (!payload.ok) throw new Error(payload.error || "参数保存失败");
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
    render(payload);
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

els.chartZoomInput.addEventListener("input", () => {
  if (!latestChart?.candles?.length) return;
  const windowSize = Number(els.chartZoomInput.value);
  els.chartPanInput.value = String(Math.max(0, latestChart.candles.length - windowSize));
  drawBacktestChart(latestChart);
});
els.chartPanInput.addEventListener("input", () => latestChart?.candles?.length && drawBacktestChart(latestChart));
els.backtestChart.addEventListener("wheel", handleChartWheel, { passive: false });
els.backtestChart.addEventListener("pointerdown", handleChartPointerDown);
els.backtestChart.addEventListener("pointermove", handleChartPointerMove);
els.backtestChart.addEventListener("pointerup", endChartDrag);
els.backtestChart.addEventListener("pointercancel", endChartDrag);

els.saveBacktestBtn.addEventListener("click", async () => {
  try {
    await saveSettings();
    await runBacktest();
  } catch (error) {
    els.settingsStatus.textContent = "保存失败";
    els.errorBox.textContent = error.message;
  }
});
els.startBtn.addEventListener("click", () => request("/api/start", { method: "POST" }));
els.stopBtn.addEventListener("click", () => request("/api/stop", { method: "POST" }));
els.runOnceBtn.addEventListener("click", () => request("/api/run-once", { method: "POST" }));
els.backtestBtn.addEventListener("click", async () => {
  try {
    await saveSettings();
    await runBacktest();
  } catch (error) {
    els.settingsStatus.textContent = "保存失败";
    els.errorBox.textContent = error.message;
  }
});

refresh();
setInterval(refresh, 3000);
