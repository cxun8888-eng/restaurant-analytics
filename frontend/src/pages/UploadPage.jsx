import { useRef, useState } from 'react'
import { Card, DataTable, Metric } from '../components/ui'
import { readActiveAIConfig } from '../utils/ai'

export default function UploadPage({ quality, preview, onUpload, progress, onOpenSettings }) {
  const inputRef = useRef(null)
  const bypassNextPrompt = useRef(false)
  const [aiPromptOpen, setAiPromptOpen] = useState(false)
  const [pendingFile, setPendingFile] = useState(null)
  const processSteps = [
    ['01', '智能识别', '自动匹配当前平台字段'],
    ['02', '数据清洗', '处理缺失、重复和异常值'],
    ['03', '特征构建', '生成时间、品类、RFM 特征'],
    ['04', '经营分析', '输出指标、预测和行动建议']
  ]

  const requestUpload = file => {
    if (!file) return
    const bypass = bypassNextPrompt.current
    bypassNextPrompt.current = false
    if (!readActiveAIConfig() && !bypass) { setPendingFile(file); setAiPromptOpen(true); return }
    onUpload(file)
  }
  const openFilePicker = () => { bypassNextPrompt.current = true; inputRef.current?.click() }
  const continueWithoutAI = () => {
    setAiPromptOpen(false)
    if (pendingFile) { const file = pendingFile; setPendingFile(null); onUpload(file) } else openFilePicker()
  }

  return <main className="upload-page">
    <section className="upload-hero">
      <div className="hero-copy">
        <p className="hero-kicker"><span>01</span> / INGEST</p>
        <h2>把平台报表，变成看得懂的经营答案。</h2>
        <p className="hero-description">上传一份平台报表，系统会自动识别字段、清洗数据，并生成经营分析。</p>
        <div className="hero-stats"><div><strong>4</strong><span>个处理阶段</span></div><div><strong>50<span>MB</span></strong><span>单文件上限</span></div><div><strong>7</strong><span>分析模块</span></div></div>
      </div>
      <label className="dropzone" onClick={event => { if (bypassNextPrompt.current) return; if (!readActiveAIConfig()) { event.preventDefault(); setPendingFile(null); setAiPromptOpen(true) } }} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); bypassNextPrompt.current = false; const file = event.dataTransfer.files?.[0]; if (file) requestUpload(file) }}>
        <input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; requestUpload(file) }} />
        <span className="drop-orbit"><span className="drop-orbit-core">+</span></span>
        <b>放入你的订单账本</b>
        <span>拖放或点击选择一份文件</span>
        <small>.CSV / .XLSX / .XLS <i>·</i> MAX 50 MB</small>
        {progress > 0 && progress < 100 && <div className="progress"><i style={{ width: `${progress}%` }} /></div>}
      </label>
    </section>
    <section className="upload-grid">
      <Card title="数据如何变成信号" subtitle="每个阶段都会留下可追溯的结果">
        <div className="process-list">{processSteps.map(([no, title, text]) => <div key={no}><b>{no}</b><span><strong>{title}</strong><small>{text}</small></span><i className="process-line" /></div>)}</div>
      </Card>
      <Card title="准备一份订单账本" subtitle="支持当前平台字段，系统会自动匹配业务含义">
        <div className="format-note"><span className="format-mark">CSV</span><div><strong>订单明细文件</strong><small>订单号 · 时间 · 商品 · 金额等列名均可</small></div></div>
        <div className="format-note"><span className="format-mark xlsx">XLS</span><div><strong>Excel 工作簿</strong><small>支持中文、英文及当前平台导出字段</small></div></div>
        <p className="format-footnote">上传后查看“字段识别”，低置信度字段可手动确认。</p>
        <p className="format-footnote ai-optional-copy">AI 服务商为可选配置。未配置时仍可完成清洗和基础分析，配置后可获得更准确的字段判断和经营解读。</p>
      </Card>
    </section>
    {quality && <>
      <Card title="数据质量" subtitle={`已完成清洗 · ${quality.date_range || '当前数据集'}`}>
        <div className="metrics compact"><Metric label="原始行数" value={Number(quality.raw_rows || 0).toLocaleString()} detail="上传文件" /><Metric label="清洗后行数" value={Number(quality.clean_rows || 0).toLocaleString()} detail="分析数据" /><Metric label="订单数" value={Number(quality.total_orders || 0).toLocaleString()} detail="去重后" /><Metric label="金额异常" value={Number(quality.anomalies?.amount_outliers?.n_outliers || 0).toLocaleString()} detail="IQR 检测" accent /></div>
        {quality.issues?.length > 0 && <div className="notice">{quality.issues.join('；')}</div>}
        {quality.column_mapping?.length > 0 && <div className="field-mapping"><strong>字段识别</strong><div>{quality.column_mapping.filter(item => item.source !== '系统生成').map(item => <span key={`${item.source}-${item.field}`}><b>{item.source}</b><i>→</i>{item.label}</span>)}</div></div>}
        {quality.ai_assistance?.status === 'used' && <div className="ai-assist-note"><strong>AI 辅助识别</strong><span>{quality.ai_assistance.provider || '已配置服务商'} 已参与低置信度字段判断</span>{quality.ai_assistance.mapping?.map(item => <small key={`${item.source}-${item.field}`}>{item.source} → {item.field} · {Math.round(Number(item.confidence || 0) * 100)}%{item.reason ? ` · ${item.reason}` : ''}</small>)}</div>}
        {quality.ai_assistance?.status === 'fallback' && <div className="ai-assist-note muted"><strong>AI 辅助识别</strong><span>{quality.ai_assistance.warnings?.[0] || '已回退到规则识别'}</span></div>}
      </Card>
      <Card title="数据预览" subtitle={`前 ${preview?.rows?.length || 0} 行 · ${preview?.columns?.length || 0} 个字段`}>
        <DataTable rows={preview?.rows} columns={(preview?.columns || []).map(column => [column, column])} pageSize={10} />
      </Card>
    </>}
    {aiPromptOpen && <div className="ai-upload-modal-backdrop" role="presentation" onMouseDown={event => { if (event.target === event.currentTarget) { setAiPromptOpen(false); setPendingFile(null) } }}><section className="ai-upload-modal" role="dialog" aria-modal="true" aria-labelledby="ai-upload-title"><div className="ai-upload-modal-icon">✦</div><div><h2 id="ai-upload-title">建议先配置 AI 服务商</h2><p>配置后，懂单儿可以在字段含义不清时辅助识别，并为经营报告生成更具体的解读和建议。</p></div><div className="ai-upload-impact"><strong>如果暂不配置</strong><span>仍然可以上传和分析，系统会使用内置规则；遇到非标准表头时，可能需要手动确认，且不会生成 AI 解读。</span></div><div className="ai-upload-actions"><button className="ai-upload-primary" type="button" onClick={() => { setAiPromptOpen(false); setPendingFile(null); onOpenSettings?.() }}>去设置</button><button className="ai-upload-secondary" type="button" onClick={continueWithoutAI}>暂不配置，继续上传</button></div><button className="ai-upload-close" type="button" aria-label="关闭" onClick={() => { setAiPromptOpen(false); setPendingFile(null) }}>×</button></section></div>}
  </main>
}
