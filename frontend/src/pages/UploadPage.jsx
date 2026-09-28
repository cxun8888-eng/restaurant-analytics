import { useEffect, useMemo, useRef, useState } from 'react'
import { Card, DataTable, Metric } from '../components/ui'
import { readActiveAIConfig } from '../utils/ai'

const FIELD_OPTIONS = [
  ['order_id', '订单号'], ['order_time', '订单时间'], ['customer_id', '顾客编号'],
  ['product_name', '商品名称'], ['category', '商品分类'], ['quantity', '数量'],
  ['unit_price', '单价'], ['total_amount', '订单金额'], ['discount', '优惠金额'],
  ['actual_amount', '实付金额'], ['refund_amount', '退款金额'], ['platform', '平台'], ['status', '订单状态'],
  ['restaurant_name', '餐厅名称'], ['weekday_label', '星期/营业日'], ['rating', '评分'],
  ['preparation_time', '备餐时长'], ['delivery_duration', '配送时长']
]

const DATASET_TYPE_LABELS = {
  order_detail: '订单明细', restaurant_summary: '餐厅汇总', product_summary: '商品汇总', delivery_summary: '配送数据', unknown: '待确认'
}

function confidenceLabel(value) {
  const confidence = Number(value || 0)
  if (confidence >= .8) return { text: '高置信度', className: 'high' }
  if (confidence >= .6) return { text: '需确认', className: 'medium' }
  return { text: '低置信度', className: 'low' }
}

function initialMappings(inspection) {
  const rule = new Map((inspection?.rule_mapping || []).filter(item => item.source && item.source !== '系统生成').map(item => [item.source, item]))
  const ai = new Map((inspection?.suggestion?.mapping || []).filter(item => item.source).map(item => [item.source, item]))
  const proposed = (inspection?.columns || []).map(source => {
    const isTechnicalIndex = /^unnamed(?::|_|\s|$)/i.test(String(source).trim())
    const suggestion = ai.get(source)
    const fallback = rule.get(source)
    const selected = suggestion || fallback || {}
    if (isTechnicalIndex) {
      return {
        source,
        field: '',
        confidence: 0,
        method: '规则识别',
        reason: '这是 CSV 导出的技术索引列，不参与业务分析'
      }
    }
    return {
      source,
      field: selected.field || '',
      confidence: selected.confidence || 0,
      method: suggestion ? 'AI 建议' : fallback ? '规则识别' : '未识别',
      reason: suggestion?.reason || (fallback ? '内置规则根据表头和数据类型判断' : '没有可靠的自动映射建议')
    }
  })
  const owners = new Map()
  return proposed.map(item => {
    if (!item.field) return item
    if (!owners.has(item.field)) {
      owners.set(item.field, item.source)
      return item
    }
    return {
      ...item,
      field: '',
      confidence: 0,
      method: '冲突待确认',
      reason: `AI 建议与 ${owners.get(item.field)} 重复，已暂不采用，请确认真正的${FIELD_OPTIONS.find(([field]) => field === item.field)?.[1] || '标准字段'}`
    }
  })
}

function MappingReview({ inspection, onConfirm, onCancel, onReselect, onOpenSettings, busy }) {
  const [mappings, setMappings] = useState(() => initialMappings(inspection))
  const [submitError, setSubmitError] = useState('')
  useEffect(() => { setMappings(initialMappings(inspection)); setSubmitError('') }, [inspection])

  const profileBySource = useMemo(() => new Map((inspection?.profile?.columns || []).map(item => [item.name, item])), [inspection])
  const translationBySource = useMemo(() => new Map((inspection?.suggestion?.header_translations || []).filter(item => item?.source).map(item => [item.source, item])), [inspection])
  const ruleLabelBySource = useMemo(() => new Map((inspection?.rule_mapping || []).filter(item => item?.source && item.source !== '系统生成' && item?.label).map(item => [item.source, item.label])), [inspection])
  const selectedFields = new Set(mappings.filter(item => item.field).map(item => item.field))
  const unresolved = mappings.filter(item => !item.field)
  const suggestion = inspection?.suggestion || {}
  const aiEnabled = suggestion.status === 'ready' && Boolean(suggestion.provider)
  const analysisGate = inspection?.analysis_gate || inspection?.quality?.analysis_gate || {}
  const analysisBlocked = analysisGate.allowed === false
  const amountMapped = selectedFields.has('total_amount')
  const duplicateFields = mappings.reduce((duplicates, item) => {
    if (!item.field) return duplicates
    duplicates[item.field] = (duplicates[item.field] || 0) + 1
    return duplicates
  }, {})
  const hasDuplicateMapping = Object.values(duplicateFields).some(count => count > 1)

  const updateMapping = (source, field) => {
    setSubmitError('')
    setMappings(current => current.map(item => {
      if (item.source === source) return { ...item, field, confidence: field ? 1 : 0, method: '用户确认', reason: field ? '用户确认字段含义' : '用户选择忽略' }
      if (field && item.field === field) return { ...item, field: '', confidence: 0, method: '冲突待确认', reason: `已将 ${field} 分配给其他字段` }
      return item
    }))
  }

  const handleSubmit = async () => {
    setSubmitError('')
    if (analysisBlocked) {
      setSubmitError(analysisGate.reason || '当前文件不符合餐饮订单分析要求。')
      return
    }
    if (!amountMapped) {
      setSubmitError('当前文件没有可靠的订单金额字段，无法生成营业额分析。请上传包含订单金额/营业额/实收金额的订单报表。')
      return
    }
    if (hasDuplicateMapping) {
      setSubmitError('同一个标准字段只能绑定一个原始字段，请先处理重复映射。')
      return
    }
    try {
      await onConfirm(mappings.map(item => ({ source: item.source, field: item.field })))
    } catch (error) {
      setSubmitError(error?.message || '确认失败，请检查字段映射后重试。')
    }
  }

  return <div className="mapping-review-backdrop" role="presentation">
    <section className={`mapping-review${analysisBlocked ? ' is-blocked' : ''}`} role="dialog" aria-modal="true" aria-labelledby="mapping-review-title">
      <div className="mapping-review-head"><div><p className="eyebrow">02 / REVIEW</p><h2 id="mapping-review-title">确认字段识别</h2><p>AI 已先翻译全部表头，再结合整份文件的结构画像给出字段建议。</p></div><button className="mapping-review-close" type="button" onClick={onCancel} aria-label="取消检查">×</button></div>
      <div className="mapping-summary"><div><span>文件</span><strong>{inspection.filename}</strong></div><div><span>数据规模</span><strong>{Number(inspection.profile?.row_count || 0).toLocaleString()} 行 · {inspection.profile?.column_count || inspection.columns?.length || 0} 列</strong></div><div><span>报表判断</span><strong className={analysisBlocked ? 'mapping-status-blocked' : ''}>{analysisBlocked ? '不可分析' : DATASET_TYPE_LABELS[suggestion.dataset_type] || '待确认'}</strong></div><div><span>识别方式</span><strong>{aiEnabled ? `${suggestion.provider} AI 建议` : suggestion.status === 'fallback' ? '规则回退' : '内置规则识别'}</strong></div></div>
      {analysisBlocked && <div className="mapping-gate-alert" role="alert"><span className="mapping-gate-icon">!</span><div><strong>当前文件不能分析</strong><p>{analysisGate.reason || '当前文件不符合餐饮订单分析要求。'}</p></div></div>}
      {suggestion.warnings?.length > 0 && <div className="mapping-warning"><strong>AI 提醒</strong>{suggestion.warnings.map((warning, index) => <span key={`${warning}-${index}`}>{warning}</span>)}</div>}
      {!aiEnabled && <div className="mapping-info"><span>尚未启用 AI 服务商，本次使用内置规则；你仍可以手动修正每个字段。</span><button type="button" onClick={onOpenSettings}>去配置 AI</button></div>}
      <div className="mapping-table-wrap"><table className="mapping-table"><thead><tr><th>原始字段 / 中文释义</th><th>样例与数据画像</th><th>映射到标准字段</th><th>判断依据</th></tr></thead><tbody>{mappings.map(item => {
        const profile = profileBySource.get(item.source) || {}
        const confidence = confidenceLabel(item.confidence)
        const aiTranslation = translationBySource.get(item.source)
        const aiLabel = String(aiTranslation?.translated || '').trim()
        const ruleLabel = String(ruleLabelBySource.get(item.source) || '').trim()
        const translatedLabel = aiLabel && aiLabel !== item.source ? aiLabel : ruleLabel && ruleLabel !== item.source ? ruleLabel : ''
        const translationMethod = aiLabel && aiLabel !== item.source ? 'AI 译名' : translatedLabel ? '规则释义' : ''
        return <tr key={item.source}><td><strong>{item.source}</strong>{translatedLabel && <span className="mapping-translation"><em>{translationMethod}</em>{translatedLabel}</span>}<small>{profile.dtype || '未知类型'}</small></td><td><span className="mapping-examples">{(profile.examples || []).slice(0, 3).map(value => String(value ?? '—')).join(' · ') || '暂无非空样例'}</span><small>{Math.round(Number(profile.non_null_ratio || 0) * 100)}% 非空 · {Number(profile.unique_count || 0).toLocaleString()} 个不同值</small></td><td><select value={item.field} onChange={event => updateMapping(item.source, event.target.value)} aria-label={`${item.source} 的标准字段`}><option value="">忽略此字段</option>{FIELD_OPTIONS.map(([field, label]) => { const occupied = selectedFields.has(field) && item.field !== field; return <option key={field} value={field} disabled={occupied}>{occupied ? `${label}（已占用）` : label}</option> })}</select>{item.field && <small className={`mapping-confidence ${confidence.className}`}>{item.method} · {confidence.text}</small>}</td><td><span>{item.reason}</span></td></tr>
      })}</tbody></table></div>
      {unresolved.length > 0 && <p className="mapping-unresolved">{unresolved.length} 个字段暂未映射：{unresolved.slice(0, 5).map(item => item.source).join('、')}{unresolved.length > 5 ? '…' : ''}。这些原始字段仍会保留在预览中。</p>}
      {!analysisBlocked && !amountMapped && <p className="mapping-submit-hint">当前文件缺少可靠的订单金额。可以继续查看识别结果，但不能进入营业额分析。</p>}
      {submitError && <div className="mapping-submit-error" role="alert">{submitError}</div>}
      <div className="mapping-review-footer"><div className="mapping-review-actions"><button className="button secondary" type="button" onClick={onReselect} disabled={busy}>重新选择文件</button><button className="button" type="button" onClick={handleSubmit} disabled={busy || analysisBlocked || !amountMapped || hasDuplicateMapping}>{busy ? '正在生成分析…' : '确认字段并开始分析'}</button></div><p className="mapping-review-footnote">确认后才会保存正式数据集。临时文件将在 {Math.max(1, Math.round(Number(inspection.expires_in_seconds || 1800) / 60))} 分钟后自动清理。</p></div>
    </section>
  </div>
}

export default function UploadPage({ quality, preview, inspection, onUpload, onConfirm, onCancelInspection, busy, progress, onOpenSettings }) {
  const inputRef = useRef(null)
  const [pendingFile, setPendingFile] = useState(null)
  const processSteps = [
    ['01', '结构检查', '读取完整文件并生成数据画像'],
    ['02', '智能识别', 'AI 建议字段含义并标出风险'],
    ['03', '人工确认', '你决定哪些字段参与分析'],
    ['04', '经营分析', '清洗数据并输出经营答案']
  ]

  const requestUpload = (file, useRulesWithoutAI = false) => {
    if (!file || busy) return
    if (!useRulesWithoutAI && !readActiveAIConfig()) {
      setPendingFile(file)
      return
    }
    setPendingFile(null)
    onUpload(file)
  }
  const reselectFile = () => {
    if (busy) return
    onCancelInspection()
    // 在用户点击事件里同步触发 input，浏览器才会允许打开系统文件选择器。
    inputRef.current?.click()
  }

  return <main className="upload-page">
    <section className="upload-hero"><div className="hero-copy"><p className="hero-kicker"><span>01</span> / INGEST</p><h2>把平台报表，变成看得懂的经营答案。</h2><p className="hero-description">先理解整份报表，再由你确认字段，最后才保存并生成经营分析。</p><div className="hero-stats"><div><strong className="hero-stat-value">4</strong><span className="hero-stat-label">个处理阶段</span></div><div><strong className="hero-stat-value">50<small>MB</small></strong><span className="hero-stat-label">单文件上限</span></div><div><strong className="hero-stat-value hero-stat-word">全量</strong><span className="hero-stat-label">表头识别</span></div></div></div><label className={`dropzone${busy ? ' is-busy' : ''}`} onDragOver={event => { if (!busy) event.preventDefault() }} onDrop={event => { event.preventDefault(); const file = event.dataTransfer.files?.[0]; if (file) requestUpload(file) }}><input ref={inputRef} type="file" accept=".csv,.xlsx,.xls" disabled={busy} onChange={event => { const file = event.target.files?.[0]; event.target.value = ''; requestUpload(file) }} />{busy ? <div className="upload-processing" role="status" aria-live="polite"><span className="upload-processing-spinner" aria-hidden="true" /><b>正在处理数据…</b><span>正在读取完整文件并生成字段建议</span><div className="upload-processing-progress"><div className="progress"><i style={{ width: `${Math.max(progress, 8)}%` }} /></div><strong>{progress > 0 ? `${Math.round(progress)}%` : '读取中'}</strong></div><small>请稍候，文件会在后端本地完整处理</small></div> : <><span className="drop-orbit"><span className="drop-orbit-core">+</span></span><b>放入你的订单账本</b><span>拖放或点击选择一份文件</span><small>.CSV / .XLSX / .XLS <i>·</i> MAX 50 MB</small></>}</label></section>
    <section className="upload-grid"><Card title="数据如何变成信号" subtitle="每个阶段都会留下可追溯的结果"><div className="process-list">{processSteps.map(([no, title, text]) => <div key={no}><b>{no}</b><span><strong>{title}</strong><small>{text}</small></span><i className="process-line" /></div>)}</div></Card><Card title="准备一份订单账本" subtitle="支持 CSV、XLSX、XLS，AI 只接收结构画像和少量样例"><div className="format-note"><span className="format-mark"><b>CSV</b></span><div><strong>CSV 订单明细</strong><small>订单号 · 时间 · 商品 · 金额等列名均可</small></div></div><div className="format-note"><span className="format-mark xlsx"><b>XLSX</b></span><div><strong>Excel 工作簿</strong><small>支持中文、英文及当前平台导出字段</small></div></div><div className="format-note"><span className="format-mark xls"><b>XLS</b></span><div><strong>旧版 Excel 工作簿</strong><small>兼容旧版平台导出的 .xls 文件</small></div></div><p className="format-footnote">完整文件在后端本地处理，AI 不会接收整份明细。</p></Card></section>
    {quality && <><Card title={inspection ? '预检结果' : '数据质量'} subtitle={`${inspection ? '等待字段确认 · ' : '已完成清洗 · '}${quality.date_range || '当前数据集'}`}><div className="metrics compact"><Metric label="原始行数" value={Number(quality.raw_rows || 0).toLocaleString()} detail="上传文件" /><Metric label="清洗后行数" value={Number(quality.clean_rows || 0).toLocaleString()} detail={inspection ? '预检结果' : '分析数据'} /><Metric label="订单数" value={Number(quality.total_orders || 0).toLocaleString()} detail="去重后" /><Metric label="金额异常" value={Number(quality.anomalies?.amount_outliers?.n_outliers || 0).toLocaleString()} detail="IQR 检测" accent /></div>{quality.issues?.length > 0 && <div className="notice">{quality.issues.join('；')}</div>}{quality.column_mapping?.length > 0 && <div className="field-mapping"><strong>规则识别结果</strong><div>{quality.column_mapping.filter(item => item.source !== '系统生成').map(item => <span key={`${item.source}-${item.field}`}><b>{item.source}</b><i>→</i>{item.label}</span>)}</div></div>}{quality.ai_assistance && ['ready', 'confirmed', 'used', 'translated'].includes(quality.ai_assistance.status) && <div className="ai-assist-note"><strong>AI 表头翻译与字段建议</strong><span>{quality.ai_assistance.provider || '当前未启用服务商'} {inspection ? '已完成表头翻译并生成建议，请在上方确认' : '已参与表头翻译和字段判断'}</span></div>}{quality.ai_assistance?.status === 'fallback' && <div className="ai-assist-note muted"><strong>AI 表头翻译与字段建议</strong><span>{quality.ai_assistance.warnings?.[0] || '已回退到规则识别'}</span></div>}</Card><Card title="数据预览" subtitle={`${inspection ? '代表性样例 · ' : '前 '}${preview?.rows?.length || 0} 行 · ${preview?.columns?.length || 0} 个字段`}><DataTable rows={preview?.rows} columns={(preview?.columns || []).map(column => [column, column])} pageSize={10} /></Card></>}
    {inspection && <MappingReview inspection={inspection} onConfirm={onConfirm} onCancel={onCancelInspection} onReselect={reselectFile} onOpenSettings={onOpenSettings} busy={busy} />}
    {pendingFile && <div className="mapping-review-backdrop" role="presentation"><section className="ai-upload-prompt" role="dialog" aria-modal="true" aria-labelledby="ai-upload-prompt-title"><button className="mapping-review-close" type="button" onClick={() => setPendingFile(null)} aria-label="关闭提示">×</button><p className="eyebrow">AI / OPTIONAL</p><h2 id="ai-upload-prompt-title">尚未配置 AI 服务商</h2><p>配置 API Key 后，AI 可以辅助翻译表头和建议字段映射；也可以继续使用内置规则，核心分析功能不受影响。</p><div className="ai-upload-file"><span>准备检查</span><strong>{pendingFile.name}</strong></div><div className="ai-upload-actions"><button className="button secondary" type="button" onClick={() => requestUpload(pendingFile, true)}>暂不配置，使用内置规则</button><button className="button" type="button" onClick={() => { setPendingFile(null); onOpenSettings() }}>先配置 API Key</button></div><small>API Key 仅保存在当前浏览器，并只随单次 AI 请求发送。</small></section></div>}
  </main>
}
