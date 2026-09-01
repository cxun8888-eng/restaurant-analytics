import { useState } from 'react'
import { Button, Card, LineChart, money, num } from '../components/ui'

const pct = value => `${Number(value || 0).toFixed(1)}%`
const shortDate = value => value ? String(value).slice(5, 10).replace('-', ' / ') : '—'
const fullDate = value => value ? String(value).slice(0, 10) : '—'

function getForecastRead(rows) {
  if (!rows.length) return { tone: 'steady', title: '等待生成预测', detail: '点击运行预测，系统会把当前报表的经营节奏推演到未来。' }
  const first = Number(rows[0].predicted || 0)
  const last = Number(rows[rows.length - 1].predicted || 0)
  const average = rows.reduce((sum, row) => sum + Number(row.predicted || 0), 0) / rows.length
  const averageRange = rows.reduce((sum, row) => sum + Number(row.upper_bound || 0) - Number(row.lower_bound || 0), 0) / rows.length
  const change = first ? ((last - first) / first) * 100 : 0
  const spread = average ? averageRange / average : 0
  if (spread >= .9) return { tone: 'warning', title: '先按保守计划准备', detail: '未来每天的可能范围较宽，预测更适合用来安排备货和排班，不建议把单日数字当成承诺。' }
  if (change >= 3) return { tone: 'positive', title: '预计营收逐步抬升', detail: `从首日到末日预计提升 ${pct(change)}，可以提前为高峰日准备人手和备货。` }
  if (change <= -3) return { tone: 'warning', title: '预计营收逐步回落', detail: `从首日到末日预计下降 ${pct(Math.abs(change))}，建议先检查高频商品和流失订单。` }
  return { tone: 'steady', title: '预计经营节奏稳定', detail: '未来 14 天预测变化不大，适合维持当前节奏，重点观察可能范围较宽的日期。' }
}

function ForecastTable({ rows = [] }) {
  const [hoveredIndex, setHoveredIndex] = useState(null)
  const hovered = hoveredIndex == null ? null : rows[hoveredIndex]

  if (!rows.length) return <div className="empty">暂无预测数据</div>

  return <div className="forecast-table-shell">
    <div className="forecast-hover-note" aria-live="polite"><span className="forecast-hover-dot" />{hovered ? <><b>{fullDate(hovered.date)}</b><span>预测营收 {money(hovered.predicted)}</span><span>预计范围 {money(hovered.lower_bound)} – {money(hovered.upper_bound)}</span></> : <span>将鼠标移到任意日期，查看当天预测详情</span>}</div>
    <div className="forecast-table-scroll"><table className="forecast-table"><thead><tr><th>日期</th><th>预测营收</th><th>可能下限</th><th>可能上限</th><th>当天判断</th></tr></thead><tbody>{rows.map((row, index) => { const predicted = Number(row.predicted || 0); const lower = Number(row.lower_bound || 0); const upper = Number(row.upper_bound || 0); const spread = upper - lower; const label = spread > predicted * .9 ? '波动较大' : predicted >= Number(rows[0]?.predicted || 0) ? '保持增长' : '保持观察'; return <tr key={`${row.date}-${index}`} className={hoveredIndex === index ? 'is-hovered' : ''} onMouseEnter={() => setHoveredIndex(index)} title={`${fullDate(row.date)} · 预测营收 ${money(predicted)} · 可能范围 ${money(lower)} – ${money(upper)}`}><td>{fullDate(row.date)}</td><td><strong>{money(predicted)}</strong></td><td>{money(lower)}</td><td>{money(upper)}</td><td><span className={`forecast-row-label${label === '波动较大' ? ' warning' : ''}`}>{label}</span></td></tr> })}</tbody></table></div>
  </div>
}

function ForecastActions({ rows, averageRange, peak }) {
  const widest = rows.reduce((best, row) => (Number(row.upper_bound || 0) - Number(row.lower_bound || 0)) > (Number(best?.upper_bound || 0) - Number(best?.lower_bound || 0)) ? row : best, null)
  const actions = [
    { tone: 'sage', status: '备货', index: '01', title: peak ? `${shortDate(peak.date)} 可能是高峰日` : '识别高峰日', detail: peak ? `预估营收 ${money(peak.predicted)}，提前准备备货与排班。` : '生成预测后查看高峰安排。' },
    { tone: widest ? 'amber' : 'sage', status: '留量', index: '02', title: widest ? `${shortDate(widest.date)} 需要留余量` : '留意预测范围', detail: widest ? `当天可能相差 ${money(Number(widest.upper_bound || 0) - Number(widest.lower_bound || 0))}，计划按下限准备。` : `平均可能范围约 ${money(averageRange)}。` },
    { tone: 'sage', status: '复盘', index: '03', title: '每天对照实际营收', detail: '记录预测与实际的差距，系统会在下一次选择时重新比较方法。' }
  ]
  return <div className="forecast-action-list">{actions.map(action => <div className={`forecast-action-item ${action.tone}`} key={action.index}><span className="forecast-action-index">{action.index}</span><span><strong>{action.title}</strong><small>{action.detail}</small></span><span className="forecast-action-status" aria-label={`行动状态：${action.status}`}>{action.status}</span></div>)}</div>
}

function ModelComparison({ meta = {} }) {
  const candidates = meta.candidate_scores || []
  const scored = candidates.filter(item => item.smape != null)
  const maxError = Math.max(...scored.map(item => Number(item.smape) || 0), 1)
  const error = Number(meta.validation_smape)
  const confidence = meta.validation_smape == null ? ['参考', 'limited'] : error <= 20 ? ['高', 'high'] : error <= 40 ? ['中', 'medium'] : ['低', 'low']
  const limited = candidates.length <= 2
  return <section className="forecast-model-card"><div className="forecast-model-head"><div><span>智能选择过程</span><h3>为什么这次采用「{meta.method || '稳健参考'}」</h3><p>{meta.selection_note || '系统使用历史数据回测，优先选择误差更低的方法。'}</p></div><div className={`forecast-confidence ${confidence[1]}`}><small>预测可信度</small><strong>{confidence[0]}</strong><span>{meta.validation_smape != null ? `回测误差 ${pct(meta.validation_smape)}` : '历史样本较少'}</span></div></div>
    <div className="forecast-model-table"><div className="forecast-model-table-head"><span>比较方法</span><span>回测误差（越低越好）</span><span>结果</span></div>{candidates.map(candidate => <div className={`forecast-model-row${candidate.selected ? ' is-selected' : ''}`} key={candidate.key || candidate.method}><span><b>{candidate.method}</b><small>{candidate.selected ? '本次采用' : '参与比较'}</small></span><span className="forecast-model-error"><i style={{ width: candidate.smape == null ? '8%' : `${Math.max(8, Number(candidate.smape) / maxError * 100)}%` }} /><b>{candidate.smape == null ? '样本不足' : pct(candidate.smape)}</b></span><span>{candidate.selected ? '✓ 误差最低' : '未采用'}</span></div>)}</div>
    <div className="forecast-model-note"><strong>{limited ? '为什么只比较这些方法？' : '选择规则'}</strong><p>{limited ? '历史数据较少时，复杂模型容易过度拟合，所以先比较更稳健的周期基线与移动平均；累计到至少 21 天后会自动加入随机森林和梯度提升。' : '系统使用最近一段历史数据进行同口径回测，比较 sMAPE 和 MAE，优先采用相对误差更低的方法。每次运行都会重新选择。'}</p></div>
  </section>
}

export default function ForecastPage({ forecast, onForecast }) {
  const rows = forecast?.forecast || []
  const read = getForecastRead(rows)
  const total = rows.reduce((sum, row) => sum + Number(row.predicted || 0), 0)
  const average = rows.length ? total / rows.length : 0
  const averageRange = rows.length ? rows.reduce((sum, row) => sum + Number(row.upper_bound || 0) - Number(row.lower_bound || 0), 0) / rows.length : 0
  const peak = rows.reduce((best, row) => Number(row.predicted || 0) > Number(best?.predicted || 0) ? row : best, null)
  const validationError = forecast?.meta?.validation_smape ?? forecast?.meta?.mape
  const method = forecast?.meta?.method || '等待选择'
  const comparedModels = forecast?.meta?.candidate_scores?.length || 0
  const excludedAnomalies = Number(forecast?.meta?.excluded_anomalies || 0)
  const dateRange = rows.length ? `${fullDate(rows[0].date)} — ${fullDate(rows[rows.length - 1].date)}` : '尚未运行'

  return <main className="forecast-page">
    <section className="forecast-heading"><div><p className="eyebrow">06 / FORWARD SIGNALS</p><h2>智能预测</h2><p>把历史经营节奏，变成未来 14 天可以执行的安排。</p></div><div className={`forecast-context${forecast ? ' is-ready' : ''}`}><span className={`forecast-context-dot ${forecast ? 'ready' : ''}`} /><span className="forecast-context-state"><strong>{forecast ? '智能选择完成' : '等待预测'}</strong><small>{forecast ? `已比较 ${comparedModels || 1} 种方法` : '点击运行'}</small></span>{forecast && <span className="forecast-context-method"><small>本次采用</small><b>{method}</b></span>}</div></section>

    {!forecast && <section className="forecast-empty-card"><div className="forecast-empty-icon">↗</div><div><h3>先看未来，再决定今天</h3><p>系统会根据当前报表的日期、营收和周期节奏，生成未来 14 天的预测区间。</p></div><Button onClick={onForecast}>运行未来 14 天预测</Button></section>}

    {forecast && <>
      <section className={`forecast-hero ${read.tone}`}><div className="forecast-hero-copy"><span>当前预测判断</span><h3>{read.title}</h3><p>{read.detail}</p><div className="forecast-hero-meta"><span>预测窗口 <b>{rows.length} 天</b></span><span>覆盖日期 <b>{dateRange}</b></span><span>选择方式 <b>{forecast.meta?.selection_mode || '智能选择'}</b></span></div></div><div className="forecast-hero-side"><div><span>预计总营收</span><strong>{money(total)}</strong><small>未来 {rows.length} 天累计</small></div><div><span>日均预测</span><strong>{money(average)}</strong><small>每日平均</small></div><div><span>最高预估日</span><strong>{peak ? shortDate(peak.date) : '—'}</strong><small>{peak ? money(peak.predicted) : '暂无数据'}</small></div></div></section>

      <section className="forecast-metric-row"><div><span>平均可能范围</span><strong>{money(averageRange)}</strong><small>上下限平均差值</small></div><div><span>回测参考误差</span><strong>{validationError != null ? pct(validationError) : '—'}</strong><small>SMAPE，越低越稳定</small></div><div><span>预测最高日</span><strong>{peak ? money(peak.predicted) : '—'}</strong><small>{peak ? fullDate(peak.date) : '—'}</small></div><div className="is-clean"><span>数据清洗</span><strong>已排除 {num(excludedAnomalies)} 笔</strong><small>异常订单不参与预测</small></div></section>

      <ModelComparison meta={forecast.meta} />

      <section className="forecast-main-grid"><Card className="forecast-trend-card" title="未来 14 天走势" subtitle="实线是预测营收，虚线是可能上下限，浅色区域代表预测范围。" action={<span className="forecast-card-tag">悬停看当天</span>}><LineChart rows={rows} forecast /><div className="forecast-chart-legend"><span><i className="forecast-legend-main" />预测营收</span><span><i className="forecast-legend-bound" />可能范围（上限 / 下限）</span></div></Card><Card className="forecast-action-card" title="把预测变成动作" subtitle="预测不是结论，而是今天安排工作的提醒。"><ForecastActions rows={rows} averageRange={averageRange} peak={peak} /></Card></section>

      <Card className="forecast-detail-card" title="逐日预测明细" subtitle="14 天全部展开，悬停图表或表格行可查看当天的预测范围。" action={<span className="forecast-card-tag">完整窗口</span>}><ForecastTable rows={rows} /></Card>

    </>}
  </main>
}
