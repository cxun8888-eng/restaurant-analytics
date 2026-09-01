import { Card, LineChart, money, num } from '../components/ui'

const pct = value => `${Number(value || 0).toFixed(1)}%`

function formatDate(value) {
  return value ? String(value).slice(5, 10).replace('-', ' / ') : '—'
}

function getTrendState(change, refundRate) {
  if (Number(refundRate || 0) >= 5) return { tone: 'warning', label: '退款需要留意', detail: `当前退款率 ${pct(refundRate)}，建议到“分析报告”查看订单明细。` }
  if (Number(change || 0) >= 5) return { tone: 'positive', label: '经营节奏在上升', detail: `最近一天营收较前一日增长 ${pct(change)}。` }
  if (Number(change || 0) <= -5) return { tone: 'warning', label: '最近一天有所回落', detail: `最近一天营收较前一日下降 ${pct(Math.abs(change))}，先观察趋势再调整。` }
  return { tone: 'steady', label: '经营节奏稳定', detail: '最近一天波动在正常范围内，可以继续观察高峰和商品结构。' }
}

function SignalList({ metrics, trend }) {
  const latest = trend?.[trend.length - 1]
  const topDay = trend?.reduce((best, row) => Number(row.revenue || 0) > Number(best?.revenue || 0) ? row : best, null)
  const items = [
    { label: '今日营收', value: money(metrics.today_revenue), note: `${num(metrics.today_orders)} 笔订单` },
    { label: '周期最高日', value: money(topDay?.revenue), note: topDay ? `${formatDate(topDay.date)} · ${num(topDay.orders)} 笔` : '暂无趋势数据' },
    { label: '最后更新', value: formatDate(latest?.date), note: '当前报表最新日期' }
  ]
  return <div className="overview-signal-list">{items.map(item => <div key={item.label}><span>{item.label}</span><strong>{item.value}</strong><small>{item.note}</small></div>)}</div>
}

export default function OverviewPage({ overview }) {
  const metrics = overview?.metrics || {}
  const trend = overview?.trend || []
  const state = getTrendState(metrics.dod_change, metrics.refund_rate)
  const source = overview?.platform?.[0]?.platform || '当前平台'
  const trendRows = trend.map(row => ({ date: row.date, revenue: row.revenue }))

  return <main className="overview-page">
    <section className="overview-heading">
      <div><p className="eyebrow">02 / OPERATING PULSE</p><h2>经营脉搏</h2><p>只看这一份平台报表，先判断经营状态，再决定要深入哪一层。</p></div>
      <div className="overview-context"><span className="overview-context-dot" /> <strong>{source}</strong><small>{metrics.date_range || '等待数据'}</small></div>
    </section>

    <section className="overview-command-card">
      <div className={`overview-state ${state.tone}`}><span className="overview-state-mark">{state.tone === 'positive' ? '↗' : state.tone === 'warning' ? '!' : '—'}</span><div><small>当前判断</small><h3>{state.label}</h3><p>{state.detail}</p></div></div>
      <SignalList metrics={metrics} trend={trend} />
    </section>

    <section className="overview-metric-row">
      <div><span>统计周期营收</span><strong>{money(metrics.total_revenue)}</strong><small>{metrics.date_range || '—'}</small></div>
      <div><span>有效订单</span><strong>{num(metrics.total_orders)}</strong><small>含退款订单记录</small></div>
      <div><span>平均客单价</span><strong>{money(metrics.avg_order_value)}</strong><small>营收 ÷ 订单数</small></div>
      <div className={Number(metrics.refund_rate || 0) >= 5 ? 'is-alert' : ''}><span>退款率</span><strong>{pct(metrics.refund_rate)}</strong><small>折扣率 {pct(metrics.avg_discount_rate)}</small></div>
    </section>

    <section className="overview-main-grid">
      <Card className="overview-trend-card" title="营收节奏" subtitle="按日查看当前平台的波动，曲线只回答一个问题：最近是在变好还是变慢？" action={<span className="overview-card-tag">周期趋势</span>}>
        <LineChart rows={trendRows} showYAxis />
        <div className="overview-trend-note"><span><i className="trend-dot" />每日营收</span><span><i className="trend-line" />趋势方向</span><b>{metrics.dod_change >= 0 ? '↗' : '↘'} {pct(Math.abs(metrics.dod_change))} <small>最近一天变化</small></b></div>
      </Card>
      <Card className="overview-reading-card" title="今天先看什么" subtitle="概览页不展开细节，只把下一步入口交给对应模块。">
        <div className="overview-reading-list"><a href="#products"><span className="reading-index">01</span><span><strong>商品分析</strong><small>确认营收变化是否由少数商品带动</small></span><b>→</b></a><a href="#users"><span className="reading-index">02</span><span><strong>用户分析</strong><small>查看订单变化背后的顾客结构</small></span><b>→</b></a><a href="#anomalies"><span className="reading-index">03</span><span><strong>异常诊断</strong><small>确认偏离常规的订单是否需要处理</small></span><b>→</b></a><a href="#forecast"><span className="reading-index">04</span><span><strong>智能预测</strong><small>判断当前节奏能否延续到未来</small></span><b>→</b></a><a href="#report"><span className="reading-index">05</span><span><strong>分析报告</strong><small>获取经营风险与行动建议的完整解释</small></span><b>→</b></a></div>
      </Card>
    </section>

    <section className="overview-secondary-grid">
      <Card title="经营构成" subtitle="把周期结果拆成四个可以被行动影响的信号。">
        <div className="overview-composition"><div><span>订单贡献</span><b>{num(metrics.total_orders)}<small>笔</small></b><i><em style={{ width: '78%' }} /></i></div><div><span>顾客规模</span><b>{num(metrics.n_customers)}<small>位</small></b><i><em style={{ width: '58%' }} /></i></div><div><span>客单水平</span><b>{money(metrics.avg_order_value)}</b><i><em style={{ width: '66%' }} /></i></div><div><span>退款压力</span><b>{pct(metrics.refund_rate)}</b><i><em className={Number(metrics.refund_rate || 0) >= 5 ? 'hot' : ''} style={{ width: `${Math.min(100, Math.max(6, Number(metrics.refund_rate || 0) * 10))}%` }} /></i></div></div>
      </Card>
      <Card title="本次分析口径" subtitle="让你知道这份报表里的数字是怎么来的。">
        <div className="overview-method-list"><div><b>01</b><span><strong>一份平台报表</strong><small>{source} · {metrics.date_range || '当前周期'}</small></span></div><div><b>02</b><span><strong>按订单去重</strong><small>同一订单的多道商品合并计算，不重复放大订单量。</small></span></div><div><b>03</b><span><strong>实付金额为主</strong><small>折扣与退款单独展示，方便判断真实经营压力。</small></span></div></div>
      </Card>
    </section>
  </main>
}
