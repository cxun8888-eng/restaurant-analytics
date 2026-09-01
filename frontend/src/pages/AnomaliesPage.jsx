import { useMemo, useState } from 'react'
import { money, num } from '../components/ui'

const STATUS = {
  pending: ['待复核', 'pending'],
  reviewed: ['已复核', 'reviewed'],
  normal: ['正常', 'normal'],
  needs_action: ['需要处理', 'needs-action']
}

const FILTERS = [['all', '全部'], ['金额异常', '金额'], ['数量异常', '数量'], ['折扣异常', '折扣'], ['组合异常', '组合']]

function ReviewButtons({ row, onReview }) {
  return <div className="anomaly-review-buttons" aria-label={`订单 ${row.order_id} 的复核状态`}>
    {[['reviewed', '已复核'], ['normal', '正常'], ['needs_action', '需要处理']].map(([value, label]) => <button type="button" className={row.review_status === value ? 'is-active' : ''} onClick={() => onReview?.(String(row.order_id), value)} key={value}>{label}</button>)}
  </div>
}

export default function AnomaliesPage({ data, onReview }) {
  const [filter, setFilter] = useState('all')
  const rows = data?.anomalies || []
  const statusCounts = data?.summary?.by_status || {}
  const visible = useMemo(() => filter === 'all' ? rows : rows.filter(row => String(row.anomaly_types || '').includes(filter)), [rows, filter])
  const resolved = Number(statusCounts.reviewed || 0) + Number(statusCounts.normal || 0)

  return <main className="anomalies-page">
    <section className="anomalies-heading"><div><p className="eyebrow">05 / ORDER CHECK</p><h2>异常诊断</h2><p>把可疑订单说清楚、复核完，再用于经营判断。</p></div><div className="anomalies-heading-state"><i /><span><strong>{rows.length ? `${num(rows.length)} 笔待判断` : '数据正常'}</strong><small>复核结果会自动保存</small></span></div></section>

    <section className="anomaly-summary-strip">
      <div className="anomaly-summary-lead"><span>诊断结论</span><h3>{rows.length ? '有少量订单偏离日常经营范围' : '没有发现明显异常订单'}</h3><p>{rows.length ? '系统已经给出原因，但是否属于真实业务仍由你确认。' : '当前订单可以正常用于趋势与预测分析。'}</p></div>
      <div><span>发现异常</span><strong>{num(rows.length)}</strong><small>占全部 {num(data?.total)} 笔订单</small></div>
      <div><span>尚未复核</span><strong>{num(statusCounts.pending || 0)}</strong><small>建议优先确认</small></div>
      <div><span>已完成判断</span><strong>{num(resolved)}</strong><small>已复核或确认正常</small></div>
      <div className="is-warning"><span>需要处理</span><strong>{num(statusCounts.needs_action || 0)}</strong><small>保留为处理清单</small></div>
    </section>

    <section className="anomaly-workspace">
      <div className="anomaly-toolbar"><div><h3>异常订单明细</h3><p>点击分类缩小范围，每一笔都显示判断依据。</p></div><div className="anomaly-filters">{FILTERS.map(([value, label]) => <button type="button" className={filter === value ? 'is-active' : ''} onClick={() => setFilter(value)} key={value}>{label}<span>{value === 'all' ? rows.length : rows.filter(row => String(row.anomaly_types || '').includes(value)).length}</span></button>)}</div></div>

      {!visible.length ? <div className="anomaly-empty"><span>✓</span><strong>这个分类没有待复核订单</strong><small>可以继续查看其他分类。</small></div> : <div className="anomaly-list">{visible.map(row => {
        const [statusLabel, statusTone] = STATUS[row.review_status] || STATUS.pending
        return <article className="anomaly-order" key={row.order_id}>
          <header><div><span className="anomaly-order-id">订单 {row.order_id}</span><span className={`anomaly-status ${statusTone}`}>{statusLabel}</span></div><time>{String(row.order_date || '').slice(0, 10) || '日期未知'}</time></header>
          <div className="anomaly-order-body"><div className="anomaly-order-copy"><div className="anomaly-type-row">{String(row.anomaly_types || '组合异常').split('、').map(type => <span className={`anomaly-type ${type.includes('折扣') ? 'discount' : type.includes('数量') ? 'quantity' : type.includes('金额') ? 'amount' : ''}`} key={type}>{type}</span>)}</div><h4>{row.anomaly_reason || '这笔订单的多项指标组合偏离常规。'}</h4><p>{row.products || '商品信息缺失'}<span>{row.platform || '平台未知'}</span></p></div><dl><div><dt>实付金额</dt><dd>{money(row.total_amount)}</dd></div><div><dt>商品数量</dt><dd>{num(row.total_quantity)} 份</dd></div><div><dt>优惠金额</dt><dd>{money(row.discount_total)}</dd></div><div><dt>风险程度</dt><dd className={row.severity === '高' ? 'is-high' : ''}>{row.severity || '中'}</dd></div></dl></div>
          <footer><span>你的判断</span><ReviewButtons row={row} onReview={onReview} /></footer>
        </article>
      })}</div>}
    </section>
  </main>
}
