import { Card, LineChart, money, num } from '../components/ui'

const pct = value => `${Number(value || 0).toFixed(1)}%`
const shortDate = value => value ? String(value).slice(5, 10).replace('-', ' / ') : '—'

function PlatformBars({ rows = [] }) {
  if (!rows.length) return <div className="screen-empty">暂无平台数据</div>
  const max = Math.max(...rows.map(row => Number(row.total_revenue || 0)), 1)
  return <div className="screen-platform-list">{rows.slice(0, 5).map((row, index) => <div className="screen-platform-row" key={`${row.platform}-${index}`}><div><span className="screen-platform-name"><i>{String(index + 1).padStart(2, '0')}</i>{row.platform || '未命名平台'}</span><b>{money(row.total_revenue)}</b></div><div className="screen-platform-track"><em style={{ width: `${Math.max(4, Number(row.total_revenue || 0) / max * 100)}%` }} /></div><small>{pct(row.revenue_share)} · {num(row.total_orders)} 笔订单 · 客单价 {money(row.avg_order_value)}</small></div>)}</div>
}

function ProductLeaders({ rows = [] }) {
  if (!rows.length) return <div className="screen-empty">暂无商品数据</div>
  const max = Math.max(...rows.map(row => Number(row.total_sold || 0)), 1)
  return <div className="screen-product-list">{rows.slice(0, 6).map((row, index) => <div className="screen-product-row" key={`${row.product_name}-${index}`}><span className="screen-product-index">{String(index + 1).padStart(2, '0')}</span><span className="screen-product-copy"><strong>{row.product_name || '未命名商品'}</strong><small>{row.category || '未提供品类'} · {money(row.total_revenue)} 营收</small></span><b>{num(row.total_sold)}<small>份</small></b><i><em style={{ width: `${Math.max(5, Number(row.total_sold || 0) / max * 100)}%` }} /></i></div>)}</div>
}

function findPeakHour(rows = []) {
  let peak = null
  rows.forEach(row => Object.entries(row).forEach(([key, value]) => { if (!/^\d+$/.test(key)) return; const amount = Number(value || 0); if (!peak || amount > peak.amount) peak = { day: row.weekday || row.index || '高峰日', hour: key, amount } }))
  return peak
}

function ScreenHeatmap({ rows = [] }) {
  const columns = [...new Set(rows.flatMap(row => Object.keys(row).filter(key => /^\d+$/.test(key))))].sort((a, b) => Number(a) - Number(b))
  const values = rows.flatMap(row => columns.map(column => Number(row[column] || 0)))
  const max = Math.max(...values, 1)
  if (!rows.length || !columns.length) return <div className="screen-empty">暂无订单时段数据</div>
  return <div className="screen-heatmap"><div className={`screen-heatmap-grid columns-${columns.length}`} style={{ '--heat-columns': columns.length }}><div className="screen-heatmap-header"><span>星期</span>{columns.map(column => <span key={column}>{String(column).padStart(2, '0')}:00</span>)}</div>{rows.map((row, rowIndex) => { const dayLabel = row.weekday || row.index || `第 ${rowIndex + 1} 天`; return <div className="screen-heatmap-line" key={`${dayLabel}-${rowIndex}`}><b>{dayLabel}</b>{columns.map(column => { const amount = Number(row[column] || 0); const ratio = amount / max; return <div className={`screen-heatmap-cell${ratio > .62 ? ' is-strong' : ''}`} key={`${dayLabel}-${column}`} style={{ background: `rgba(75,128,109,${.08 + ratio * .66})` }}><strong>{amount ? num(amount) : '—'}</strong><small>单/时</small></div> })}</div> })}</div><div className="screen-heatmap-legend"><span>少</span><i /><i /><i /><i /><span>多</span><small>颜色越深，平均订单越多</small></div></div>
}

export default function ScreenPage({ overview, products }) {
  const metrics = overview?.metrics || {}
  const trend = overview?.trend || []
  const platforms = overview?.platform || []
  const heatmap = overview?.hourly_heatmap || []
  const ranking = products?.ranking || []
  const latest = trend[trend.length - 1]
  const topDay = trend.reduce((best, row) => Number(row.revenue || 0) > Number(best?.revenue || 0) ? row : best, null)
  const peakHour = findPeakHour(heatmap)
  const source = platforms[0]?.platform || '当前平台'
  const change = Number(metrics.dod_change || 0)

  return <main className="screen-page">
    <section className="screen-heading"><div><p className="eyebrow">07 / LIVE BUSINESS BOARD</p><h2>可视化大屏</h2><p>把平台报表浓缩成一眼能读懂的经营现场。</p></div><div className="screen-context"><span className="screen-context-dot" /><strong>数据已连接</strong><small>{metrics.date_range || '等待数据'}</small></div></section>

    <section className="screen-command"><div className="screen-command-copy"><span>LIVE BUSINESS MONITOR</span><h3>今天的经营，先看清再行动。</h3><p>{latest ? `最新一天实收 ${money(latest.revenue)}，${change >= 0 ? '较前一天有所上升' : '较前一天有所回落'}。` : '上传订单报表后，这里会实时汇总关键经营信号。'}</p><div className="screen-command-tags"><span>数据来源 <b>{source}</b></span><span>最新日期 <b>{shortDate(latest?.date)}</b></span><span>状态 <b>已更新</b></span></div></div><div className="screen-command-total"><span>周期总营收</span><strong>{money(metrics.total_revenue)}</strong><small>{metrics.date_range || '尚未生成周期'}</small><b>{change >= 0 ? '↗' : '↘'} {pct(Math.abs(change))}<em>最近一天变化</em></b></div></section>

    <section className="screen-metric-row"><div><span>总营收</span><strong>{money(metrics.total_revenue)}</strong><small>当前统计周期</small></div><div><span>有效订单</span><strong>{num(metrics.total_orders)}</strong><small>按订单编号去重</small></div><div><span>平均客单价</span><strong>{money(metrics.avg_order_value)}</strong><small>实收 ÷ 订单数</small></div><div><span>顾客数</span><strong>{num(metrics.n_customers)}</strong><small>独立顾客数量</small></div></section>

    <section className="screen-main-grid"><Card className="screen-trend-card" title="营收节奏" subtitle="按天查看周期波动，悬停曲线可查看当天营收。" action={<span className="screen-card-tag">{shortDate(latest?.date)} 更新</span>}><LineChart rows={trend.map(row => ({ date: row.date, revenue: row.revenue }))} showYAxis /><div className="screen-trend-foot"><span><i />每日营收</span><b>{topDay ? `${shortDate(topDay.date)} · ${money(topDay.revenue)}` : '暂无峰值数据'}<small>周期最高日</small></b></div></Card><Card className="screen-platform-card" title="平台贡献" subtitle="看清营收来自哪里，以及各平台的客单差异。"><PlatformBars rows={platforms} /></Card></section>

    <section className="screen-secondary-grid"><Card className="screen-heatmap-card" title="订单高峰时段" subtitle="每格显示该星期与时段的平均订单量，颜色越深代表越忙。"><div className="screen-heatmap-summary"><div><strong>{peakHour ? `${String(peakHour.hour).padStart(2, '0')}:00` : '—'}</strong><span>最忙时段</span></div><div><strong>{peakHour?.day || '—'}</strong><span>高峰日</span></div><p>高峰前提前准备人手和备货，减少临时忙乱。</p></div><ScreenHeatmap rows={heatmap} /></Card><Card className="screen-product-card" title="商品销量排行" subtitle="优先关注销量靠前、同时贡献营收的商品。"><ProductLeaders rows={ranking} /></Card></section>
  </main>
}
