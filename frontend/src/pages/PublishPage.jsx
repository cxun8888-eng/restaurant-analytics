import { useEffect, useMemo, useState } from 'react'
import { num } from '../components/ui'
import { generatePublishCopy } from '../services/api'
import { AI_PROVIDER_LABELS, readActiveAIConfig } from '../utils/ai'
import { buildPublishHandoffUrl, formatPublishCopy, parsePublishTags, publicationReceiptId, PUBLISH_PLATFORMS } from '../utils/publishBridge'

const BRIDGE_REPOSITORY = 'https://github.com/cxun8888-eng/cross-platform-publish-review'
const METRIC_LABELS = { views: '浏览', likes: '点赞', comments: '评论', collects: '收藏', shares: '分享' }
const TONES = ['自然真诚', '新品上新', '活动转化', '门店故事']

function readStored(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback } catch { return fallback }
}

function platformFor(id) { return PUBLISH_PLATFORMS.find(item => item.id === id) || PUBLISH_PLATFORMS[0] }

function PhonePreview({ draft, tags, platform, author }) {
  const isWeibo = platform.id === 'weibo'
  return <div className={`publish-phone publish-phone-${platform.id}`}>
    <div className="publish-phone-status"><b>9:41</b><span><i /><i />▰</span></div>
    <div className="publish-phone-appbar"><span>{platform.code}</span><strong>{platform.label === '小红书' ? '发现' : platform.label === '微博' ? '关注' : '推荐'}</strong><i>⌕</i></div>
    <div className="publish-phone-stage">
      <div className="publish-dish-scene" aria-hidden="true"><i /><i /><i /><b>今日<br />门店</b></div>
      {!isWeibo && <div className="publish-phone-actions" aria-hidden="true"><b>{author.slice(0, 1)}</b><span>♥<small>赞</small></span><span>●<small>评论</small></span><span>◆<small>收藏</small></span><span>↗<small>分享</small></span></div>}
      <div className="publish-phone-copy">
        <span>@{author}</span>
        <h4>{draft.title.trim() || '一条值得被看见的门店内容'}</h4>
        <p>{draft.content.trim() || '正文会在这里实时预览。先在左侧写下门店此刻最值得告诉顾客的事，或请右侧 AI 助手起草。'}</p>
        <div>{tags.length ? tags.slice(0, 6).map(tag => <em key={tag}>#{tag}</em>) : <em>#门店日常</em>}</div>
      </div>
    </div>
    <div className="publish-phone-nav"><b>首页</b><span>发现</span><i>＋</i><span>消息</span><span>我</span></div>
  </div>
}

export default function PublishPage({ user, receipt, onReceiptHandled, onNotify, onOpenAISettings }) {
  const scope = String(user?.id || user?.email || 'local')
  const draftKey = `rodas-publish-draft:${scope}`
  const historyKey = `rodas-publish-history:${scope}`
  const bridgeKey = `rodas-publish-bridge-ready:${scope}`
  const platformKey = `rodas-publish-platform:${scope}`
  const initialDraft = useMemo(() => readStored(draftKey, { title: '', content: '', tags: '' }), [draftKey])
  const [draft, setDraft] = useState(initialDraft)
  const [history, setHistory] = useState(() => readStored(historyKey, []))
  const [bridgeReady, setBridgeReady] = useState(() => localStorage.getItem(bridgeKey) === '1')
  const [selectedPlatform, setSelectedPlatform] = useState(() => localStorage.getItem(platformKey) || 'douyin')
  const [copied, setCopied] = useState('')
  const [aiConfig, setAIConfig] = useState(readActiveAIConfig)
  const [aiBrief, setAIBrief] = useState('')
  const [aiTone, setAITone] = useState(TONES[0])
  const [aiBusy, setAIBusy] = useState(false)
  const [aiAngle, setAIAngle] = useState('')
  const tags = useMemo(() => parsePublishTags(draft.tags), [draft.tags])
  const previewCopy = useMemo(() => formatPublishCopy({ ...draft, tags }), [draft, tags])
  const platform = platformFor(selectedPlatform)
  const author = user?.display_name?.trim() || '懂单儿门店'
  const origin = window.location.origin
  const callbackPath = window.location.pathname || '/zh'

  useEffect(() => { localStorage.setItem(draftKey, JSON.stringify(draft)) }, [draft, draftKey])
  useEffect(() => { localStorage.setItem(bridgeKey, bridgeReady ? '1' : '0') }, [bridgeReady, bridgeKey])
  useEffect(() => { localStorage.setItem(platformKey, selectedPlatform) }, [platformKey, selectedPlatform])
  useEffect(() => {
    const refresh = () => setAIConfig(readActiveAIConfig())
    window.addEventListener('rodas:ai-config-changed', refresh)
    window.addEventListener('storage', refresh)
    window.addEventListener('focus', refresh)
    return () => { window.removeEventListener('rodas:ai-config-changed', refresh); window.removeEventListener('storage', refresh); window.removeEventListener('focus', refresh) }
  }, [])
  useEffect(() => {
    if (!receipt) return
    const record = { ...receipt, id: publicationReceiptId(receipt) }
    setHistory(current => {
      const next = [record, ...current.filter(item => item.id !== record.id)].slice(0, 20)
      localStorage.setItem(historyKey, JSON.stringify(next))
      return next
    })
    onNotify?.({ type: 'success', message: receipt.outcome === 'resolved' ? '平台回执已带回，作品信息已记录' : '平台操作已返回，请到官方页面确认最终状态' })
    onReceiptHandled?.()
  }, [historyKey, onNotify, onReceiptHandled, receipt])

  const updateDraft = (key, value) => setDraft(current => ({ ...current, [key]: value }))
  const notify = (type, message) => onNotify?.({ type, message })

  const copyText = async (value, key, label) => {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(key)
      window.setTimeout(() => setCopied(current => current === key ? '' : current), 1800)
      notify('success', `${label}已复制`)
    } catch {
      notify('error', `无法复制${label}，请手动选择文本`)
    }
  }

  const launch = () => {
    if (!bridgeReady) { notify('error', '请先安装并配置发布桥接扩展'); return }
    if (!draft.content.trim()) { notify('error', '请先填写准备公开的正文'); return }
    try {
      window.location.assign(buildPublishHandoffUrl({ platform: selectedPlatform, ...draft, tags }))
    } catch (error) {
      notify('error', error.message || '无法创建发布交接')
    }
  }

  const clearDraft = () => {
    if ((draft.title || draft.content || draft.tags) && !window.confirm('清空当前内容底稿？此操作无法撤销。')) return
    setDraft({ title: '', content: '', tags: '' })
    setAIAngle('')
    notify('success', '内容底稿已清空')
  }

  const saveDraft = () => {
    localStorage.setItem(draftKey, JSON.stringify(draft))
    notify('success', '草稿已保存在当前浏览器')
  }

  const downloadDraft = () => {
    if (!previewCopy) { notify('error', '请先填写发布文案'); return }
    const url = URL.createObjectURL(new Blob([previewCopy], { type: 'text/plain;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `${draft.title.trim() || '门店发布文案'}.txt`
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    notify('success', '发布文案下载已开始')
  }

  const createWithAI = async () => {
    const activeConfig = readActiveAIConfig()
    setAIConfig(activeConfig)
    if (!activeConfig) { notify('error', '请先在设置中配置并启用一个 AI 服务商'); onOpenAISettings?.(); return }
    if (aiBrief.trim().length < 2) { notify('error', '请告诉 AI 这次想写什么'); return }
    if ((draft.title.trim() || draft.content.trim()) && !window.confirm('AI 生成的文案会替换左侧当前标题、正文和话题，继续吗？')) return
    setAIBusy(true)
    try {
      const result = await generatePublishCopy({ platform: selectedPlatform, brief: aiBrief.trim(), tone: aiTone, title: draft.title, content: draft.content, tags }, activeConfig)
      setDraft({ title: result.draft?.title || '', content: result.draft?.content || '', tags: (result.draft?.tags || []).join('，') })
      setAIAngle(result.draft?.angle || '')
      notify('success', `${AI_PROVIDER_LABELS[result.provider] || 'AI'} 文案已填入左侧，请核对后发布`)
    } catch (error) {
      notify('error', error.message || 'AI 文案生成失败')
    } finally {
      setAIBusy(false)
    }
  }

  const clearHistory = () => {
    if (!history.length || !window.confirm('清空当前浏览器中的发布回执？')) return
    setHistory([])
    localStorage.removeItem(historyKey)
    notify('success', '发布回执已清空')
  }

  return <main className="publish-page">
    <section className="publish-heading">
      <div><p className="eyebrow">09 / PUBLISH DESK</p><h2>内容发布</h2><p>从一句门店灵感，到一条可核对、可交接的公开内容。</p></div>
      <div className={`publish-bridge-state${bridgeReady ? ' is-ready' : ''}`}><i /><span><strong>{bridgeReady ? '发布桥接已确认' : '发布桥接待配置'}</strong><small>{bridgeReady ? '文案可以交接到官方平台' : '先完成浏览器扩展设置'}</small></span></div>
    </section>

    <nav className="publish-platform-tabs" aria-label="选择目标发布平台">{PUBLISH_PLATFORMS.map((item, index) => <button type="button" role="tab" aria-selected={selectedPlatform === item.id} className={selectedPlatform === item.id ? 'is-active' : ''} onClick={() => setSelectedPlatform(item.id)} key={item.id}><span>{String(index + 1).padStart(2, '0')}</span><b>{item.label}</b><small>{item.destination}</small><i>{selectedPlatform === item.id ? '正在编辑' : '选择'}</i></button>)}</nav>

    <section className="publish-workbench">
      <div className="publish-compose-panel">
        <header className="publish-panel-head"><div><span>01 / 文案底稿</span><h3>发布到{platform.label}</h3><small>输入内容会同步显示在右侧预览</small></div><button type="button" onClick={clearDraft}>清空</button></header>
        <label className="publish-field"><span>标题 <small>{draft.title.length} / 200</small></span><input value={draft.title} maxLength={200} onChange={event => updateDraft('title', event.target.value)} placeholder="例如：晚市新菜单，今天先从这三道菜开始" /></label>
        <label className="publish-field publish-copy-field"><span>正文 <small>{draft.content.length} / 10,000</small></span><textarea value={draft.content} maxLength={10000} onChange={event => updateDraft('content', event.target.value)} placeholder="写下准备公开给顾客看的内容。不要填写手机号、预算、库存或内部审批信息。" /></label>
        <label className="publish-field"><span>话题标签 <small>{tags.length} / 30</small></span><input value={draft.tags} onChange={event => updateDraft('tags', event.target.value)} placeholder="新品，晚餐，城市探店（使用逗号分隔）" /></label>

        <div className="publish-editor-note"><b>接下来 3 步</b><ol><li>保存或复制这份公开文案</li><li>进入官方平台后选择图片并检查文案</li><li>完成发布后保持页面在前台，等待回执</li></ol></div>
        <div className="publish-editor-actions"><button type="button" className="secondary" onClick={saveDraft}>✓ 保存草稿</button><button type="button" className="secondary" onClick={downloadDraft}>↓ 下载文案</button><button type="button" className="primary" disabled={!draft.content.trim()} onClick={launch}>打开并导入{platform.label} ↗</button><button type="button" className="secondary" disabled={!previewCopy} onClick={() => copyText(previewCopy, 'copy', '完整文案')}>{copied === 'copy' ? '✓ 已复制' : '复制全文'}</button></div>
      </div>

      <div className="publish-preview-panel">
        <header className="publish-panel-head"><div><span>02 / 实时预览</span><h3>顾客看到的样子</h3></div><b><i /> LIVE</b></header>
        <PhonePreview draft={draft} tags={tags} platform={platform} author={author} />
        <p className="publish-preview-caption">预览只用于发布前核对文案；图片、封面与最终样式仍以{platform.label}官方页面为准。</p>
      </div>

      <aside className="publish-assistant-panel">
        <article className="publish-ai-card">
          <header><span className="publish-ai-mark">AI</span><div><h3>发布助手</h3><p>为当前{platform.label}生成标题、正文和话题。</p></div></header>
          <div className={`publish-ai-provider${aiConfig ? ' is-ready' : ''}`}><i /><span><b>{aiConfig ? `${AI_PROVIDER_LABELS[aiConfig.provider] || aiConfig.provider} 已接入` : '尚未配置 AI'}</b><small>{aiConfig?.modelId || '复用设置中的服务商与模型'}</small></span><button type="button" onClick={onOpenAISettings}>设置</button></div>
          <label className="publish-ai-brief"><span>你想写什么？</span><textarea value={aiBrief} maxLength={1000} onChange={event => setAIBrief(event.target.value)} placeholder={`例如：为周末晚市的新菜单写一条${platform.label}文案，语气轻松，突出三道新品`} /></label>
          <fieldset className="publish-tone-list"><legend>文案语气</legend><div>{TONES.map(tone => <button type="button" aria-pressed={aiTone === tone} className={aiTone === tone ? 'is-active' : ''} onClick={() => setAITone(tone)} key={tone}>{tone}</button>)}</div></fieldset>
          <button type="button" className="publish-generate-button" disabled={aiBusy || !aiBrief.trim()} onClick={createWithAI}>{aiBusy ? <><i className="publish-ai-spinner" /> 正在生成…</> : <><span>✦</span> 生成发布文案</>}</button>
          {aiAngle && <p className="publish-ai-angle"><b>本次写作角度</b>{aiAngle}</p>}
          <small className="publish-ai-disclaimer">AI 只会接收此处需求与当前底稿，不会自动发布，也不会保存你的密钥。</small>
        </article>

        <article className="publish-material-card"><span>素材准备</span><h3>图片仍由你选择</h3><p>懂单儿不读取平台相册或账号素材。进入官方发布页后，再选择封面、门店图和菜品图。</p><div><i>01</i><b>封面 / 菜品图</b><small>建议提前整理 3–6 张</small></div></article>
      </aside>
    </section>

    <div className="publish-privacy-note"><b>只交接公开文案</b><span>标题、正文和话题通过浏览器地址片段进入扩展；账号、Cookie、本地素材与 AI 密钥不会进入发布交接内容。</span></div>

    <section className="publish-lower-grid">
      <article className="publish-setup-card">
        <header><div><span>BRIDGE SETUP</span><h3>发布桥接设置</h3></div><a href={BRIDGE_REPOSITORY} target="_blank" rel="noreferrer">查看扩展源码 ↗</a></header>
        <ol><li><b>1</b><span><strong>构建并加载扩展</strong><small>Chrome / Edge 打开扩展管理页，加载仓库中的 browser-extension 目录。</small></span></li><li><b>2</b><span><strong>填写可信回调</strong><small>把下面的应用地址与回调路径保存到扩展弹窗。</small></span></li><li><b>3</b><span><strong>登录官方平台</strong><small>账号、素材、验证码和最终发布动作始终由你在官方页面确认。</small></span></li></ol>
        <div className="publish-config-values"><div><span>应用地址</span><code>{origin}</code><button type="button" onClick={() => copyText(origin, 'origin', '应用地址')}>{copied === 'origin' ? '已复制' : '复制'}</button></div><div><span>回调路径</span><code>{callbackPath}</code><button type="button" onClick={() => copyText(callbackPath, 'path', '回调路径')}>{copied === 'path' ? '已复制' : '复制'}</button></div></div>
        <label className="publish-ready-check"><input type="checkbox" checked={bridgeReady} onChange={event => setBridgeReady(event.target.checked)} /><span><strong>我已安装并按上方地址配置扩展</strong><small>这是本机确认项，懂单儿无法读取浏览器扩展状态。</small></span></label>
      </article>

      <article className="publish-history-card">
        <header><div><span>RETURN SLIPS</span><h3>最近回执</h3></div>{history.length > 0 && <button type="button" onClick={clearHistory}>清空</button>}</header>
        {!history.length ? <div className="publish-history-empty"><b>↩</b><strong>还没有平台回执</strong><span>从官方页面返回后，会在这里保留最多 20 条本机记录。</span></div> : <div className="publish-history-list">{history.map(item => {
          const itemPlatform = platformFor(item.platform)
          const metrics = Object.entries(item.metrics || {}).slice(0, 3)
          return <div className="publish-history-row" key={item.id}><b>{itemPlatform.code}</b><span><strong>{item.title || `${itemPlatform.label}发布操作`}</strong><small>{new Date(item.completedAt).toLocaleString('zh-CN')} · {item.outcome === 'resolved' ? '已带回公开作品信息' : '已触发，等待官方确认'}</small>{metrics.length > 0 && <em>{metrics.map(([key, value]) => `${METRIC_LABELS[key] || key} ${num(value)}`).join(' · ')}</em>}</span>{item.workUrl ? <a href={item.workUrl} target="_blank" rel="noreferrer">查看作品 ↗</a> : <i>无公开链接</i>}</div>
        })}</div>}
        <p className="publish-receipt-warning">平台回执没有签名，只用于流程提示，不能作为审核通过、计费或收入依据。</p>
      </article>
    </section>
  </main>
}
