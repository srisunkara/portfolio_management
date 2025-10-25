import React from "react";
import { api } from "../../api/client.js";

function formatDate(d) {
  if (!d) return "";
  const dt = new Date(d);
  const yyyy = dt.getFullYear();
  const mm = String(dt.getMonth() + 1).padStart(2, "0");
  const dd = String(dt.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function defaultFromDateOneYear() {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 1);
  return formatDate(d);
}

const COLORS = [
  "#2563eb", // blue
  "#dc2626", // red
  "#16a34a", // green
  "#7c3aed", // purple
  "#f59e0b", // amber
  "#0ea5e9", // sky
  "#f97316", // orange
  "#10b981", // emerald
];

export default function SecurityPriceChange() {
  const [securities, setSecurities] = React.useState([]);
  const [ticker, setTicker] = React.useState(""); // primary ticker (kept for backward compat/metrics)
  const [extraInput, setExtraInput] = React.useState(""); // input for adding additional tickers
  const [extraTickers, setExtraTickers] = React.useState([]); // list of comparison tickers
  const [fromDate, setFromDate] = React.useState(defaultFromDateOneYear);
  const [toDate, setToDate] = React.useState(() => formatDate(new Date()));
  const [seriesByTicker, setSeriesByTicker] = React.useState({}); // { TICKER: [prices...] }
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [mode, setMode] = React.useState("price"); // 'price' | 'performance'

  // Load securities for dropdown
  React.useEffect(() => {
    api.listSecurities()
      .then((list) => setSecurities(list || []))
      .catch(() => {});
  }, []);

  const allSelectedTickers = React.useMemo(() => {
    const t0 = (ticker || "").trim().toUpperCase();
    const others = (extraTickers || []).map((t) => (t || "").trim().toUpperCase());
    const uniq = Array.from(new Set([...(t0 ? [t0] : []), ...others])).filter(Boolean);
    return uniq;
  }, [ticker, extraTickers]);

  const selectedSecurity = React.useMemo(() => {
    const t = ticker.trim().toUpperCase();
    if (!t) return null;
    return securities.find((s) => (s.ticker || "").trim().toUpperCase() === t) || null;
  }, [ticker, securities]);

  const validTicker = (t) => {
    if (!t) return false;
    const up = t.trim().toUpperCase();
    return securities.some((s) => (s.ticker || "").trim().toUpperCase() === up);
  };

  const addExtraTicker = () => {
    const t = extraInput.trim().toUpperCase();
    if (!t) return;
    if (!validTicker(t)) {
      setError(`Unknown ticker: ${t}`);
      return;
    }
    setError("");
    setExtraTickers((prev) => (prev.includes(t) || t === ticker.trim().toUpperCase() ? prev : [...prev, t]));
    setExtraInput("");
  };
  const removeExtraTicker = (t) => setExtraTickers((prev) => prev.filter((x) => x !== t));

  const loadData = React.useCallback(async () => {
    if (allSelectedTickers.length === 0) {
      setSeriesByTicker({});
      return;
    }
    setLoading(true);
    setError("");
    try {
      const promises = allSelectedTickers.map((t) => api.listSecurityPricesWithFilters(fromDate, toDate, t));
      const results = await Promise.all(promises);
      const byTicker = {};
      for (let i = 0; i < allSelectedTickers.length; i++) {
        const t = allSelectedTickers[i];
        const rows = Array.isArray(results[i]) ? results[i] : [];
        // sort by date asc
        byTicker[t] = rows.sort((a, b) => String(a.price_date).localeCompare(String(b.price_date)));
      }
      setSeriesByTicker(byTicker);
    } catch (e) {
      setError("Failed to load prices");
      setSeriesByTicker({});
    } finally {
      setLoading(false);
    }
  }, [allSelectedTickers, fromDate, toDate]);

  // Auto-load when inputs change and at least one ticker is selected
  React.useEffect(() => {
    if (allSelectedTickers.length > 0) loadData();
  }, [allSelectedTickers, fromDate, toDate]);

  // Primary metrics (for main ticker only to keep UI simple)
  const primaryPrices = React.useMemo(() => seriesByTicker[ (ticker || "").trim().toUpperCase() ] || [], [seriesByTicker, ticker]);
  const metrics = React.useMemo(() => {
    const prices = primaryPrices;
    if (!prices || prices.length === 0) return null;
    const sorted = prices; // already sorted
    const first = sorted[0];
    const last = sorted[sorted.length - 1];
    const start = Number(first?.price ?? first?.close_px ?? 0);
    const end = Number(last?.price ?? last?.close_px ?? 0);
    const change = end - start;
    const pct = start !== 0 ? (change / start) * 100 : null;
    let high = -Infinity;
    let low = Infinity;
    for (const p of sorted) {
      const v = Number(p.price ?? p.close_px ?? 0);
      if (Number.isFinite(v)) {
        if (v > high) high = v;
        if (v < low) low = v;
      }
    }
    if (high === -Infinity) high = null;
    if (low === Infinity) low = null;
    return {
      startPrice: start || null,
      endPrice: end || null,
      absChange: Number.isFinite(change) ? change : null,
      pctChange: pct,
      high,
      low,
      days: sorted.length,
      startDate: first?.price_date,
      endDate: last?.price_date,
    };
  }, [primaryPrices]);

  // Build chart series in requested mode
  const chartSeries = React.useMemo(() => {
    const out = [];
    const allDatesSet = new Set();
    for (const t of Object.keys(seriesByTicker)) {
      for (const row of seriesByTicker[t]) allDatesSet.add(String(row.price_date));
    }
    const allDates = Array.from(allDatesSet).sort((a, b) => a.localeCompare(b));
    // Prepare per ticker arrays aligned to allDates
    for (const [idx, t] of Object.keys(seriesByTicker).entries()) {
      const rows = seriesByTicker[t];
      if (!rows || rows.length === 0) continue;
      const mapByDate = new Map(rows.map((r) => [String(r.price_date), Number(r.price ?? r.close_px ?? NaN)]));
      const firstVal = Number(rows[0]?.price ?? rows[0]?.close_px ?? NaN);
      const data = allDates.map((ds) => {
        const v = mapByDate.get(ds);
        const price = Number.isFinite(v) ? v : null;
        const perf = (Number.isFinite(firstVal) && Number.isFinite(v) && firstVal !== 0)
          ? ((v / firstVal) - 1) * 100
          : null;
        const value = mode === "performance" ? perf : price;
        return { dateStr: ds, value, price, perf };
      });
      out.push({ name: t, color: COLORS[idx % COLORS.length], data });
    }
    return { series: out, dates: out.length > 0 ? out[0].data.map(d => d.dateStr) : [] };
  }, [seriesByTicker, mode]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, height: "100%", overflow: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <h1 style={{ margin: 0, flex: 1, fontSize: 24 }}>Security Performance Comparison</h1>
      </div>

      {/* Controls — single horizontal toolbar */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "nowrap", overflowX: "auto", background: "white", border: "1px solid #e5e7eb", borderRadius: 8, padding: 8 }}>
        {/* Primary ticker with inline label */}
        <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontWeight: 600, whiteSpace: "nowrap" }}>Primary Ticker</span>
          <input list="tickers" value={ticker} onChange={(e) => setTicker(e.target.value)} placeholder="e.g., AAPL" style={{ padding: 8, border: "1px solid #d1d5db", borderRadius: 6, minWidth: 140 }} />
          <datalist id="tickers">
            {securities.map((s) => (
              <option key={s.security_id} value={(s.ticker || "").toUpperCase()}>{s.name || s.company_name || s.ticker}</option>
            ))}
          </datalist>
        </div>

        {/* Mode toggle next to Primary Ticker */}
        <div style={{ display: "inline-flex", alignItems: "center", gap: 12, background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, padding: "6px 8px" }}>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <input type="radio" name="mode" value="price" checked={mode === "price"} onChange={() => setMode("price")} /> Price
          </label>
          <label style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <input type="radio" name="mode" value="performance" checked={mode === "performance"} onChange={() => setMode("performance")} /> Performance (%)
          </label>
        </div>

        {/* Compare with */}
        <div style={{ display: "inline-flex", alignItems: "center", gap: 6, minWidth: 280 }}>
          <span style={{ fontWeight: 600, whiteSpace: "nowrap" }}>Compare With</span>
          <input list="tickers" value={extraInput} onChange={(e) => setExtraInput(e.target.value)} placeholder="Type ticker" style={{ flex: 1, minWidth: 160, padding: 8, border: "1px solid #d1d5db", borderRadius: 6 }} />
          <button onClick={addExtraTicker} style={{ background: "#10b981", color: "white", border: "none", borderRadius: 6, padding: "8px 10px", cursor: "pointer", fontWeight: 600 }}>Add</button>
        </div>

        {/* Dates */}
        <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontWeight: 600 }}>From</span>
          <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} style={{ padding: 8, border: "1px solid #d1d5db", borderRadius: 6 }} />
        </div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontWeight: 600 }}>To</span>
          <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} style={{ padding: 8, border: "1px solid #d1d5db", borderRadius: 6 }} />
        </div>

        {/* Actions aligned to the right */}
        <div style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 8 }}>
          <button onClick={loadData} style={{ background: "#2563eb", color: "white", border: "none", borderRadius: 6, padding: "8px 12px", cursor: "pointer", fontWeight: 600 }}>Apply</button>
          <button onClick={() => { setTicker(""); setExtraTickers([]); setSeriesByTicker({}); }} style={{ background: "#6b7280", color: "white", border: "none", borderRadius: 6, padding: "8px 12px", cursor: "pointer", fontWeight: 600 }}>Clear</button>
        </div>
      </div>

      {/* Summary */}
      <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 8, padding: 12 }}>
        {selectedSecurity ? (
          <div style={{ marginBottom: 8, fontWeight: 600 }}>
            {(selectedSecurity.ticker || "").toUpperCase()} — {selectedSecurity.name || selectedSecurity.company_name || ""}
          </div>
        ) : (
          <div style={{ marginBottom: 8, color: "#6b7280" }}>Type a primary ticker and optionally add more to compare</div>
        )}
        {loading && <div>Loading...</div>}
        {error && <div style={{ color: "#dc2626" }}>{error}</div>}
        {metrics && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12 }}>
            <Metric label="Start Price" value={metrics.startPrice} />
            <Metric label="End Price" value={metrics.endPrice} />
            <Metric label="Change" value={metrics.absChange} />
            <Metric label="Change %" value={metrics.pctChange} suffix="%" />
            <Metric label="High" value={metrics.high} />
            <Metric label="Low" value={metrics.low} />
          </div>
        )}
      </div>

      {/* Interactive Chart with side panel for selected tickers */}
      {chartSeries.series.length > 0 && (
        <div style={{ display: "flex", gap: 12 }}>
          {/* Left: chart card */}
          <div style={{ flex: 1, background: "white", border: "1px solid #e5e7eb", borderRadius: 8, padding: 12, minWidth: 0 }}>
            <h3 style={{ marginTop: 0 }}>{mode === "price" ? "Price History" : "Performance vs Start (%)"}</h3>
            <InteractiveMultiLineChart series={chartSeries.series} dates={chartSeries.dates} mode={mode} width={820} height={380} />
            {/* Legend */}
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginTop: 8 }}>
              {chartSeries.series.map((s) => (
                <span key={s.name} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12 }}>
                  <span style={{ width: 12, height: 12, background: s.color, borderRadius: 3, border: "1px solid #e5e7eb" }} />
                  {s.name}
                </span>
              ))}
            </div>
          </div>
          {/* Right: selected tickers */}
          <div style={{ width: 240, background: "white", border: "1px solid #e5e7eb", borderRadius: 8, padding: 12, alignSelf: "flex-start" }}>
            <h3 style={{ marginTop: 0, fontSize: 16 }}>Selected Securities</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {allSelectedTickers.length === 0 ? (
                <div style={{ color: "#6b7280", fontSize: 12 }}>None selected</div>
              ) : (
                allSelectedTickers.map((t) => (
                  <span key={t} style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 8px", borderRadius: 8, background: "#f9fafb", border: "1px solid #e5e7eb", fontSize: 12 }}>
                    <span style={{ width: 10, height: 10, background: COLORS[allSelectedTickers.indexOf(t) % COLORS.length], borderRadius: 999 }} />
                    <span style={{ fontWeight: 600 }}>{t}</span>
                    {t !== (ticker || '').trim().toUpperCase() && (
                      <button onClick={() => removeExtraTicker(t)} title="Remove" style={{ marginLeft: "auto", border: "none", background: "transparent", color: "#6b7280", cursor: "pointer", fontWeight: 700 }}>×</button>
                    )}
                  </span>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Table (primary ticker) */}
      {primaryPrices && primaryPrices.length > 0 && (
        <div style={{ background: "white", border: "1px solid #e5e7eb", borderRadius: 8, padding: 12 }}>
          <h3 style={{ marginTop: 0 }}>Data — {ticker.trim().toUpperCase()}</h3>
          <div style={{ overflow: "auto", maxHeight: 360 }}>
            <table style={{ borderCollapse: "collapse", width: "100%" }}>
              <thead>
                <tr>
                  <Th>Date</Th>
                  <Th>Price</Th>
                  <Th>Open</Th>
                  <Th>High</Th>
                  <Th>Low</Th>
                  <Th>Adj Close</Th>
                  <Th>Volume</Th>
                </tr>
              </thead>
              <tbody>
                {primaryPrices.map((p) => (
                  <tr key={`${p.security_price_id || ''}-${p.price_date}`}>
                    <Td>{p.price_date}</Td>
                    <Td>{fmtNum(p.price)}</Td>
                    <Td>{fmtNum(p.open_px)}</Td>
                    <Td>{fmtNum(p.high_px)}</Td>
                    <Td>{fmtNum(p.low_px)}</Td>
                    <Td>{fmtNum(p.adj_close_px)}</Td>
                    <Td>{fmtNum(p.volume)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function InteractiveMultiLineChart({ series, dates, mode = "price", width = 900, height = 320 }) {
  const margin = { top: 20, right: 24, bottom: 36, left: 60 };
  const w = width - margin.left - margin.right;
  const h = height - margin.top - margin.bottom;

  // Build x values (as Date objects) from dates
  const xDates = dates.map((d) => new Date(`${d}T00:00:00`));
  const xMin = xDates[0];
  const xMax = xDates[dates.length - 1];
  const xScale = (d) => {
    const t = new Date(`${d}T00:00:00`).getTime();
    const t0 = xMin.getTime();
    const t1 = xMax.getTime();
    if (t1 === t0) return margin.left + w / 2;
    return margin.left + ((t - t0) / (t1 - t0)) * w;
  };

  // Y domain from all series values
  let yMin = Infinity, yMax = -Infinity;
  for (const s of series) {
    for (const p of s.data) {
      if (p.value == null) continue;
      if (p.value < yMin) yMin = p.value;
      if (p.value > yMax) yMax = p.value;
    }
  }
  if (!isFinite(yMin) || !isFinite(yMax)) {
    yMin = 0; yMax = 1;
  }
  // add a small padding
  const pad = (yMax - yMin) * 0.05 || 1;
  yMin -= pad; yMax += pad;
  const yScale = (v) => {
    if (yMax === yMin) return margin.top + h / 2;
    return margin.top + (h - ((v - yMin) / (yMax - yMin)) * h);
  };

  // Build axes ticks
  function niceNumber(range, round) {
    const exponent = Math.floor(Math.log10(range));
    const fraction = range / Math.pow(10, exponent);
    let niceFraction;
    if (round) {
      if (fraction < 1.5) niceFraction = 1;
      else if (fraction < 3) niceFraction = 2;
      else if (fraction < 7) niceFraction = 5;
      else niceFraction = 10;
    } else {
      if (fraction <= 1) niceFraction = 1;
      else if (fraction <= 2) niceFraction = 2;
      else if (fraction <= 5) niceFraction = 5;
      else niceFraction = 10;
    }
    return niceFraction * Math.pow(10, exponent);
  }
  function niceScale(min, max, ticks = 5) {
    const range = niceNumber(max - min, false);
    const tickSpacing = niceNumber(range / (ticks - 1), true);
    const niceMin = Math.floor(min / tickSpacing) * tickSpacing;
    const niceMax = Math.ceil(max / tickSpacing) * tickSpacing;
    return { niceMin, niceMax, tickSpacing };
  }
  const yTicks = (() => {
    const { niceMin, niceMax, tickSpacing } = niceScale(yMin, yMax, 6);
    const arr = [];
    for (let v = niceMin; v <= niceMax + 1e-9; v += tickSpacing) arr.push(v);
    return arr;
  })();
  const xTicks = (() => {
    const count = Math.min(8, Math.max(3, Math.floor(w / 120)));
    const arr = [];
    if (xDates.length === 0) return arr;
    for (let i = 0; i < count; i++) {
      const idx = Math.round((i / (count - 1)) * (xDates.length - 1));
      arr.push(dates[idx]);
    }
    return Array.from(new Set(arr)); // unique
  })();

  // Hover state
  const [hover, setHover] = React.useState(null); // { idx, x, yPerSeries: [{x,y,value,name,color}] }
  const svgRef = React.useRef(null);

  function onMove(e) {
    if (!svgRef.current || dates.length === 0) return;
    const rect = svgRef.current.getBoundingClientRect();
    const xPos = e.clientX - rect.left;
    // find nearest date index by distance in pixels
    let bestIdx = 0;
    let bestDist = Infinity;
    for (let i = 0; i < dates.length; i++) {
      const dx = Math.abs(xScale(dates[i]) - xPos);
      if (dx < bestDist) { bestDist = dx; bestIdx = i; }
    }
    const hoverX = xScale(dates[bestIdx]);
    const yPerSeries = series.map((s) => {
      const dp = s.data[bestIdx];
      const v = dp?.value ?? null;
      const price = dp?.price ?? null;
      const perf = dp?.perf ?? null;
      return { name: s.name, color: s.color, x: hoverX, y: v == null ? null : yScale(v), value: v, price, perf };
    });
    setHover({ idx: bestIdx, x: hoverX, yPerSeries });
  }
  function onLeave() { setHover(null); }

  return (
    <svg ref={svgRef} width={width} height={height} onMouseMove={onMove} onMouseLeave={onLeave} style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8 }}>
      {/* Grid + axes */}
      {/* Y grid lines */}
      {yTicks.map((yt, i) => (
        <g key={`yg-${i}`}>
          <line x1={margin.left} x2={margin.left + w} y1={yScale(yt)} y2={yScale(yt)} stroke="#f3f4f6" />
          <text x={margin.left - 8} y={yScale(yt)} textAnchor="end" dominantBaseline="middle" fontSize={11} fill="#6b7280">
            {mode === 'performance' ? `${fmtNum(yt)}%` : fmtNum(yt)}
          </text>
        </g>
      ))}
      {/* X axis */}
      <line x1={margin.left} x2={margin.left + w} y1={margin.top + h} y2={margin.top + h} stroke="#9ca3af" />
      {xTicks.map((d, i) => (
        <g key={`xt-${i}`}>
          <line x1={xScale(d)} x2={xScale(d)} y1={margin.top} y2={margin.top + h} stroke="#f9fafb" />
          <text x={xScale(d)} y={margin.top + h + 16} textAnchor="middle" fontSize={11} fill="#6b7280">{d}</text>
        </g>
      ))}
      {/* Axis labels */}
      <text x={margin.left + w / 2} y={height - 4} textAnchor="middle" fontSize={12} fill="#374151">Date</text>
      <text x={12} y={margin.top - 6} textAnchor="start" fontSize={12} fill="#374151">{mode === 'performance' ? 'Performance (%)' : 'Price'}</text>

      {/* Lines */}
      {series.map((s) => {
        const pts = s.data
          .map((dp) => (dp.value == null ? null : `${xScale(dp.dateStr)},${yScale(dp.value)}`))
          .filter(Boolean)
          .join(" ");
        return <polyline key={s.name} fill="none" stroke={s.color} strokeWidth={2} points={pts} />;
      })}

      {/* Hover overlay */}
      {hover && (
        <g>
          <line x1={hover.x} x2={hover.x} y1={margin.top} y2={margin.top + h} stroke="#9ca3af" strokeDasharray="3,3" />
          {hover.yPerSeries.map((p) => (
            p.y == null ? null : <circle key={p.name} cx={hover.x} cy={p.y} r={3.5} fill="#fff" stroke={p.color} strokeWidth={2} />
          ))}
          {/* Tooltip */}
          {(() => {
            const dateLabel = dates[hover.idx];
            const lines = hover.yPerSeries
              .filter((p) => p.value != null)
              .map((p) => {
                const priceText = p.price == null ? '-' : `${fmtNum(p.price)}`;
                const perfText = p.perf == null ? '-' : `${fmtNum(p.perf)}%`;
                return { name: p.name, color: p.color, priceText, perfText };
              });
            if (lines.length === 0) return null;
            const boxX = Math.min(Math.max(hover.x + 8, margin.left + 4), margin.left + w - 240);
            const boxY = margin.top + 8;
            const boxW = 230;
            const boxH = 24 + lines.length * 18;
            return (
              <g>
                <rect x={boxX} y={boxY} width={boxW} height={boxH} rx={6} ry={6} fill="#111827" opacity={0.9} />
                <text x={boxX + 8} y={boxY + 16} fill="#e5e7eb" fontSize={12} fontWeight={700}>{dateLabel}</text>
                {lines.map((ln, i) => (
                  <g key={ln.name}>
                    <rect x={boxX + 8} y={boxY + 22 + i * 18 - 8} width={8} height={8} fill={ln.color} rx={1} ry={1} />
                    <text x={boxX + 20} y={boxY + 22 + i * 18} fill="#f9fafb" fontSize={12}>{ln.name}: Price {ln.priceText} • Perf {ln.perfText}</text>
                  </g>
                ))}
              </g>
            );
          })()}
        </g>
      )}
    </svg>
  );
}

function fmtNum(v) {
  if (v == null) return "-";
  const n = Number(v);
  if (!Number.isFinite(n)) return String(v);
  try { return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }); } catch { return n.toFixed(2); }
}

function Metric({ label, value, suffix }) {
  return (
    <div style={{ padding: 12, border: "1px solid #e5e7eb", borderRadius: 8 }}>
      <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700 }}>
        {value == null ? "-" : `${fmtNum(value)}${suffix || ""}`}
      </div>
    </div>
  );
}

function Th({ children }) {
  return <th style={{ textAlign: "left", borderBottom: "1px solid #e5e7eb", padding: "8px 6px", position: "sticky", top: 0, background: "#fafafa" }}>{children}</th>;
}
function Td({ children }) {
  return <td style={{ borderBottom: "1px solid #f0f0f0", padding: "6px" }}>{children}</td>;
}
