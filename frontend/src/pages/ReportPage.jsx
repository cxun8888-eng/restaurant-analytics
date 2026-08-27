import { Button, Card } from '../components/ui'

export default function ReportPage({ report, onGenerate, onDownload }) {
  return <main><Card title="经营诊断报告" subtitle="汇总经营、商品、用户和预测分析" action={<div className="actions"><Button onClick={onGenerate}>生成报告</Button>{report && <Button secondary onClick={onDownload}>下载 Markdown</Button>}</div>}><div className="report-body">{report ? <pre>{report}</pre> : <div className="empty report-empty">点击“生成报告”，自动生成完整经营诊断。</div>}</div></Card></main>
}
