import React from "react";
import { api } from "../../api/client.js";

// Helper function to format numbers with commas and 2 decimal places
function formatNumber(value) {
  if (value == null || value === "" || isNaN(value)) return "-";
  const num = typeof value === "number" ? value : Number(value);
  if (!Number.isFinite(num)) return String(value);
  return num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function TransactionPerformanceComparison() {
  const [pairs, setPairs] = React.useState([]);
  const [selectedPair, setSelectedPair] = React.useState("");
  const [fromDate, setFromDate] = React.useState(() => {
    // Default to 1 year ago
    const date = new Date();
    date.setDate(date.getDate() - 365);
    return date.toISOString().split('T')[0];
  });
  const [toDate, setToDate] = React.useState(() => {
    // Default to today
    const date = new Date();
    return date.toISOString().split('T')[0];
  });
  const [performanceData, setPerformanceData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [chartLoading, setChartLoading] = React.useState(false);
  const [error, setError] = React.useState("");
  const [abortController, setAbortController] = React.useState(null);

  // Load linked transaction pairs on component mount
  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const response = await api.getLinkedTransactionPairs();
        if (alive) {
          setPairs(response.pairs || []);
          if (response.pairs && response.pairs.length > 0) {
            setSelectedPair(response.pairs[0].pair_id);
          }
        }
      } catch (e) {
        if (alive) setError("Failed to load transaction pairs.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => (alive = false);
  }, []);

  // Stop current loading operation
  const stopLoading = React.useCallback(() => {
    if (abortController) {
      abortController.abort();
      setAbortController(null);
      setChartLoading(false);
    }
  }, [abortController]);

  // Performance data loading function with abort support
  const loadPerformanceData = React.useCallback(async (autoLoad = false) => {
    if (!selectedPair || !fromDate || !toDate) return;
    
    // Cancel any existing request
    if (abortController) {
      abortController.abort();
    }
    
    const controller = new AbortController();
    setAbortController(controller);
    setChartLoading(true);
    setError("");
    
    try {
      const response = await api.getPerformanceComparison(selectedPair, fromDate, toDate, {
        signal: controller.signal
      });
      if (!controller.signal.aborted) {
        setPerformanceData(response);
        setError("");
      }
    } catch (e) {
      if (!controller.signal.aborted) {
        setError("Failed to load performance data.");
      }
    } finally {
      if (!controller.signal.aborted) {
        setChartLoading(false);
        setAbortController(null);
      }
    }
  }, [selectedPair, fromDate, toDate, abortController]);

  // Date range helper functions
  const getDateRange = React.useCallback((period) => {
    const today = new Date(2025, 9, 10); // October 10, 2025 (month is 0-indexed)
    let fromDate;
    
    switch (period) {
      case '1d':
        fromDate = new Date(today);
        fromDate.setDate(today.getDate() - 1);
        break;
      case '1w':
        fromDate = new Date(today);
        fromDate.setDate(today.getDate() - 7);
        break;
      case '1m':
        fromDate = new Date(today);
        fromDate.setMonth(today.getMonth() - 1);
        break;
      case '6m':
        fromDate = new Date(today);
        fromDate.setMonth(today.getMonth() - 6);
        break;
      case '1y':
        fromDate = new Date(today);
        fromDate.setFullYear(today.getFullYear() - 1);
        break;
      case 'ytd':
        fromDate = new Date(today.getFullYear(), 0, 1); // January 1st of current year
        break;
      case '5y':
        fromDate = new Date(today);
        fromDate.setFullYear(today.getFullYear() - 5);
        break;
      case 'all':
        fromDate = new Date(2000, 0, 1); // Far back date to get all available data
        break;
      default:
        return;
    }
    
    setFromDate(fromDate.toISOString().split('T')[0]);
    setToDate(today.toISOString().split('T')[0]);
    
    // Auto-refresh with new date range
    if (selectedPair) {
      loadPerformanceData(false);
    }
  }, [selectedPair, loadPerformanceData]);

  if (loading) return <div>Loading transaction pairs...</div>;
  if (error && !pairs.length) return <div style={{ color: "#b91c1c" }}>{error}</div>;

  return (
    <div style={{ height: "100vh", overflow: "auto", padding: "16px" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", marginBottom: 8 }}>
        <h1 style={{ margin: 0, flex: 1, fontSize: 24 }}>Transaction Performance Comparison</h1>
      </div>

      {pairs.length === 0 ? (
        <div style={{ background: "#f8fafc", padding: 20, borderRadius: 8, marginTop: 12, textAlign: "center" }}>
          <h3>No Linked Transaction Pairs Found</h3>
          <p>To use this feature, you need to create duplicate transactions using the "Duplicate as VOO" feature on the transactions list page.</p>
        </div>
      ) : (
        <>
          {/* Controls */}
          <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", padding: 16, marginTop: 12 }}>
            <div style={{ display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
              <label style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 200 }}>
                <span>Transaction Pair</span>
                <select
                  value={selectedPair}
                  onChange={(e) => setSelectedPair(e.target.value)}
                  style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1", height: 40 }}
                >
                  {pairs.map((pair) => (
                    <option key={pair.pair_id} value={pair.pair_id}>
                      {pair.original.security_ticker} - {pair.original.security_name} vs {pair.duplicate.security_ticker} - {pair.duplicate.security_name} (${pair.original.total_inv_amt})
                    </option>
                  ))}
                </select>
              </label>

              <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span>From Date</span>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1", height: 40, boxSizing: "border-box" }}
                />
              </label>

              <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span>To Date</span>
                <input
                  type="date"
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  style={{ padding: 8, borderRadius: 6, border: "1px solid #cbd5e1", height: 40, boxSizing: "border-box" }}
                />
              </label>

              {chartLoading ? (
                <button
                  type="button"
                  onClick={stopLoading}
                  style={{ 
                    background: "#ef4444", 
                    color: "white", 
                    padding: "8px 16px", 
                    borderRadius: 8, 
                    border: "none", 
                    cursor: "pointer",
                    fontWeight: 600,
                    height: 40
                  }}
                >
                  Stop Loading
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => loadPerformanceData(false)}
                  disabled={!selectedPair || !fromDate || !toDate}
                  style={{ 
                    background: (!selectedPair || !fromDate || !toDate) ? "#94a3b8" : "#10b981", 
                    color: "white", 
                    padding: "8px 16px", 
                    borderRadius: 8, 
                    border: "none", 
                    cursor: (!selectedPair || !fromDate || !toDate) ? "not-allowed" : "pointer",
                    fontWeight: 600,
                    height: 40
                  }}
                >
                  Refresh
                </button>
              )}

              {/* Date Range Buttons - moved to same line */}
              {[
                { label: '1D', value: '1d' },
                { label: '1W', value: '1w' },
                { label: '1M', value: '1m' },
                { label: '6M', value: '6m' },
                { label: '1Y', value: '1y' },
                { label: 'YTD', value: 'ytd' },
                { label: '5Y', value: '5y' },
                { label: 'All', value: 'all' }
              ].map((range) => (
                <button
                  key={range.value}
                  type="button"
                  onClick={() => getDateRange(range.value)}
                  disabled={!selectedPair || chartLoading}
                  style={{
                    background: (!selectedPair || chartLoading) ? "#e2e8f0" : "#f1f5f9",
                    color: (!selectedPair || chartLoading) ? "#94a3b8" : "#475569",
                    border: "1px solid #cbd5e1",
                    padding: "6px 12px",
                    borderRadius: 6,
                    fontSize: "12px",
                    fontWeight: 500,
                    cursor: (!selectedPair || chartLoading) ? "not-allowed" : "pointer",
                    transition: "all 0.2s ease",
                    height: 40,
                    boxSizing: "border-box"
                  }}
                  onMouseEnter={(e) => {
                    if (!(!selectedPair || chartLoading)) {
                      e.target.style.background = "#e2e8f0";
                      e.target.style.borderColor = "#94a3b8";
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!(!selectedPair || chartLoading)) {
                      e.target.style.background = "#f1f5f9";
                      e.target.style.borderColor = "#cbd5e1";
                    }
                  }}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Investment Performance Summary */}
          {performanceData && (
            <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", padding: 16, marginTop: 12 }}>
              <h3 style={{ marginTop: 0 }}>Investment Performance Summary</h3>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div style={{ padding: 12, background: "#f8fafc", borderRadius: 8 }}>
                  <h4 style={{ margin: "0 0 8px 0" }}>Original Investment</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 16px", fontSize: "14px" }}>
                    <p style={{ margin: "4px 0" }}><strong>Security:</strong> {performanceData.pair_info.original.security_ticker} - {performanceData.pair_info.original.security_name}</p>
                    <p style={{ margin: "4px 0" }}><strong>Transaction Date:</strong> {new Date(performanceData.pair_info.original.transaction_date).toLocaleDateString()}</p>
                    <p style={{ margin: "4px 0" }}><strong>Transaction Price:</strong> ${formatNumber(performanceData.pair_info.original.transaction_price)}</p>
                    <p style={{ margin: "4px 0" }}><strong>Quantity:</strong> {formatNumber(performanceData.pair_info.original.quantity)}</p>
                    <p style={{ margin: "4px 0" }}><strong>Investment Amount:</strong> ${formatNumber(performanceData.pair_info.original.total_inv_amt)}</p>
                    <p style={{ margin: "4px 0" }}><strong>Total Fees Paid:</strong> ${formatNumber(performanceData.pair_info.original.total_fees_paid || 0)}</p>
                    {performanceData.pair_info.original.current_value && (
                      <>
                        <p style={{ margin: "4px 0" }}><strong>Current Value:</strong> ${formatNumber(performanceData.pair_info.original.current_value)}</p>
                        <p style={{ margin: "4px 0" }}><strong>Unrealized Gain/Loss:</strong> <span style={{ color: (performanceData.pair_info.original.unrealized_gain_loss || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                          ${(performanceData.pair_info.original.unrealized_gain_loss || 0) >= 0 ? '+' : ''}{formatNumber(Math.abs(performanceData.pair_info.original.unrealized_gain_loss || 0))}
                        </span></p>
                        <p style={{ margin: "4px 0" }}><strong>Unrealized Gain/Loss %:</strong> <span style={{ color: (performanceData.pair_info.original.unrealized_gain_loss_pct || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                          {(performanceData.pair_info.original.unrealized_gain_loss_pct || 0) >= 0 ? '+' : ''}{formatNumber(Math.abs(performanceData.pair_info.original.unrealized_gain_loss_pct || 0))}%
                        </span></p>
                      </>
                    )}
                  </div>
                </div>
                <div style={{ padding: 12, background: "#f8fafc", borderRadius: 8 }}>
                  <h4 style={{ margin: "0 0 8px 0" }}>Comparison Investment</h4>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px 16px", fontSize: "14px" }}>
                    <p style={{ margin: "4px 0" }}><strong>Security:</strong> {performanceData.pair_info.duplicate.security_ticker} - {performanceData.pair_info.duplicate.security_name}</p>
                    <p style={{ margin: "4px 0" }}><strong>Transaction Date:</strong> {new Date(performanceData.pair_info.duplicate.transaction_date).toLocaleDateString()}</p>
                    <p style={{ margin: "4px 0" }}><strong>Transaction Price:</strong> ${formatNumber(performanceData.pair_info.duplicate.transaction_price)}</p>
                    <p style={{ margin: "4px 0" }}><strong>Quantity:</strong> {formatNumber(performanceData.pair_info.duplicate.quantity)}</p>
                    <p style={{ margin: "4px 0" }}><strong>Investment Amount:</strong> ${formatNumber(performanceData.pair_info.duplicate.total_inv_amt)}</p>
                    <p style={{ margin: "4px 0" }}><strong>Total Fees Paid:</strong> ${formatNumber(performanceData.pair_info.duplicate.total_fees_paid || 0)}</p>
                    {performanceData.pair_info.duplicate.current_value && (
                      <>
                        <p style={{ margin: "4px 0" }}><strong>Current Value:</strong> ${formatNumber(performanceData.pair_info.duplicate.current_value)}</p>
                        <p style={{ margin: "4px 0" }}><strong>Unrealized Gain/Loss:</strong> <span style={{ color: (performanceData.pair_info.duplicate.unrealized_gain_loss || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                          ${(performanceData.pair_info.duplicate.unrealized_gain_loss || 0) >= 0 ? '+' : ''}{formatNumber(Math.abs(performanceData.pair_info.duplicate.unrealized_gain_loss || 0))}
                        </span></p>
                        <p style={{ margin: "4px 0" }}><strong>Unrealized Gain/Loss %:</strong> <span style={{ color: (performanceData.pair_info.duplicate.unrealized_gain_loss_pct || 0) >= 0 ? '#10b981' : '#ef4444' }}>
                          {(performanceData.pair_info.duplicate.unrealized_gain_loss_pct || 0) >= 0 ? '+' : ''}{formatNumber(Math.abs(performanceData.pair_info.duplicate.unrealized_gain_loss_pct || 0))}%
                        </span></p>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Chart Area */}
          <div style={{ background: "white", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.05)", padding: 16, marginTop: 12, minHeight: 400 }}>
            {chartLoading ? (
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 300 }}>
                Loading performance data...
              </div>
            ) : performanceData ? (
              <PerformanceChart data={performanceData} fromDate={fromDate} toDate={toDate} />
            ) : (
              <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 300, color: "#64748b" }}>
                Select a transaction pair and date range to view performance comparison
              </div>
            )}
            {error && <div style={{ color: "#b91c1c", marginTop: 8 }}>{error}</div>}
          </div>
        </>
      )}
    </div>
  );
}

// Simple line chart component using HTML5 Canvas
function PerformanceChart({ data, fromDate, toDate }) {
  const canvasRef = React.useRef(null);
  const [hoveredPoint, setHoveredPoint] = React.useState(null);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    
    // Set canvas size
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 20, bottom: 60, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    const originalData = data.performance_data.original || [];
    const duplicateData = data.performance_data.duplicate || [];

    if (originalData.length === 0 && duplicateData.length === 0) {
      ctx.fillStyle = "#64748b";
      ctx.font = "14px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No performance data available for the selected date range", width / 2, height / 2);
      return;
    }

    // Combine all data points to find min/max values
    const allData = [...originalData, ...duplicateData];
    const allPerformances = allData.map(d => d.performance);
    const minPerformance = Math.min(...allPerformances);
    const maxPerformance = Math.max(...allPerformances);
    
    // Add some padding to the range
    const performanceRange = maxPerformance - minPerformance;
    const performancePadding = performanceRange * 0.1;
    const yMin = minPerformance - performancePadding;
    const yMax = maxPerformance + performancePadding;

    // Get date range - use selected date range instead of data points for proper X-axis
    const minDate = new Date(fromDate);
    const maxDate = new Date(toDate);

    // Helper functions
    const getX = (date) => padding.left + ((new Date(date) - minDate) / (maxDate - minDate)) * chartWidth;
    const getY = (performance) => padding.top + ((yMax - performance) / (yMax - yMin)) * chartHeight;

    // Draw grid lines
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    
    // Horizontal grid lines (performance values)
    const performanceSteps = 5;
    for (let i = 0; i <= performanceSteps; i++) {
      const performance = yMin + (yMax - yMin) * (i / performanceSteps);
      const y = getY(performance);
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(padding.left + chartWidth, y);
      ctx.stroke();
      
      // Y-axis labels
      ctx.fillStyle = "#64748b";
      ctx.font = "12px sans-serif";
      ctx.textAlign = "right";
      ctx.fillText(`${performance.toFixed(1)}%`, padding.left - 5, y + 4);
    }

    // Draw zero line if it's in range
    if (yMin <= 0 && yMax >= 0) {
      const zeroY = getY(0);
      ctx.strokeStyle = "#374151";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(padding.left, zeroY);
      ctx.lineTo(padding.left + chartWidth, zeroY);
      ctx.stroke();
    }

    // Draw original data line
    if (originalData.length > 0) {
      ctx.strokeStyle = "#3b82f6";
      ctx.lineWidth = 2;
      ctx.beginPath();
      originalData.forEach((point, index) => {
        const x = getX(point.date);
        const y = getY(point.performance);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Draw points
      ctx.fillStyle = "#3b82f6";
      originalData.forEach(point => {
        const x = getX(point.date);
        const y = getY(point.performance);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }

    // Draw duplicate data line
    if (duplicateData.length > 0) {
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 2;
      ctx.beginPath();
      duplicateData.forEach((point, index) => {
        const x = getX(point.date);
        const y = getY(point.performance);
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Draw points
      ctx.fillStyle = "#10b981";
      duplicateData.forEach(point => {
        const x = getX(point.date);
        const y = getY(point.performance);
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }

    // Draw axes
    ctx.strokeStyle = "#374151";
    ctx.lineWidth = 1;
    // Y-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, padding.top + chartHeight);
    ctx.stroke();
    // X-axis
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + chartHeight);
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.stroke();

    // X-axis labels (dates)
    ctx.fillStyle = "#64748b";
    ctx.font = "12px sans-serif";
    ctx.textAlign = "center";
    const dateSteps = Math.min(5, Math.max(allData.length, 1));
    for (let i = 0; i <= dateSteps; i++) {
      const date = new Date(minDate.getTime() + (maxDate - minDate) * (i / dateSteps));
      const x = getX(date);
      const dateStr = date.toLocaleDateString();
      ctx.fillText(dateStr, x, padding.top + chartHeight + 20);
    }

  }, [data]);

  const handleMouseMove = (event) => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Find closest data point
    const padding = { top: 20, right: 20, bottom: 60, left: 60 };
    if (x < padding.left || x > rect.width - padding.right || 
        y < padding.top || y > rect.height - padding.bottom) {
      setHoveredPoint(null);
      return;
    }

    // Use selected date range for hover calculations
    const minDate = new Date(fromDate);
    const maxDate = new Date(toDate);
    const chartWidth = rect.width - padding.left - padding.right;
    
    const dateAtX = new Date(minDate.getTime() + ((x - padding.left) / chartWidth) * (maxDate - minDate));
    
    // Find closest data points
    let closestOriginal = null;
    let closestDuplicate = null;
    let minOriginalDistance = Infinity;
    let minDuplicateDistance = Infinity;

    data.performance_data.original?.forEach(point => {
      const distance = Math.abs(new Date(point.date) - dateAtX);
      if (distance < minOriginalDistance) {
        minOriginalDistance = distance;
        closestOriginal = point;
      }
    });

    data.performance_data.duplicate?.forEach(point => {
      const distance = Math.abs(new Date(point.date) - dateAtX);
      if (distance < minDuplicateDistance) {
        minDuplicateDistance = distance;
        closestDuplicate = point;
      }
    });

    if (closestOriginal || closestDuplicate) {
      setHoveredPoint({
        original: closestOriginal,
        duplicate: closestDuplicate,
        x: event.clientX,
        y: event.clientY
      });
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <h3 style={{ marginTop: 0, marginBottom: 16, textAlign: "center" }}>Investment Performance Comparison</h3>
      
      {/* Legend */}
      <div style={{ display: "flex", justifyContent: "center", gap: 24, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 16, height: 2, backgroundColor: "#3b82f6" }}></div>
          <span>Original Investment ({data.pair_info.original.security_ticker})</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{ width: 16, height: 2, backgroundColor: "#10b981" }}></div>
          <span>Comparison Investment ({data.pair_info.duplicate.security_ticker})</span>
        </div>
      </div>

      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "300px", cursor: "crosshair" }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredPoint(null)}
      />

      {/* Investment Performance Tooltip */}
      {hoveredPoint && (
        <div
          style={{
            position: "fixed",
            left: hoveredPoint.x + 10,
            top: hoveredPoint.y - 10,
            background: "white",
            border: "1px solid #cbd5e1",
            borderRadius: 6,
            padding: 8,
            boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
            fontSize: 12,
            zIndex: 1000,
            pointerEvents: "none"
          }}
        >
          {hoveredPoint.original && (
            <div style={{ color: "#3b82f6", marginBottom: 4 }}>
              <strong>{data.pair_info.original.security_ticker} Investment:</strong>
              <br />
              <span>Price: ${formatNumber(hoveredPoint.original.price)}</span>
              <br />
              <span>Performance: {hoveredPoint.original.performance >= 0 ? '+' : ''}{formatNumber(Math.abs(hoveredPoint.original.performance))}%</span>
              <br />
              <span style={{ color: "#64748b" }}>Current Value: ${formatNumber(hoveredPoint.original.current_value)}</span>
              <br />
              <span style={{ color: hoveredPoint.original.unrealized_gain_loss >= 0 ? '#10b981' : '#ef4444' }}>
                Gain/Loss: ${hoveredPoint.original.unrealized_gain_loss >= 0 ? '+' : ''}{formatNumber(Math.abs(hoveredPoint.original.unrealized_gain_loss || 0))}
              </span>
            </div>
          )}
          {hoveredPoint.duplicate && (
            <div style={{ color: "#10b981" }}>
              <strong>{data.pair_info.duplicate.security_ticker} Investment:</strong>
              <br />
              <span>Price: ${formatNumber(hoveredPoint.duplicate.price)}</span>
              <br />
              <span>Performance: {hoveredPoint.duplicate.performance >= 0 ? '+' : ''}{formatNumber(Math.abs(hoveredPoint.duplicate.performance))}%</span>
              <br />
              <span style={{ color: "#64748b" }}>Current Value: ${formatNumber(hoveredPoint.duplicate.current_value)}</span>
              <br />
              <span style={{ color: hoveredPoint.duplicate.unrealized_gain_loss >= 0 ? '#10b981' : '#ef4444' }}>
                Gain/Loss: ${hoveredPoint.duplicate.unrealized_gain_loss >= 0 ? '+' : ''}{formatNumber(Math.abs(hoveredPoint.duplicate.unrealized_gain_loss || 0))}
              </span>
            </div>
          )}
          {hoveredPoint.original && (
            <div style={{ color: "#64748b", marginTop: 4, fontSize: 11 }}>
              {new Date(hoveredPoint.original.date).toLocaleDateString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
}