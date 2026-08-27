import { Button, Card, DataTable, LineChart, num } from '../components/ui'

export default function ForecastPage({ forecast, anomalies, onForecast }) {
  return <main><section className="actions"><Button onClick={onForecast}>运行未来 14 天预测</Button><span>Isolation Forest 已检测 <b>{num(anomalies?.anomalies?.length)}</b> 笔异常订单</span></section>{forecast && <Card title="未来营收预测" subtitle={`${forecast.meta?.method || '随机森林回归'} · MAPE ${forecast.meta?.mape ? `${forecast.meta.mape}%` : '—'}`}><LineChart rows={forecast.forecast} forecast /><DataTable rows={forecast.forecast} columns={[["date", "日期"], ["predicted", "预测营收"], ["lower_bound", "95% 下界"], ["upper_bound", "95% 上界"]]} searchable={false} /></Card>}<Card title="异常订单检测" subtitle="基于金额、商品结构、数量和折扣等多维特征"><DataTable rows={anomalies?.anomalies} columns={[["order_id", "订单编号"], ["total_amount", "订单金额"], ["item_count", "商品种类"], ["total_quantity", "商品数量"], ["anomaly_score", "异常分数"]]} /></Card></main>
}
