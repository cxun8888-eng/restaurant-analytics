import { Button, Card } from '../components/ui'

const providerLabels = { deepseek: 'DeepSeek', doubao: '豆包', openai: 'OpenAI', gemini: 'Gemini' }

function InsightList({ items = [], type }) {
  if (!items.length) return <div className="report-insight-empty">当前没有足够依据生成{type === 'risk' ? '风险' : '机会'}提醒。</div>
  return <div className="report-insight-list">{items.map((item, index) => <div className="report-insight-item" key={`${item.title}-${index}`}><span className="report-insight-index">{String(index + 1).padStart(2, '0')}</span><span><strong>{item.title}</strong><small>{item.detail}</small>{item.evidence && <em>依据：{item.evidence}</em>}</span>{item.priority && <b className={`report-priority ${item.priority === '高' ? 'high' : item.priority === '低' ? 'low' : ''}`}>{item.priority}</b>}</div>)}</div>
}

function ActionList({ items = [] }) {
  if (!items.length) return <div className="report-insight-empty">当前没有生成具体行动建议。</div>
  return <div className="report-action-list">{items.map((item, index) => <div className="report-action-item" key={`${item.title}-${index}`}><b>{String(item.priority || index + 1).padStart(2, '0')}</b><span><strong>{item.title}</strong><small>{item.detail}</small><em>{item.reason}</em></span><i>→</i></div>)}</div>
}

export default function ReportPage({ report, reportData, reportInfo, onGenerate, onDownload, busy = false }) {
  const ai = reportData
  const isAI = reportInfo?.mode === 'ai' && ai
  const provider = providerLabels[reportInfo?.provider] || reportInfo?.provider
  return <main className="report-page">
    <section className="report-heading"><div><p className="eyebrow">08 / DECISION BRIEF</p><h2>分析报告</h2><p>把经营数据翻译成今天就能执行的决定。</p></div><div className="report-heading-actions"><div className={`report-mode${isAI ? ' ai' : ''}`}><span className="report-mode-dot" /><strong>{isAI ? 'AI 经营解读' : '本地数据报告'}</strong><small>{isAI ? `${provider || 'AI'} 已参与` : '无需联网也可生成'}</small></div>{report && <Button disabled={busy} onClick={onGenerate}>{busy && <span className="report-button-spinner" aria-hidden="true" />}{busy ? '正在生成…' : '重新生成解读'}</Button>}{report && <details className="report-download-menu"><summary className="button secondary">下载报告 <span>⌄</span></summary><div><button type="button" onClick={() => onDownload('md')}>Markdown <small>.md</small></button><button type="button" onClick={() => onDownload('word')}>Word 文档 <small>.doc</small></button><button type="button" onClick={() => onDownload('pdf')}>PDF 文件 <small>打印保存</small></button></div></details>}</div></section>

    {busy && <div className="report-progress" role="status" aria-live="polite"><span className="report-progress-spinner" aria-hidden="true" /><div><strong>正在生成经营报告</strong><small>先整理本地经营指标，再生成 AI 解读，请稍候几秒。</small></div></div>}

    {!report && <section className="report-empty-card"><div className="report-empty-icon">✦</div><div><h3>让 AI 帮你读懂这份报表</h3><p>系统会先在本地算好经营指标，再让 AI 提炼结论、风险、机会和今日行动。整份订单明细不会发送给 AI。</p><div className="report-empty-tags"><span>本地计算指标</span><span>AI 解读摘要</span><span>数据依据可追溯</span></div></div><div className="report-empty-action"><Button disabled={busy} onClick={onGenerate}>{busy && <span className="report-button-spinner" aria-hidden="true" />}{busy ? '正在生成…' : '生成经营报告'}</Button><small>本地计算完成后自动生成 AI 解读</small></div></section>}

    {report && isAI && <>
      <section className="report-ai-hero"><div><span>AI BUSINESS BRIEF</span><h3>{ai.title}</h3><p>{ai.summary}</p></div><div className="report-ai-hero-badge"><strong>AI</strong><small>{provider || '智能助手'}</small><em>基于本地统计摘要</em></div></section>

      <section className="report-signal-row">{(ai.signals || []).slice(0, 4).map((signal, index) => <div className={signal.tone === 'warning' ? 'warning' : signal.tone === 'positive' ? 'positive' : ''} key={`${signal.label}-${index}`}><span>{signal.label}</span><strong>{signal.value}</strong><small>{signal.detail}</small></div>)}</section>

      <section className="report-insight-grid"><Card title="需要留意" subtitle="AI 从当前数据中提炼的风险信号。"><InsightList items={ai.risks} type="risk" /></Card><Card title="可以尝试" subtitle="基于商品、用户、平台和预测结果的机会。"><InsightList items={ai.opportunities} type="opportunity" /></Card></section>

      <Card className="report-actions-card" title="今天先做什么" subtitle="按优先级排列，建议逐项核对数据依据后执行。"><ActionList items={ai.actions} /></Card>
      <div className="report-method-note"><span>解读口径</span><p>{ai.method_note}</p></div>
    </>}

    {report && !isAI && <Card className="report-fallback-card" title="经营诊断报告" subtitle={reportInfo?.warning || '本次使用本地规则生成，指标和结论均来自当前数据集。'}><pre>{report}</pre></Card>}
    {report && <details className="report-raw"><summary><span>查看完整报告原文</span><small>Markdown / Word / PDF 可导出</small></summary><pre>{report}</pre></details>}
  </main>
}
