import { useMemo, useState } from 'react'
import { Card, DataTable, money, num } from '../components/ui'

const pct = value => `${Number(value || 0).toFixed(1)}%`
const isUnknown = value => !value || ['其他', '未知', '未知品类', '未分类', 'none', 'null'].includes(String(value).trim().toLowerCase())

function Bars({ rows = [], labelKey, valueKey, formatter = num, empty = '暂无可用数据' }) {
  if (!rows.length) return <div className="empty">{empty}</div>
  const max = Math.max(...rows.map(row => Number(row[valueKey]) || 0), 1)
  return <div className="product-bars">{rows.slice(0, 7).map((row, index) => <div className="product-bar" key={`${row[labelKey] || 'row'}-${index}`}><div><span>{row[labelKey]}</span><b>{formatter(row[valueKey])}</b></div><i><em style={{ width: `${Math.max(4, Number(row[valueKey] || 0) / max * 100)}%` }} /></i></div>)}</div>
}

function priceBands(rows) {
  const groups = [['0–20 元', 0, 20], ['20–40 元', 20, 40], ['40–80 元', 40, 80], ['80 元以上', 80, Infinity]]
  return groups.map(([label, min, max]) => { const items = rows.filter(row => Number(row.avg_price) >= min && Number(row.avg_price) < max); return { label, product_count: items.length, total_revenue: items.reduce((sum, row) => sum + Number(row.total_revenue || 0), 0), total_sold: items.reduce((sum, row) => sum + Number(row.total_sold || 0), 0) } }).filter(row => row.product_count)
}

const TIME_METRICS = { quantity: ['销量', '份/日'], orders: ['订单数', '单/日'], revenue: ['营收', '元/日'] }

function ProductTimeExplorer({ rows = [] }) {
  const [metric, setMetric] = useState('quantity')
  const [period, setPeriod] = useState('全部')
  const [product, setProduct] = useState('全部商品')
  const [hovered, setHovered] = useState(null)
  const products = useMemo(() => [...new Set(rows.map(row => row.product_name))], [rows])
  const periodRows = rows.filter(row => row.period === period && (product === '全部商品' || row.product_name === product))
  const displayProducts = product === '全部商品' ? products.slice(0, 6) : [product]
  const hours = [...new Set(periodRows.map(row => Number(row.hour)))].sort((a, b) => a - b)
  const lookup = new Map(periodRows.map(row => [`${row.product_name}-${row.hour}`, row]))
  const max = Math.max(...periodRows.map(row => Number(row[metric]) || 0), 1)
  const peak = periodRows.reduce((best, row) => Number(row[metric] || 0) > Number(best?.[metric] || 0) ? row : best, null)
  const focusProduct = product === '全部商品' ? peak?.product_name : product
  const totalFor = targetPeriod => rows.filter(row => row.product_name === focusProduct && row.period === targetPeriod).reduce((sum, row) => sum + Number(row[metric] || 0), 0)
  const weekdayTotal = totalFor('工作日')
  const weekendTotal = totalFor('周末')
  const busierPeriod = weekendTotal > weekdayTotal ? '周末' : '工作日'
  const formatter = value => metric === 'revenue' ? money(value) : num(value)
  const suggestion = peak ? `${peak.product_name} 在 ${String(peak.hour).padStart(2, '0')}:00 左右达到高峰，建议提前 1–2 小时完成备货；${busierPeriod}的日均${TIME_METRICS[metric][0]}更高。` : '选择商品后，系统会根据高峰时段给出备货建议。'

  if (!rows.length) return <div className="empty">暂无商品时段数据</div>

  return <div className="product-time-explorer">
    <div className="product-time-controls"><label><span>查看商品</span><select value={product} onChange={event => setProduct(event.target.value)}><option>全部商品</option>{products.map(name => <option value={name} key={name}>{name}</option>)}</select></label><div><span>统计内容</span><div className="product-time-segments">{Object.entries(TIME_METRICS).map(([key, [label]]) => <button type="button" className={metric === key ? 'is-active' : ''} onClick={() => setMetric(key)} key={key}>{label}</button>)}</div></div><div><span>日期类型</span><div className="product-time-segments">{['全部', '工作日', '周末'].map(value => <button type="button" className={period === value ? 'is-active' : ''} onClick={() => setPeriod(value)} key={value}>{value}</button>)}</div></div></div>
    <div className="product-time-insight"><div><span>备货建议</span><strong>{peak ? `${peak.product_name} · ${String(peak.hour).padStart(2, '0')}:00` : '等待数据'}</strong><p>{suggestion}</p></div><div className="product-time-compare"><span>工作日 / 周末</span><b>{formatter(weekdayTotal)} <small>vs</small> {formatter(weekendTotal)}</b><p>{focusProduct || '当前商品'}在{busierPeriod}更集中</p></div>{hovered && <div className="product-time-hover"><span>当前格详情</span><strong>{hovered.product_name} · {String(hovered.hour).padStart(2, '0')}:00</strong><p>销量 {num(hovered.quantity)} 份 · {num(hovered.orders)} 单 · 营收 {money(hovered.revenue)}</p></div>}</div>
    <div className="product-time-scroll"><div className="product-time-grid" style={{ '--time-columns': Math.max(hours.length, 1) }}><div className="product-time-row product-time-header"><span>商品</span>{hours.map(hour => <span key={hour}>{String(hour).padStart(2, '0')}:00</span>)}</div>{displayProducts.map(name => <div className="product-time-row" key={name}><b title={name}>{name}</b>{hours.map(hour => { const row = lookup.get(`${name}-${hour}`) || { product_name: name, hour, quantity: 0, orders: 0, revenue: 0 }; const value = Number(row[metric] || 0); return <button type="button" className={`product-time-cell${peak?.product_name === name && Number(peak?.hour) === hour ? ' is-peak' : ''}`} onMouseEnter={() => setHovered(row)} onFocus={() => setHovered(row)} title={`${name} · ${String(hour).padStart(2, '0')}:00 · 销量 ${num(row.quantity)} 份 · ${num(row.orders)} 单 · 营收 ${money(row.revenue)}`} style={{ background: `rgba(75,128,109,${.06 + value / max * .72})` }} key={`${name}-${hour}`}><strong>{value ? formatter(value) : '—'}</strong><small>{TIME_METRICS[metric][1]}</small></button>})}</div>)}</div></div>
    <div className="product-time-legend"><span>少</span><i /><i /><i /><i /><span>多</span><small>悬停任意格，可同时查看销量、订单数和营收</small></div>
  </div>
}

export default function ProductsPage({ products }) {
  const ranking = products?.ranking || []
  const categories = products?.categories || []
  const rules = products?.association_rules || []
  const totalSold = ranking.reduce((sum, row) => sum + Number(row.total_sold || 0), 0)
  const totalRevenue = ranking.reduce((sum, row) => sum + Number(row.total_revenue || 0), 0)
  const averagePrice = totalSold ? totalRevenue / totalSold : 0
  const topThreeShare = ranking.slice(0, 3).reduce((sum, row) => sum + Number(row.revenue_share || 0), 0)
  const categoryRows = categories.filter(row => !isUnknown(row.category))
  const hasCategoryView = categoryRows.length > 1
  const structureRows = hasCategoryView ? categoryRows : priceBands(ranking)
  const structureValueKey = hasCategoryView ? 'total_revenue' : 'total_revenue'
  const structureLabelKey = hasCategoryView ? 'category' : 'label'
  const priceRank = ranking.filter(row => Number(row.avg_price) > 0).slice(0, 6)
  const riskRows = ranking.map(row => ({ ...row, refund_rate: row.order_count ? Number(row.refund_count || 0) / Number(row.order_count) * 100 : 0 })).filter(row => row.refund_rate >= 5 || Number(row.revenue_share || 0) < 2).sort((a, b) => b.refund_rate - a.refund_rate).slice(0, 5)
  const productTimeAnalysis = products?.product_time_analysis || []
  const sourceLabel = products?.platform || '当前平台报表'

  return <main className="products-page">
    <section className="products-heading"><div><p className="eyebrow">03 / MENU SIGNALS</p><h2>商品分析</h2><p>根据当前报表实际字段，识别商品贡献、价格结构与需要复盘的风险。</p></div><div className="products-context"><strong>{num(ranking.length)}</strong><span>个商品</span><small>{sourceLabel}</small></div></section>

    <section className="products-hero"><div className="products-hero-copy"><span>PRODUCT SNAPSHOT</span><h3>{ranking.length ? `这份报表记录了 ${num(ranking.length)} 个商品` : '等待商品数据进入'}</h3><p>{ranking.length ? `合计售出 ${num(totalSold)} 份，商品实收 ${money(totalRevenue)}。先从贡献集中度和价格结构开始判断。` : '上传订单明细后，系统会根据实际字段生成商品结构。'}</p></div><div className="products-hero-metrics"><div><span>商品实收</span><strong>{money(totalRevenue)}</strong></div><div><span>平均售出单价</span><strong>{money(averagePrice)}</strong></div><div><span>前三商品营收占比</span><strong>{pct(topThreeShare)}</strong></div></div></section>

    <section className="products-stat-row"><div><span>总销量</span><strong>{num(totalSold)}</strong><small>商品售出份数</small></div><div><span>商品平均价格</span><strong>{money(averagePrice)}</strong><small>实收 ÷ 销量</small></div><div><span>品类字段</span><strong>{hasCategoryView ? num(categoryRows.length) : '—'}</strong><small>{hasCategoryView ? '可用于品类结构' : '本报表未提供有效品类'}</small></div><div><span>组合规则</span><strong>{num(rules.length)}</strong><small>{rules.length ? '可进一步复盘' : '暂不生成建议'}</small></div></section>

    <section className="products-core-grid"><Card title="商品贡献" subtitle="按销量排序，右侧显示该商品贡献的营收比例。"><div className="product-contribution-list">{ranking.slice(0, 8).map((row, index) => <div key={row.product_name}><span className="product-position">{String(index + 1).padStart(2, '0')}</span><span><strong>{row.product_name}</strong><small>{row.category || '未提供品类'} · {num(row.order_count)} 笔订单</small></span><b>{num(row.total_sold)}<small>份</small></b><i><em style={{ width: `${Math.max(3, Math.min(100, Number(row.revenue_share || 0) * 3))}%` }} /></i><mark>{pct(row.revenue_share)}</mark></div>)}{!ranking.length && <div className="empty">暂无商品数据</div>}</div></Card><Card title={hasCategoryView ? '品类结构' : '价格带结构'} subtitle={hasCategoryView ? '当前报表提供有效品类字段。' : '未识别到足够品类信息，改用商品平均价格分组。'}><Bars rows={structureRows} labelKey={structureLabelKey} valueKey={structureValueKey} formatter={money} empty="暂无足够的结构数据" /></Card></section>

    <Card className="products-time-card" title="商品销售时段" subtitle="选择商品和经营指标，对比工作日与周末，并直接获得备货建议。" action={<span className="products-card-tag">可交互</span>}><ProductTimeExplorer rows={productTimeAnalysis} /></Card>

    <section className="products-diagnostic-grid"><Card title="价格与销量" subtitle="帮助判断高销量商品和高价值商品是否是同一批。"><div className="product-price-list">{priceRank.map(row => <div key={row.product_name}><span><strong>{row.product_name}</strong><small>销量 {num(row.total_sold)} 份</small></span><b>{money(row.avg_price)}<small>平均售出价</small></b><i><em style={{ width: `${Math.max(5, Math.min(100, Number(row.total_sold || 0) / Math.max(Number(ranking[0]?.total_sold || 1), 1) * 100))}%` }} /></i></div>)}{!priceRank.length && <div className="empty">报表缺少价格字段，暂不展示价格关系</div>}</div></Card><Card title="商品风险提示" subtitle="风险提示用于复盘，不直接替代下架或促销决定。"><div className="product-risk-list">{riskRows.map(row => <div key={row.product_name}><span className={row.refund_rate >= 5 ? 'risk-dot high' : 'risk-dot'} /> <span><strong>{row.product_name}</strong><small>{row.refund_rate >= 5 ? `退款率 ${pct(row.refund_rate)}` : `营收占比仅 ${pct(row.revenue_share)}`}</small></span><b>{row.refund_rate >= 5 ? '退款复盘' : '贡献偏低'}</b></div>)}{!riskRows.length && <div className="product-safe-state"><span>✓</span><p><strong>暂未发现明显风险</strong><small>当前报表中没有达到提示阈值的商品。</small></p></div>}</div></Card></section>

    {rules.length > 0 && <Card className="products-combination-card" title="商品组合机会" subtitle="仅展示当前报表中确实存在的同单购买关系。"><div className="bundle-list">{rules.slice(0, 8).map((rule, index) => <div key={`${rule.antecedent}-${rule.consequent}-${index}`}><span><strong>{rule.antecedent}</strong><i>＋</i><strong>{rule.consequent}</strong></span><small>支持度 {pct(Number(rule.support || 0) * 100)} · 置信度 {pct(Number(rule.confidence || 0) * 100)} · 提升度 {Number(rule.lift || 0).toFixed(2)}</small><b>→</b></div>)}</div></Card>}

    <details className="products-details"><summary><span>查看全部商品明细</span><small>搜索、排序和分页</small></summary><DataTable rows={ranking} columns={[["product_name", "商品"], ["category", "品类"], ["total_sold", "销量"], ["total_revenue", "营收"], ["avg_price", "平均售价"], ["order_penetration", "订单渗透率"], ["revenue_share", "营收占比"]]} /></details>
  </main>
}
