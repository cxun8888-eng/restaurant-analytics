import { BarList, Card, LineChart, Metric, money, num } from '../components/ui'

export default function ScreenPage({ overview, products }) {
  const m = overview?.metrics || {}
  return <main className="screen-view"><div className="screen-hero"><div><p className="eyebrow">LIVE BUSINESS MONITOR</p><h2>餐饮经营实时大屏</h2><p>{m.date_range || '上传数据后查看实时指标'}</p></div><span className="live-dot">● 数据已连接</span></div><section className="metrics"><Metric label="总营收" value={money(m.total_revenue)} detail="统计周期" /><Metric label="总订单" value={num(m.total_orders)} detail="笔" /><Metric label="平均客单价" value={money(m.avg_order_value)} detail="每笔订单" /><Metric label="顾客数" value={num(m.n_customers)} detail="独立用户" /></section><section className="grid-2"><Card title="营收走势"><LineChart rows={overview?.trend} /></Card><Card title="营收概览"><BarList rows={overview?.platform} labelKey="platform" valueKey="total_revenue" formatter={money} /></Card></section><Card title="商品销量 Top 10"><BarList rows={products?.ranking} labelKey="product_name" valueKey="total_sold" /></Card></main>
}
