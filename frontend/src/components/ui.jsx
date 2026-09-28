import { useEffect, useMemo, useState } from 'react'

export const money = (value) => `¥${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}`
export const num = (value) => Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })

const NAV_ICON_PATHS = {
  upload: <><path d="M12 15V4" /><path d="m7.5 8.5 4.5-4.5 4.5 4.5" /><path d="M5 15.5v3h14v-3" /></>,
  overview: <><rect x="4" y="4" width="6" height="6" rx="1" /><rect x="14" y="4" width="6" height="6" rx="1" /><rect x="4" y="14" width="6" height="6" rx="1" /><rect x="14" y="14" width="6" height="6" rx="1" /></>,
  products: <><path d="m12 3 8 4.5v9L12 21l-8-4.5v-9L12 3Z" /><path d="m4.5 7.5 7.5 4.2 7.5-4.2M12 11.7V21" /></>,
  users: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
  anomalies: <><path d="M12 3 20 6v5c0 5.1-3.3 8.3-8 10-4.7-1.7-8-4.9-8-10V6l8-3Z" /><path d="M12 8v5" /><path d="M12 16.5h.01" /></>,
  forecast: <><path d="M4 17 9 12l3 3 7-8" /><path d="M15 7h4v4" /></>,
  screen: <><rect x="3" y="4" width="18" height="14" rx="2" /><path d="M8 21h8M12 18v3" /></>,
  report: <><path d="M6 3h9l3 3v15H6z" /><path d="M15 3v4h4M9 12h6M9 16h6" /></>,
  publish: <><path d="m4 5 16 7-16 7 3-7-3-7Z" /><path d="M7 12h13" /></>,
  admin: <><path d="M4 5h16v14H4z" /><path d="M8 9h8M8 13h5M8 17h3" /><path d="M17 15.5v3M15.5 17h3" /></>,
  settings: <><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.38a2 2 0 0 0-.73-2.73l-.15-.09a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2Z" /><circle cx="12" cy="12" r="3" /></>,
  logout: <><path d="M10 17l5-5-5-5" /><path d="M15 12H3" /><path d="M14 4h5v16h-5" /></>
}

export function Icon({ name }) {
  return <span className="icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">{NAV_ICON_PATHS[name] || NAV_ICON_PATHS.overview}</svg></span>
}
export function Button({ children, onClick, secondary = false, disabled = false, type = 'button' }) { return <button type={type} className={secondary ? 'button secondary' : 'button'} onClick={onClick} disabled={disabled}>{children}</button> }
export function Card({ title, subtitle, action, children, className = '' }) { return <section className={`card ${className}`}><div className="card-head"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>{children}</section> }
export function Metric({ label, value, detail, accent = false }) { return <div className={`metric ${accent ? 'accent' : ''}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div> }

export function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return undefined
    const timeout = window.setTimeout(onClose, toast.type === 'error' ? 6000 : 3500)
    return () => window.clearTimeout(timeout)
  }, [toast])
  if (!toast) return null
  return <div className={`toast ${toast.type || 'info'}`} role="status"><span>{toast.type === 'error' ? '!' : toast.type === 'success' ? '✓' : 'i'}</span><b>{toast.message}</b><button onClick={onClose} aria-label="关闭">×</button></div>
}

export function DataTable({ rows = [], columns, empty = '暂无数据', searchable = true, pageSize = 10 }) {
  const [query, setQuery] = useState(''); const [sort, setSort] = useState(null); const [page, setPage] = useState(1)
  const filtered = useMemo(() => rows.filter(row => !query || columns.some(([key]) => String(row[key] ?? '').toLowerCase().includes(query.toLowerCase()))), [rows, columns, query])
  const sorted = useMemo(() => sort ? [...filtered].sort((a, b) => { const av = a[sort.key] ?? ''; const bv = b[sort.key] ?? ''; const result = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv), 'zh-CN'); return sort.direction === 'desc' ? -result : result }) : filtered, [filtered, sort])
  const pages = Math.max(1, Math.ceil(sorted.length / pageSize)); const safePage = Math.min(page, pages); const visible = sorted.slice((safePage - 1) * pageSize, safePage * pageSize)
  if (!rows.length) return <div className="empty">{empty}</div>
  return <div className="table-box">{searchable && <div className="table-tools"><label className="search"><span>⌕</span><input value={query} onChange={event => { setQuery(event.target.value); setPage(1) }} placeholder="搜索当前表格" /></label><span>{num(sorted.length)} 条记录</span></div>}<div className="table-scroll"><table><thead><tr>{columns.map(([key, label]) => <th key={key}><button className="sort-button" onClick={() => setSort(current => current?.key === key && current.direction === 'asc' ? { key, direction: 'desc' } : { key, direction: 'asc' })}>{label}<small>{sort?.key === key ? (sort.direction === 'asc' ? ' ↑' : ' ↓') : ''}</small></button></th>)}</tr></thead><tbody>{visible.map((row, index) => <tr key={`${row.order_id || row.product_name || row.customer_id || row.cluster || 'row'}-${index}`}>{columns.map(([key]) => <td key={key}>{key.includes('amount') || key.includes('revenue') || key.includes('monetary') || key.includes('price') ? money(row[key]) : typeof row[key] === 'number' ? num(row[key]) : (row[key] ?? '—')}</td>)}</tr>)}</tbody></table></div><div className="pagination"><span>第 {safePage} / {pages} 页</span><div><button disabled={safePage <= 1} onClick={() => setPage(safePage - 1)}>上一页</button><button disabled={safePage >= pages} onClick={() => setPage(safePage + 1)}>下一页</button></div></div></div>
}

export function LineChart({ rows, forecast = false, showYAxis = false }) {
  const [hoveredPoint, setHoveredPoint] = useState(null)
  if (!rows?.length) return <div className="empty chart-empty">暂无趋势数据</div>

  const hasBounds = forecast && rows.some(row => row.lower_bound != null || row.upper_bound != null)
  const values = rows.map(row => Number(row.revenue ?? row.predicted) || 0)
  const boundValues = hasBounds ? rows.flatMap(row => [Number(row.lower_bound ?? row.predicted) || 0, Number(row.upper_bound ?? row.predicted) || 0]) : []
  const max = Math.max(...values, ...boundValues, 1)
  const min = Math.min(...values, ...boundValues, 0)
  const mid = (max + min) / 2
  const width = 760
  const height = 220
  const xFor = index => (index / Math.max(values.length - 1, 1)) * width
  const yFor = value => height - ((value - min) / Math.max(max - min, 1)) * (height - 24)
  const points = values.map((value, index) => `${xFor(index)},${yFor(value)}`).join(' ')
  const pointData = values.map((value, index) => ({ x: xFor(index), y: yFor(value), row: rows[index] }))
  const upperPoints = hasBounds ? rows.map((row, index) => `${xFor(index)},${yFor(Number(row.upper_bound ?? row.predicted) || 0)}`).join(' ') : ''
  const lowerPoints = hasBounds ? rows.map((row, index) => `${xFor(index)},${yFor(Number(row.lower_bound ?? row.predicted) || 0)}`).join(' ') : ''
  const bandPoints = hasBounds ? `${upperPoints} ${rows.map((row, index) => `${xFor(rows.length - index - 1)},${yFor(Number(rows[rows.length - index - 1].lower_bound ?? rows[rows.length - index - 1].predicted) || 0)}`).join(' ')}` : ''
  const activePoint = hoveredPoint == null ? null : pointData[hoveredPoint]
  const activeRatio = activePoint ? activePoint.x / width : 0
  const activeHeightRatio = activePoint ? activePoint.y / height : 0
  const tooltipSide = activeRatio < .16 ? 'left' : activeRatio > .84 ? 'right' : ''
  const tooltipPlacement = activeHeightRatio < .34 ? 'below' : 'above'
  const interactive = showYAxis || forecast

  return <div className={`chart-wrap${showYAxis ? ' chart-with-y-axis' : ''}`}><div className="chart-y-axis" aria-hidden="true"><span>{money(max)}</span><span>{money(mid)}</span><span>{money(min)}</span></div><div className="chart-plot"><svg viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" className={`${forecast ? 'forecast-line' : ''}${hasBounds ? ' has-bounds' : ''}`} onMouseLeave={() => setHoveredPoint(null)}><defs><linearGradient id="signalFill" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#4b806d" stopOpacity=".24" /><stop offset="1" stopColor="#4b806d" stopOpacity="0" /></linearGradient><linearGradient id="forecastBand" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#4b806d" stopOpacity=".18" /><stop offset="1" stopColor="#4b806d" stopOpacity=".05" /></linearGradient></defs><line x1="0" x2={width} y1="55" y2="55" stroke="#d6e0da" /><line x1="0" x2={width} y1="125" y2="125" stroke="#d6e0da" />{hasBounds ? <><polygon className="forecast-band" points={bandPoints} fill="url(#forecastBand)" /><polyline className="forecast-bound" points={upperPoints} fill="none" stroke="#9bb9aa" strokeWidth="1.2" strokeDasharray="4 4" /><polyline className="forecast-bound" points={lowerPoints} fill="none" stroke="#9bb9aa" strokeWidth="1.2" strokeDasharray="4 4" /></> : <polygon points={`0,${height} ${points} ${width},${height}`} fill="url(#signalFill)" />}<polyline points={points} fill="none" stroke="#4b806d" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />{interactive && pointData.map((point, index) => <g key={`${point.row.date}-${index}`} onMouseEnter={() => setHoveredPoint(index)}><circle className="chart-point-hit" cx={point.x} cy={point.y} r="16" /><circle className={`chart-point${hoveredPoint === index ? ' is-hovered' : ''}`} cx={point.x} cy={point.y} r={hasBounds ? '4' : '3.5'}><title>{`${String(point.row.date).slice(0, 10)} · 预测营收 ${money(point.row.revenue ?? point.row.predicted)}${hasBounds ? ` · 范围 ${money(point.row.lower_bound)} – ${money(point.row.upper_bound)}` : ''}`}</title></circle></g>)}</svg>{interactive && activePoint && <div className={`chart-tooltip-card${activePoint ? ' is-visible' : ''} ${tooltipSide ? `is-${tooltipSide}` : ''} is-${tooltipPlacement}`} style={{ left: `${activeRatio * 100}%`, top: `${activeHeightRatio * 100}%` }} role="status"><div className="chart-tooltip-head"><i /> <time>{String(activePoint.row.date).slice(0, 10)}</time></div><div className="chart-tooltip-main"><span>预测营收</span><strong>{money(activePoint.row.revenue ?? activePoint.row.predicted)}</strong></div>{hasBounds && <div className="chart-tooltip-range"><span>可能范围</span><b>{money(activePoint.row.lower_bound)} – {money(activePoint.row.upper_bound)}</b></div>}</div>}</div><div className="chart-labels"><span>{String(rows[0].date).slice(0, 10)}</span><span>{String(rows[rows.length - 1].date).slice(0, 10)}</span></div></div>
}

export function BarList({ rows, labelKey, valueKey, formatter = num }) { const values = rows?.map(row => Number(row[valueKey]) || 0) || []; const max = Math.max(...values, 1); return <div className="bar-list">{rows?.slice(0, 8).map((row, index) => <div className="bar-row" key={row[labelKey] || index}><div><span>{row[labelKey]}</span><b>{formatter(row[valueKey])}</b></div><div className="bar-track"><i style={{ width: `${Math.max(3, Number(row[valueKey]) / max * 100)}%` }} /></div></div>)}</div> }
export function Heatmap({ rows }) { if (!rows?.length) return <div className="empty">暂无热力数据</div>; const cols = Object.keys(rows[0]).filter(key => !['weekday', 'index'].includes(key)).sort((a, b) => Number(a) - Number(b)); const max = Math.max(...rows.flatMap(row => cols.map(col => Number(row[col]) || 0)), 1); return <div className="heatmap"><div className="heat-row heat-header"><span>星期</span>{cols.map(col => <span key={col}>{col}:00</span>)}</div>{rows.map((row, rowIndex) => { const weekday = row.weekday ?? row.index ?? `日期 ${rowIndex + 1}`; return <div className="heat-row" key={weekday}><b>{weekday}</b>{cols.map(col => <i key={`${weekday}-${col}`} title={`${weekday} ${col}:00 · ${num(row[col])} 单`} style={{ background: `rgba(75,128,109,${.06 + (Number(row[col]) || 0) / max * .72})` }}>{Number(row[col]) ? num(row[col]) : ''}</i>)}</div> })}</div> }
