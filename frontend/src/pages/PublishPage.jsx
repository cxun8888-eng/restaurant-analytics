import { useEffect, useMemo, useState } from 'react'
import { num } from '../components/ui'
import { buildPublishHandoffUrl, formatPublishCopy, parsePublishTags, publicationReceiptId, PUBLISH_PLATFORMS } from '../utils/publishBridge'

const BRIDGE_REPOSITORY = 'https://github.com/cxun8888-eng/cross-platform-publish-review'
const METRIC_LABELS = { views: '浏览', likes: '点赞', comments: '评论', collects: '收藏', shares: '分享' }

function readStored(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback } catch { return fallback }
}

function platformFor(id) { return PUBLISH_PLATFORMS.find(item => item.id === id) || PUBLISH_PLATFORMS[0] }

export default function PublishPage({ user, receipt, onReceiptHandled, onNotify }) {
  const scope = String(user?.id || user?.email || 'local')
  const draftKey = `rodas-publish-draft:${scope}`
  const historyKey = `rodas-publish-history:${scope}`
  const bridgeKey = `rodas-publish-bridge-ready:${scope}`
  const initialDraft = useMemo(() => readStored(draftKey, { title: '', content: '', tags: '' }), [draftKey])
  const [draft, setDraft] = useState(initialDraft)
  const [history, setHistory] = useState(() => readStored(historyKey, []))
  const [bridgeReady, setBridgeReady] = useState(() => localStorage.getItem(bridgeKey) === '1')
  const [copied, setCopied] = useState('')
  const tags = useMemo(() => parsePublishTags(draft.tags), [draft.tags])
  const previewCopy = useMemo(() => formatPublishCopy({ ...draft, tags }), [draft, tags])
  const origin = window.location.origin
  const callbackPath = window.location.pathname || '/zh'

  useEffect(() => { localStorage.setItem(draftKey, JSON.stringify(draft)) }, [draft, draftKey])
  useEffect(() => { localStorage.setItem(bridgeKey, bridgeReady ? '1' : '0') }, [bridgeReady, bridgeKey])
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

  const launch = platform => {
    if (!bridgeReady) { notify('error', '请先安装并配置发布桥接扩展'); return }
    if (!draft.content.trim()) { notify('error', '请先填写准备公开的正文'); return }
    try {
      window.location.assign(buildPublishHandoffUrl({ platform, ...draft, tags }))
    } catch (error) {
      notify('error', error.message || '无法创建发布交接')
    }
  }

  const clearDraft = () => {
    if ((draft.title || draft.content || draft.tags) && !window.confirm('清空当前内容底稿？此操作无法撤销。')) return
    setDraft({ title: '', content: '', tags: '' })
    notify('success', '内容底稿已清空')
  }

  const clearHistory = () => {
    if (!history.length || !window.confirm('清空当前浏览器中的发布回执？')) return
    setHistory([])
    localStorage.removeItem(historyKey)
    notify('success', '发布回执已清空')
  }

  return <main className="publish-page">
    <section className="publish-heading">
      <div><p className="eyebrow">09 / PUBLISH DESK</p><h2>内容发布</h2><p>写一次公开内容，再逐个平台完成素材、账号和发布确认。</p></div>
      <div className={`publish-bridge-state${bridgeReady ? ' is-ready' : ''}`}><i /><span><strong>{bridgeReady ? '发布桥接已确认' : '发布桥接待配置'}</strong><small>{bridgeReady ? '可以交接公开文案' : '先完成浏览器扩展设置'}</small></span></div>
    </section>

    <section className="publish-workbench">
      <div className="publish-compose-sheet">
        <header><div><span>CONTENT TICKET</span><h3>准备一条门店内容</h3></div><button type="button" onClick={clearDraft}>清空底稿</button></header>
        <label className="publish-field"><span>标题 <small>{draft.title.length} / 200</small></span><input value={draft.title} maxLength={200} onChange={event => updateDraft('title', event.target.value)} placeholder="例如：晚市新菜单，今天先从这三道菜开始" /></label>
        <label className="publish-field publish-copy-field"><span>正文 <small>{draft.content.length} / 10,000</small></span><textarea value={draft.content} maxLength={10000} onChange={event => updateDraft('content', event.target.value)} placeholder="写下准备公开给顾客看的内容。不要填写手机号、预算、库存或内部审批信息。" /></label>
        <label className="publish-field"><span>话题标签 <small>{tags.length} / 30</small></span><input value={draft.tags} onChange={event => updateDraft('tags', event.target.value)} placeholder="新品，晚餐，城市探店（使用逗号分隔）" /></label>
        <div className="publish-privacy-note"><b>只交接公开文案</b><span>标题、正文和话题通过浏览器地址片段进入扩展；账号、Cookie和本地素材不会进入懂单儿。</span></div>
      </div>

      <aside className="publish-dispatch-rail">
        <div className="publish-rail-head"><span>出单口 / DISPATCH</span><strong>{draft.content.trim() ? '文案已就绪' : '等待正文'}</strong></div>
        <article className="publish-preview-ticket">
          <div className="publish-ticket-pin" aria-hidden="true" />
          <span className="publish-ticket-label">顾客将看到</span>
          <h3>{draft.title.trim() || '标题会显示在这里'}</h3>
          <p>{draft.content.trim() || '正文预览会随着左侧输入实时更新。'}</p>
          <div className="publish-preview-tags">{tags.length ? tags.map(tag => <span key={tag}>#{tag}</span>) : <small>还没有话题标签</small>}</div>
          <footer><span>草稿保存在当前浏览器</span><button type="button" disabled={!previewCopy} onClick={() => copyText(previewCopy, 'copy', '完整文案')}>{copied === 'copy' ? '已复制' : '复制全文'}</button></footer>
        </article>

        <div className="publish-platform-list">{PUBLISH_PLATFORMS.map((platform, index) => <article className={`publish-platform publish-platform-${platform.id}`} key={platform.id}>
          <span className="publish-platform-order">{String(index + 1).padStart(2, '0')}</span><b className="publish-platform-code">{platform.code}</b>
          <div><h4>{platform.label}</h4><span>{platform.destination}</span><small>{platform.note}</small></div>
          <button type="button" disabled={!draft.content.trim()} onClick={() => launch(platform.id)}>交接到{platform.label}<i>↗</i></button>
        </article>)}</div>
      </aside>
    </section>

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
          const platform = platformFor(item.platform)
          const metrics = Object.entries(item.metrics || {}).slice(0, 3)
          return <div className="publish-history-row" key={item.id}><b>{platform.code}</b><span><strong>{item.title || `${platform.label}发布操作`}</strong><small>{new Date(item.completedAt).toLocaleString('zh-CN')} · {item.outcome === 'resolved' ? '已带回公开作品信息' : '已触发，等待官方确认'}</small>{metrics.length > 0 && <em>{metrics.map(([key, value]) => `${METRIC_LABELS[key] || key} ${num(value)}`).join(' · ')}</em>}</span>{item.workUrl ? <a href={item.workUrl} target="_blank" rel="noreferrer">查看作品 ↗</a> : <i>无公开链接</i>}</div>
        })}</div>}
        <p className="publish-receipt-warning">平台回执没有签名，只用于流程提示，不能作为审核通过、计费或收入依据。</p>
      </article>
    </section>
  </main>
}
