const PROVIDERS = { deepseek: 'DeepSeek', doubao: '豆包', openai: 'OpenAI', gemini: 'Gemini' }

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function cleanFilename(value) {
  return String(value || '当前订单报表').replace(/[\\/:*?"<>|]/g, '_')
}

function renderSignals(items) {
  if (!items?.length) return '<div class="export-empty">当前报告没有可展示的关键指标。</div>'
  return `<table class="signal-table" role="presentation"><tr>${items.slice(0, 4).map(item => {
    const tone = item.tone === 'warning' ? 'warning' : item.tone === 'positive' ? 'positive' : 'neutral'
    return `<td><div class="signal-card ${tone}"><span>${escapeHtml(item.label)}</span><strong>${escapeHtml(item.value)}</strong><small>${escapeHtml(item.detail)}</small></div></td>`
  }).join('')}</tr></table>`
}

function renderInsightItems(items, kind) {
  if (!items?.length) return `<div class="export-empty compact">暂无${kind === 'risk' ? '风险提醒' : '机会建议'}。</div>`
  return items.slice(0, 4).map((item, index) => `<div class="insight-item ${kind}">
    <table role="presentation"><tr><td class="insight-number">${String(index + 1).padStart(2, '0')}</td><td>
      <div class="insight-title">${escapeHtml(item.title)}${item.priority ? `<span class="priority ${item.priority === '高' ? 'high' : ''}">${escapeHtml(item.priority)}优先</span>` : ''}</div>
      <p>${escapeHtml(item.detail)}</p>${item.evidence ? `<small>数据依据　${escapeHtml(item.evidence)}</small>` : ''}
    </td></tr></table>
  </div>`).join('')
}

function renderActions(items) {
  if (!items?.length) return '<div class="export-empty compact">当前没有生成具体行动建议。</div>'
  return items.slice(0, 4).map((item, index) => `<div class="action-item">
    <table role="presentation"><tr><td class="action-number">${String(item.priority || index + 1).padStart(2, '0')}</td><td>
      <h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.detail)}</p>${item.reason ? `<small>${escapeHtml(item.reason)}</small>` : ''}
    </td><td class="action-arrow">→</td></tr></table>
  </div>`).join('')
}

export function buildReportExportHtml({ report, reportData, reportInfo, filename, includeAppendix = false }) {
  const provider = PROVIDERS[reportInfo?.provider] || reportInfo?.provider || '本地规则'
  const generatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
  const title = reportData?.title || '餐饮经营诊断报告'
  const summary = reportData?.summary || '系统已根据当前订单数据完成经营指标计算与本地规则分析，详细结果见报告附录。'
  const mode = reportData ? 'AI 经营解读' : '本地经营报告'
  const method = reportData?.method_note || reportInfo?.warning || '本报告基于当前数据集的统计结果生成，经营决策前请结合门店实际情况复核。'
  const source = cleanFilename(filename)

  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>${escapeHtml(title)}</title>
<style>
  @page { size: A4; margin: 12mm; }
  * { box-sizing: border-box; }
  body { margin: 0; color: #18392f; background: #edf2ef; font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .export-page { width: 100%; max-width: 210mm; min-height: 273mm; margin: 18px auto; padding: 15mm; background: #fffdf8; box-shadow: 0 10px 35px rgba(28,61,50,.12); }
  table { width: 100%; border-collapse: collapse; }
  .brand-table td { vertical-align: middle; }
  .brand-mark { display: inline-block; width: 42px; height: 42px; color: #fffdf8; background: #4c806c; border-radius: 11px; font: 700 18px/42px "Microsoft YaHei"; text-align: center; }
  .brand-copy { padding-left: 12px; }
  .brand-copy strong, .brand-copy span { display: block; }
  .brand-copy strong { color: #18392f; font-size: 16px; letter-spacing: .12em; }
  .brand-copy span { margin-top: 3px; color: #7b8e85; font-size: 9px; letter-spacing: .16em; }
  .report-meta { color: #84938c; font-size: 9px; line-height: 1.7; text-align: right; }
  .report-meta b { display: block; color: #4c806c; font-size: 10px; }
  .hero { margin: 22px 0 16px; padding: 24px 26px; color: #edf7f1; background: #214b3d; border-radius: 10px; }
  .hero-kicker { color: #9fc5b3; font: 700 9px/1.2 Consolas, monospace; letter-spacing: .18em; }
  .hero h1 { margin: 12px 0 8px; color: #fffdf8; font-family: SimSun, "Songti SC", serif; font-size: 27px; line-height: 1.25; }
  .hero p { max-width: 92%; margin: 0; color: #bfd7ca; font-size: 12px; line-height: 1.85; }
  .signal-table { margin: 0 -4px 18px; border-collapse: separate; border-spacing: 8px 0; }
  .signal-table td { width: 25%; vertical-align: top; }
  .signal-card { min-height: 92px; padding: 13px 14px; background: #f4f7f5; border: 1px solid #dae5df; border-top: 3px solid #4c806c; border-radius: 7px; }
  .signal-card.warning { border-top-color: #c46b57; background: #fff8f4; }
  .signal-card.positive { border-top-color: #4c806c; }
  .signal-card span, .signal-card strong, .signal-card small { display: block; }
  .signal-card span { color: #7a8c83; font-size: 9px; }
  .signal-card strong { margin: 8px 0 5px; color: #18392f; font-family: Consolas, "Microsoft YaHei"; font-size: 18px; }
  .signal-card small { color: #8c9993; font-size: 8px; line-height: 1.45; }
  .section-label { margin: 0 0 5px; color: #4c806c; font: 700 8px/1.2 Consolas, monospace; letter-spacing: .18em; }
  .section-title { margin: 0; color: #182f28; font-family: SimSun, "Songti SC", serif; font-size: 20px; }
  .section-subtitle { margin: 5px 0 14px; color: #89958f; font-size: 9px; }
  .insight-table { margin: 0 -6px 18px; border-collapse: separate; border-spacing: 12px 0; }
  .insight-table > tbody > tr > td { width: 50%; padding: 17px 17px 8px; vertical-align: top; background: #fbfcfa; border: 1px solid #dce6e0; border-radius: 8px; }
  .insight-item { padding: 11px 0; border-bottom: 1px solid #e2e9e5; page-break-inside: avoid; }
  .insight-item:last-child { border-bottom: 0; }
  .insight-item table td { vertical-align: top; }
  .insight-number { width: 27px; color: #4c806c; font: 700 9px Consolas, monospace; }
  .insight-title { color: #18392f; font-size: 11px; font-weight: 700; }
  .priority { float: right; padding: 2px 5px; color: #9b762e; background: #fff0c9; border-radius: 3px; font-size: 7px; font-weight: 500; }
  .priority.high { color: #a34b3b; background: #ffe8e2; }
  .insight-item p { margin: 5px 0 0; color: #687a72; font-size: 9px; line-height: 1.6; }
  .insight-item small { display: block; margin-top: 4px; color: #98a39d; font-size: 8px; line-height: 1.5; }
  .actions { margin: 0 0 18px; padding: 18px; background: #f4f7f5; border-left: 4px solid #4c806c; border-radius: 7px; }
  .action-item { padding: 11px 0; border-bottom: 1px solid #dae5df; page-break-inside: avoid; }
  .action-item:last-child { border-bottom: 0; }
  .action-item td { vertical-align: top; }
  .action-number { width: 34px; color: #4c806c; font: 700 10px Consolas, monospace; }
  .action-item h3 { margin: 0; color: #18392f; font-size: 11px; }
  .action-item p { margin: 5px 0 0; color: #60756b; font-size: 9px; line-height: 1.6; }
  .action-item small { display: block; margin-top: 4px; color: #94a199; font-size: 8px; }
  .action-arrow { width: 20px; color: #4c806c; font-size: 17px; text-align: right; }
  .method { padding: 12px 14px; color: #65786f; background: #edf4f0; border-radius: 5px; font-size: 9px; line-height: 1.65; }
  .method b { margin-right: 10px; color: #4c806c; }
  .footer { margin-top: 20px; padding-top: 11px; color: #93a098; border-top: 1px solid #dae5df; font-size: 8px; }
  .footer table td:last-child { text-align: right; }
  .appendix { margin-top: 18px; padding-top: 16px; border-top: 1px solid #dae5df; }
  .appendix h2 { margin: 0 0 6px; color: #18392f; font-family: SimSun, "Songti SC", serif; font-size: 23px; }
  .appendix > p { margin: 0 0 18px; color: #89958f; font-size: 9px; }
  .raw-report { padding: 18px; color: #455b51; background: #f7f9f7; border: 1px solid #dde6e1; border-radius: 7px; white-space: pre-wrap; word-break: break-word; font: 9px/1.75 "Microsoft YaHei", Arial, sans-serif; }
  .export-empty { padding: 20px; color: #8b9992; background: #f4f7f5; border: 1px dashed #ccdcd4; border-radius: 6px; font-size: 9px; text-align: center; }
  .export-empty.compact { padding: 14px; }
  @media print {
    body { background: #fff; }
    .export-page { max-width: none; min-height: 0; margin: 0; padding: 2mm; box-shadow: none; }
    .decision-page-tail { break-before: page; page-break-before: always; break-inside: avoid; page-break-inside: avoid; }
    .actions { break-inside: avoid; page-break-inside: avoid; }
    .appendix { padding-top: 4mm; }
  }
</style>
</head>
<body>
  <main class="export-page">
    <table class="brand-table" role="presentation"><tr><td style="width:48px"><span class="brand-mark">懂</span></td><td class="brand-copy"><strong>懂单儿</strong><span>RODAS · RESTAURANT ORDER DATA ANALYSIS</span></td><td class="report-meta"><b>${escapeHtml(mode)}</b>${escapeHtml(provider)} · ${escapeHtml(generatedAt)}<br>数据文件：${escapeHtml(source)}</td></tr></table>
    <section class="hero"><div class="hero-kicker">AI BUSINESS BRIEF / 经营决策简报</div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(summary)}</p></section>
    ${renderSignals(reportData?.signals)}
    <table class="insight-table" role="presentation"><tr>
      <td><div class="section-label">RISKS / 需要留意</div><h2 class="section-title">经营风险</h2><p class="section-subtitle">优先检查可能影响营收和复购的信号。</p>${renderInsightItems(reportData?.risks, 'risk')}</td>
      <td><div class="section-label">OPPORTUNITIES / 可以尝试</div><h2 class="section-title">增长机会</h2><p class="section-subtitle">从商品、用户和预测结果中寻找下一步。</p>${renderInsightItems(reportData?.opportunities, 'opportunity')}</td>
    </tr></table>
    <div class="decision-page-tail">
      <section class="actions"><div class="section-label">NEXT ACTION / 今天先做什么</div><h2 class="section-title">行动清单</h2><p class="section-subtitle">按优先级执行，并在下一周期复盘结果。</p>${renderActions(reportData?.actions)}</section>
      <div class="method"><b>分析口径</b>${escapeHtml(method)}</div>
      <footer class="footer"><table role="presentation"><tr><td>RODAS · 懂单儿　餐饮订单数据分析系统</td><td>© 2026 RODAS · 懂单儿 版权所有　|　未经授权不得转载</td></tr></table></footer>
    </div>
  </main>
  ${includeAppendix ? `<section class="export-page appendix"><div class="section-label">DATA APPENDIX / 数据附录</div><h2>完整本地分析原文</h2><p>以下内容保留系统计算口径，便于复核报告结论与数据依据。</p><div class="raw-report">${escapeHtml(report)}</div></section>` : ''}
</body>
</html>`
}

/** Word 对现代 CSS 卡片布局支持不稳定，因此使用固定宽度表格专用模板。 */
export function buildWordExportHtml({ report, reportData, reportInfo, filename }) {
  const provider = PROVIDERS[reportInfo?.provider] || reportInfo?.provider || '本地规则'
  const generatedAt = new Date().toLocaleString('zh-CN', { hour12: false })
  const title = reportData?.title || '餐饮经营诊断报告'
  const summary = reportData?.summary || '系统已根据当前订单数据完成经营指标计算与本地规则分析，详细结果见下方分析内容。'
  const source = cleanFilename(filename)
  const method = reportData?.method_note || reportInfo?.warning || '结论基于当前数据集统计结果，经营决策前请结合门店实际情况复核。'
  const signals = reportData?.signals?.slice(0, 4) || []
  const risks = reportData?.risks?.slice(0, 3) || []
  const opportunities = reportData?.opportunities?.slice(0, 3) || []
  const actions = reportData?.actions?.slice(0, 4) || []
  const signalCells = signals.length ? signals.map(item => `<td class="kpi-cell"><div class="kpi-label">${escapeHtml(item.label)}</div><div class="kpi-value">${escapeHtml(item.value)}</div><div class="kpi-detail">${escapeHtml(item.detail)}</div></td>`).join('') : '<td class="empty-cell">暂无关键指标</td>'
  const insightBlock = (items, type, emptyLabel) => items.length ? items.map((item, index) => `<div class="insight-item"><table role="presentation"><tr><td class="index">${String(index + 1).padStart(2, '0')}</td><td><div class="item-title">${escapeHtml(item.title)}</div><div class="item-detail">${escapeHtml(item.detail)}</div>${item.evidence ? `<div class="item-evidence">数据依据：${escapeHtml(item.evidence)}</div>` : ''}</td><td class="tag ${type === 'risk' && item.priority === '高' ? 'danger' : ''}">${type === 'risk' && item.priority ? escapeHtml(item.priority) : type === 'risk' ? '关注' : '机会'}</td></tr></table></div>`).join('') : `<div class="empty-cell">${emptyLabel}</div>`
  const actionBlock = actions.length ? actions.map((item, index) => `<div class="action-item"><table role="presentation"><tr><td class="action-index">${String(item.priority || index + 1).padStart(2, '0')}</td><td><div class="item-title">${escapeHtml(item.title)}</div><div class="item-detail">${escapeHtml(item.detail)}</div>${item.reason ? `<div class="item-evidence">${escapeHtml(item.reason)}</div>` : ''}</td><td class="action-arrow">→</td></tr></table></div>`).join('') : '<div class="empty-cell">当前没有生成具体行动建议。</div>'

  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${escapeHtml(title)}</title>
  <!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View><w:DoNotOptimizeForBrowser/></w:WordDocument></xml><![endif]-->
  <style>
    @page WordSection1 { size: 8.27in 11.69in; margin: .42in .48in .42in .48in; }
    div.WordSection1 { page: WordSection1; }
    body { margin: 0; color: #18392f; background: #ffffff; font-family: "Microsoft YaHei", "PingFang SC", Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; }
    table { width: 100%; border-collapse: collapse; table-layout: fixed; }
    td { vertical-align: top; }
    .header { margin-bottom: 12pt; border-bottom: 1pt solid #d5e1da; }
    .mark { width: 34pt; height: 34pt; color: #ffffff; background: #4c806c; font-size: 16pt; font-weight: bold; line-height: 34pt; text-align: center; }
    .brand { padding: 2pt 0 0 9pt; }
    .brand strong { display: block; color: #18392f; font-size: 13pt; letter-spacing: 1.5pt; }
    .brand span { display: block; margin-top: 2pt; color: #7d9187; font-size: 7.5pt; letter-spacing: 1.3pt; }
    .meta { color: #7b8e85; font-size: 8pt; line-height: 1.55; text-align: right; }
    .meta b { display: block; color: #4c806c; font-size: 8.5pt; }
    .hero { margin-bottom: 10pt; background: #214b3d; }
    .hero td { padding: 17pt 19pt; color: #edf7f1; }
    .kicker { color: #a6c9b7; font: bold 7.5pt Consolas, monospace; letter-spacing: 1.5pt; }
    h1 { margin: 8pt 0 5pt; color: #ffffff; font-family: SimSun, "Songti SC", serif; font-size: 22pt; line-height: 1.2; }
    .hero p { margin: 0; color: #c6ddd0; font-size: 10.5pt; line-height: 1.65; }
    .kpi-table { margin-bottom: 11pt; border-spacing: 5pt 0; border-collapse: separate; }
    .kpi-cell { padding: 9pt 10pt; background: #f2f6f3; border: 1pt solid #d9e5de; border-top: 3pt solid #4c806c; }
    .kpi-cell:nth-child(3) { border-top-color: #bd6a55; }
    .kpi-label { color: #70857a; font-size: 8.5pt; }
    .kpi-value { margin: 5pt 0 3pt; color: #18392f; font-family: Consolas, "Microsoft YaHei"; font-size: 15pt; font-weight: bold; }
    .kpi-detail { color: #81938a; font-size: 7.5pt; line-height: 1.4; }
    .section-kicker { margin: 0 0 3pt; color: #4c806c; font: bold 7.5pt Consolas, monospace; letter-spacing: 1.3pt; }
    .section-title { margin: 0 0 3pt; color: #18392f; font-family: SimSun, "Songti SC", serif; font-size: 15pt; }
    .section-note { margin: 0 0 7pt; color: #86958e; font-size: 8.5pt; }
    .panels { margin-bottom: 11pt; border-spacing: 6pt 0; border-collapse: separate; }
    .panel { padding: 11pt 12pt 5pt; background: #fbfcfa; border: 1pt solid #d9e5de; }
    .insight-item, .action-item { padding: 7pt 0; border-bottom: 1pt solid #e1e9e4; page-break-inside: avoid; }
    .insight-item:last-child, .action-item:last-child { border-bottom: 0; }
    .index, .action-index { width: 23pt; color: #4c806c; font: bold 8.5pt Consolas, monospace; }
    .item-title { color: #18392f; font-size: 10pt; font-weight: bold; }
    .item-detail { margin-top: 3pt; color: #667a70; font-size: 8.5pt; line-height: 1.5; }
    .item-evidence { margin-top: 3pt; color: #94a29b; font-size: 7.5pt; line-height: 1.4; }
    .tag { width: 25pt; height: 15pt; color: #9a782f; background: #fff1c9; font-size: 7pt; text-align: center; vertical-align: middle; }
    .tag.danger { color: #a14b3d; background: #ffe8e2; }
    .actions-panel { margin-bottom: 11pt; padding: 11pt 13pt 5pt; background: #f2f6f3; border-left: 4pt solid #4c806c; }
    .action-arrow { width: 17pt; color: #4c806c; font-size: 14pt; text-align: right; }
    .method { margin-bottom: 11pt; padding: 8pt 10pt; color: #61766b; background: #edf4f0; font-size: 8.5pt; line-height: 1.55; }
    .method b { margin-right: 8pt; color: #4c806c; }
    .footer { padding-top: 7pt; color: #80938a; border-top: 1pt solid #d5e1da; font-size: 7.5pt; }
    .footer td:last-child { text-align: right; }
    .empty-cell { padding: 12pt 0; color: #8d9b94; font-size: 8.5pt; text-align: center; }
  </style></head><body><div class="WordSection1">
    <table class="header" role="presentation"><tr><td style="width:34pt"><div class="mark">懂</div></td><td class="brand"><strong>懂单儿</strong><span>RODAS · RESTAURANT ORDER DATA ANALYSIS</span></td><td class="meta"><b>${escapeHtml(reportData ? 'AI 经营解读' : '本地经营报告')}</b>${escapeHtml(provider)} · ${escapeHtml(generatedAt)}<br>数据文件：${escapeHtml(source)}</td></tr></table>
    <table class="hero" role="presentation"><tr><td><div class="kicker">AI BUSINESS BRIEF / 经营决策简报</div><h1>${escapeHtml(title)}</h1><p>${escapeHtml(summary)}</p></td></tr></table>
    <table class="kpi-table" role="presentation"><tr>${signalCells}</tr></table>
    <table class="panels" role="presentation"><tr><td class="panel"><div class="section-kicker">RISKS / 需要留意</div><h2 class="section-title">经营风险</h2><p class="section-note">优先检查可能影响营收和复购的信号。</p>${insightBlock(risks, 'risk', '暂无风险提醒。')}</td><td class="panel"><div class="section-kicker">OPPORTUNITIES / 可以尝试</div><h2 class="section-title">增长机会</h2><p class="section-note">从商品、用户和预测结果中寻找下一步。</p>${insightBlock(opportunities, 'opportunity', '暂无机会建议。')}</td></tr></table>
    <div class="actions-panel"><div class="section-kicker">NEXT ACTION / 今天先做什么</div><h2 class="section-title">行动清单</h2><p class="section-note">按优先级执行，并在下一周期复盘结果。</p>${actionBlock}</div>
    <div class="method"><b>分析口径</b>${escapeHtml(method)}</div>
    <table class="footer" role="presentation"><tr><td>RODAS · 懂单儿　餐饮订单数据分析系统</td><td>© 2026 RODAS · 懂单儿 版权所有　|　未经授权不得转载</td></tr></table>
  </div></body></html>`
}
