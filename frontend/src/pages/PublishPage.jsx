import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { generatePublishCopy } from '../services/api'
import { AI_PROVIDER_LABELS, readActiveAIConfig } from '../utils/ai'
import { BRIDGE_PING_EVENT, BRIDGE_STATUS_EVENT, buildPublishHandoffUrl, formatPublishCopy, normalizePublishBridgeStatus, parsePublishTags, PUBLISH_PLATFORMS } from '../utils/publishBridge'

const BRIDGE_CALLBACK_PATH = '/zh'
const EMPTY_BRIDGE_STATUS = { detected: false, ready: false, version: '', appBaseUrl: '', callbackPath: '', originMatches: false, callbackMatches: false, debuggerEnabled: false, error: '', checking: true }
const PLATFORM_GUIDES = {
  douyin: { editor: '抖音图文', preview: '抖音竖屏预览', titleLabel: '标题', titleLimit: 200, contentLimit: 10000 },
  xiaohongshu: { editor: '小红书笔记', preview: '小红书笔记预览', titleLabel: '笔记标题', titleLimit: 20, contentLimit: 1000 },
  weibo: { editor: '微博图文', preview: '微博桌面预览', titleLabel: '微博首句', titleLimit: 70, contentLimit: 2000 }
}
const EMPTY_REVIEW = { platform: 'douyin', title: '', workUrl: '', views: '', likes: '', comments: '', collects: '', shares: '', note: '', source: 'manual' }
const REVIEW_METRICS = [
  ['views', '浏览 / 播放'],
  ['likes', '点赞'],
  ['comments', '评论'],
  ['collects', '收藏'],
  ['shares', '分享']
]

function readStored(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback } catch { return fallback }
}

function platformFor(id) { return PUBLISH_PLATFORMS.find(item => item.id === id) || PUBLISH_PLATFORMS[0] }
function formatTagInput(value) { return parsePublishTags(value).map(tag => `#${tag}`).join(' ') }
function metricValue(value) { const number = Number(value); return Number.isFinite(number) && number >= 0 ? number : 0 }
function formatMetric(value) { return metricValue(value).toLocaleString('zh-CN') }
function safeHttpUrl(value) {
  try {
    const url = new URL(String(value || '').trim())
    return ['http:', 'https:'].includes(url.protocol) ? url.toString() : ''
  } catch { return '' }
}
function receiptMetric(metrics, keys) {
  const key = keys.find(name => Number.isFinite(Number(metrics?.[name])))
  return key ? String(metrics[key]) : ''
}
function reviewReading(metrics) {
  if (!metrics.views) return { title: '等待第一组数据', detail: '发布后录入浏览或播放量，系统会在这里计算互动率，并提示下一条内容值得保留或调整的方向。' }
  const rate = metrics.engagementRate
  if (rate >= 8) return { title: '这条内容值得做成系列', detail: '互动反馈较集中。下一条优先复用相同选题、开头结构和发布时间，再只改变一个变量观察结果。' }
  if (metrics.collects > metrics.comments * 1.5 && metrics.collects >= 3) return { title: '收藏意图比讨论更强', detail: '用户更愿意把内容留到以后看。下一条可以强化清单、价格、地址或步骤等可保存信息。' }
  if (metrics.comments >= metrics.collects && metrics.comments >= 3) return { title: '话题带动了讨论', detail: '评论贡献更突出。下一条可在结尾保留一个明确问题，并及时整理高频评论作为新选题。' }
  if (rate >= 3) return { title: '内容方向可以继续验证', detail: '已经出现有效互动，但信号还不够集中。下一条保留主题，尝试更直接的标题或更清晰的首屏利益点。' }
  return { title: '先优化前几秒与标题', detail: '当前互动相对分散。下一条先缩短铺垫，把菜品、优惠或到店理由提前，并避免一次同时改动太多变量。' }
}

function PlatformBrandMark({ id }) {
  if (id === 'xiaohongshu') return <svg viewBox="0 0 48 48" aria-hidden="true"><text x="24" y="27" textAnchor="middle">小红书</text></svg>
  if (id === 'weibo') return <svg viewBox="0 0 48 48" aria-hidden="true">
    <path className="weibo-wave weibo-wave-outer" d="M29.4 8.4c5.2-.9 10 2.2 10.9 7" />
    <path className="weibo-wave" d="M29.9 13.4c2.8-.4 5.3 1.2 5.8 3.7" />
    <path className="weibo-body" d="M37.4 25.3c0 7.3-8.1 13.2-18.1 13.2S2.8 33.9 2.8 28.4c0-3.1 2.7-6.4 7.4-9.2 6-3.6 12.2-3.8 13.8-.7.7 1.4.2 3.1-.3 4.5 5.7-1.2 13.7-1.3 13.7 2.3Z" />
    <ellipse className="weibo-eye" cx="20.4" cy="28.1" rx="10.7" ry="7.6" transform="rotate(-10 20.4 28.1)" />
    <circle className="weibo-pupil" cx="20.4" cy="28.2" r="4.6" />
    <circle className="weibo-glint" cx="18.8" cy="26.5" r="1.5" />
  </svg>
  return <svg viewBox="0 0 48 48" aria-hidden="true">
    <path className="douyin-shadow douyin-shadow-cyan" d="M28 7v20.1a8.5 8.5 0 1 1-6.4-8.2v5.8a3.1 3.1 0 1 0 1.2 2.4V7H28Zm0 0c.4 6 4.6 10.3 10.6 10.8v5.7A16.1 16.1 0 0 1 28 19" />
    <path className="douyin-shadow douyin-shadow-red" d="M28 7v20.1a8.5 8.5 0 1 1-6.4-8.2v5.8a3.1 3.1 0 1 0 1.2 2.4V7H28Zm0 0c.4 6 4.6 10.3 10.6 10.8v5.7A16.1 16.1 0 0 1 28 19" />
    <path className="douyin-note" d="M28 7v20.1a8.5 8.5 0 1 1-6.4-8.2v5.8a3.1 3.1 0 1 0 1.2 2.4V7H28Zm0 0c.4 6 4.6 10.3 10.6 10.8v5.7A16.1 16.1 0 0 1 28 19" />
  </svg>
}

function DishArtwork({ label = '今日\n门店' }) {
  const parts = label.split('\n')
  return <div className="publish-dish-scene" aria-hidden="true"><i /><i /><i /><b>{parts.map((part, index) => <span key={part}>{part}{index < parts.length - 1 && <br />}</span>)}</b></div>
}

function DouyinPreview({ draft, tags, author }) {
  return <div className="publish-phone publish-phone-douyin">
    <div className="publish-phone-status"><b>9:41</b><span><i /><i />▰</span></div>
    <div className="publish-phone-appbar"><span>DY</span><strong>推荐</strong><i>⌕</i></div>
    <div className="publish-phone-stage">
      <DishArtwork />
      <div className="publish-phone-actions" aria-hidden="true"><b>{author.slice(0, 1)}</b><span>♥<small>赞</small></span><span>●<small>评论</small></span><span>◆<small>收藏</small></span><span>↗<small>分享</small></span></div>
      <div className="publish-phone-copy">
        <span>@{author}</span>
        <h4>{draft.title.trim() || '一条值得被看见的门店内容'}</h4>
        <p>{draft.content.trim() || '正文会在这里实时预览。先在中间编辑区写下门店此刻最值得告诉顾客的事，或请右侧 AI 助手起草。'}</p>
        <div>{tags.length ? tags.slice(0, 6).map(tag => <em key={tag}>#{tag}</em>) : <em>#门店日常</em>}</div>
      </div>
    </div>
    <div className="publish-phone-nav"><b>首页</b><span>发现</span><i>＋</i><span>消息</span><span>我</span></div>
  </div>
}

function XiaohongshuPreview({ draft, tags, author, mode, onModeChange }) {
  return <>
    <div className="publish-preview-modes" role="tablist" aria-label="小红书预览方式"><button type="button" role="tab" aria-selected={mode === 'note'} className={mode === 'note' ? 'is-active' : ''} onClick={() => onModeChange('note')}>笔记预览</button><button type="button" role="tab" aria-selected={mode === 'cover'} className={mode === 'cover' ? 'is-active' : ''} onClick={() => onModeChange('cover')}>封面预览</button></div>
    <div className={`publish-xhs-phone${mode === 'cover' ? ' is-cover' : ''}`}>
      <div className="publish-xhs-status"><b>9:41</b><span>● ◦ ▰</span></div>
      <div className="publish-xhs-author"><i>‹</i><b>{author.slice(0, 1)}</b><span><strong>{author}</strong><small>门店主理人</small></span><button type="button" tabIndex={-1}>关注</button><em>⌯</em></div>
      {mode === 'cover' ? <>
        <div className="publish-xhs-discovery-tabs"><b>☰</b><span><i>关注</i><strong>发现</strong><i>附近</i></span><em>⌕</em></div>
        <div className="publish-xhs-categories"><strong>推荐</strong><span>直播</span><span>短剧</span><span>穿搭</span><span>旅行</span><span>动漫</span></div>
        <div className="publish-xhs-cover-grid">
          <article className="is-current"><div className="publish-xhs-grid-art"><DishArtwork label="门店\n新鲜事" /></div><h4>{draft.title.trim() || '周末来店里，吃点刚刚好的'}</h4><footer><b>{author.slice(0, 1)}</b><span>{author}</span><i>♡ 0</i></footer></article>
          <article><div className="publish-xhs-placeholder" /><h4>示例笔记标题 1</h4><footer><b /><span>用户名</span><i>♡ 0</i></footer></article>
          <article className="is-tall"><div className="publish-xhs-placeholder" /><h4>示例笔记标题 2</h4><footer><b /><span>用户名</span><i>♡ 0</i></footer></article>
          <article className="is-tall"><div className="publish-xhs-placeholder" /><h4>示例笔记标题 3</h4><footer><b /><span>用户名</span><i>♡ 0</i></footer></article>
        </div>
        <div className="publish-xhs-discovery-bottom"><b>⌂<small>首页</small></b><span>▧<small>市集</small></span><i>＋</i><span>♧<small>消息</small></span><span>♙<small>我</small></span></div>
      </> : <>
        <div className="publish-xhs-cover"><DishArtwork label="本周\n好味" /><div><small>门店新鲜事</small><strong>{draft.title.trim() || '周末来店里，吃点刚刚好的'}</strong></div></div>
        <div className="publish-xhs-copy"><h4>{draft.title.trim() || '周末来店里，吃点刚刚好的'}</h4><p>{draft.content.trim() || '把门店里今天值得分享的新鲜事写下来。这里会按照小红书笔记的阅读方式展示正文。'}</p><div>{tags.length ? tags.slice(0, 7).map(tag => <em key={tag}>#{tag}</em>) : <em>#门店日常</em>}</div></div>
        <div className="publish-xhs-bottom"><span>◯ 说点什么…</span><b>♡</b><b>☆</b><b>◯</b><b>➤</b></div>
      </>}
    </div>
  </>
}

function WeiboPreview({ draft, tags, author }) {
  return <div className="publish-weibo-shell">
    <div className="publish-weibo-top"><b><i /> 微博</b><span>⌕ 搜索微博</span><div>⌂　♡　◯　♧　♙</div></div>
    <div className="publish-weibo-body">
      <aside><h4>首页</h4><b>☷　全部关注</b><span>☆　最新微博</span><span>♙　特别关注</span><span>◉　好友圈</span><hr /><small>自定义分组</small><span>·　门店同行</span><span>·　本地生活</span></aside>
      <article>
        <header><b>{author.slice(0, 1)}</b><span><strong>{author}</strong><small>刚刚 · 来自懂单儿发布助手</small></span><i>•••</i></header>
        <h4>{draft.title.trim() || '门店今天，想和大家分享一件新鲜事'}</h4>
        <p>{draft.content.trim() || '正文会在这里按微博桌面信息流的样式展开，方便在交接前检查首句、段落和话题。'}</p>
        <div className="publish-weibo-tags">{tags.length ? tags.slice(0, 7).map(tag => <em key={tag}>#{tag}</em>) : <em>#门店日常</em>}</div>
        <div className="publish-weibo-media"><div><DishArtwork label="门店\n素材" /></div><button type="button" tabIndex={-1}>＋</button></div>
        <footer><span>☺ 表情</span><span>▧ 图片</span><span># 话题</span><span>@ 用户</span><span>••• 更多</span></footer>
      </article>
    </div>
  </div>
}

function PlatformPreview({ draft, tags, platform, author, xhsMode, onXhsModeChange }) {
  if (platform.id === 'xiaohongshu') return <XiaohongshuPreview draft={draft} tags={tags} author={author} mode={xhsMode} onModeChange={onXhsModeChange} />
  if (platform.id === 'weibo') return <WeiboPreview draft={draft} tags={tags} author={author} />
  return <DouyinPreview draft={draft} tags={tags} author={author} />
}

export default function PublishPage({ user, receipt, onReceiptHandled, onNotify, onOpenAISettings }) {
  const scope = String(user?.id || user?.email || 'local')
  const draftKey = `rodas-publish-draft:${scope}`
  const platformKey = `rodas-publish-platform:${scope}`
  const reviewKey = `rodas-publish-reviews:${scope}`
  const origin = window.location.origin
  const callbackPath = BRIDGE_CALLBACK_PATH
  const initialDraft = useMemo(() => {
    const stored = readStored(draftKey, { title: '', content: '', tags: '' })
    return { ...stored, tags: formatTagInput(stored.tags) }
  }, [draftKey])
  const [draft, setDraft] = useState(initialDraft)
  const [bridgeStatus, setBridgeStatus] = useState(EMPTY_BRIDGE_STATUS)
  const [selectedPlatform, setSelectedPlatform] = useState(() => localStorage.getItem(platformKey) || 'douyin')
  const [copied, setCopied] = useState('')
  const [aiConfig, setAIConfig] = useState(readActiveAIConfig)
  const [aiBrief, setAIBrief] = useState('')
  const [aiBusy, setAIBusy] = useState(false)
  const [aiCandidate, setAICandidate] = useState(null)
  const [xhsPreviewMode, setXhsPreviewMode] = useState('note')
  const [reviews, setReviews] = useState(() => readStored(reviewKey, []))
  const [reviewDraft, setReviewDraft] = useState(() => ({ ...EMPTY_REVIEW, platform: localStorage.getItem(platformKey) || 'douyin', title: initialDraft.title }))
  const [activeReviewId, setActiveReviewId] = useState('draft')
  const [reviewPage, setReviewPage] = useState(1)
  const bridgeProbeRef = useRef('')
  const bridgeTimeoutRef = useRef(null)
  const tags = useMemo(() => parsePublishTags(draft.tags), [draft.tags])
  const previewCopy = useMemo(() => formatPublishCopy({ ...draft, tags }), [draft, tags])
  const platform = platformFor(selectedPlatform)
  const guide = PLATFORM_GUIDES[selectedPlatform] || PLATFORM_GUIDES.douyin
  const author = user?.display_name?.trim() || '懂单儿门店'
  const bridgeReady = bridgeStatus.ready
  const reviewMetrics = useMemo(() => {
    const views = metricValue(reviewDraft.views)
    const likes = metricValue(reviewDraft.likes)
    const comments = metricValue(reviewDraft.comments)
    const collects = metricValue(reviewDraft.collects)
    const shares = metricValue(reviewDraft.shares)
    const engagement = likes + comments + collects + shares
    return { views, likes, comments, collects, shares, engagement, engagementRate: views ? engagement / views * 100 : 0 }
  }, [reviewDraft])
  const currentReviewReading = useMemo(() => reviewReading(reviewMetrics), [reviewMetrics])

  const detectBridge = useCallback(() => {
    const nonce = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`
    bridgeProbeRef.current = nonce
    if (bridgeTimeoutRef.current) window.clearTimeout(bridgeTimeoutRef.current)
    setBridgeStatus(current => ({ ...current, checking: true }))
    window.dispatchEvent(new CustomEvent(BRIDGE_PING_EVENT, { detail: { nonce } }))
    bridgeTimeoutRef.current = window.setTimeout(() => {
      if (bridgeProbeRef.current !== nonce) return
      bridgeProbeRef.current = ''
      setBridgeStatus({ ...EMPTY_BRIDGE_STATUS, checking: false, error: '未检测到 PublishLoop，请重新加载扩展并刷新本页' })
    }, 1400)
  }, [])

  useEffect(() => { localStorage.setItem(draftKey, JSON.stringify(draft)) }, [draft, draftKey])
  useEffect(() => { localStorage.setItem(platformKey, selectedPlatform) }, [platformKey, selectedPlatform])
  useEffect(() => {
    const onBridgeStatus = event => {
      const detail = event instanceof CustomEvent ? event.detail : null
      if (!detail || typeof detail !== 'object') return
      if (detail.nonce && bridgeProbeRef.current && detail.nonce !== bridgeProbeRef.current) return
      bridgeProbeRef.current = ''
      if (bridgeTimeoutRef.current) window.clearTimeout(bridgeTimeoutRef.current)
      const next = { ...normalizePublishBridgeStatus(detail, { origin, callbackPath }), checking: false }
      setBridgeStatus(next)
    }
    const onFocus = () => detectBridge()
    const onVisibility = () => { if (document.visibilityState === 'visible') detectBridge() }
    window.addEventListener(BRIDGE_STATUS_EVENT, onBridgeStatus)
    window.addEventListener('focus', onFocus)
    document.addEventListener('visibilitychange', onVisibility)
    const kickoff = window.setTimeout(detectBridge, 0)
    const heartbeat = window.setInterval(detectBridge, 12000)
    return () => {
      window.removeEventListener(BRIDGE_STATUS_EVENT, onBridgeStatus)
      window.removeEventListener('focus', onFocus)
      document.removeEventListener('visibilitychange', onVisibility)
      window.clearTimeout(kickoff)
      window.clearInterval(heartbeat)
      if (bridgeTimeoutRef.current) window.clearTimeout(bridgeTimeoutRef.current)
    }
  }, [callbackPath, detectBridge, origin])
  useEffect(() => {
    const refresh = () => setAIConfig(readActiveAIConfig())
    window.addEventListener('rodas:ai-config-changed', refresh)
    window.addEventListener('storage', refresh)
    window.addEventListener('focus', refresh)
    return () => { window.removeEventListener('rodas:ai-config-changed', refresh); window.removeEventListener('storage', refresh); window.removeEventListener('focus', refresh) }
  }, [])
  useEffect(() => {
    if (!receipt) return
    setReviewDraft(current => ({
      ...current,
      platform: receipt.platform || current.platform,
      title: receipt.title || draft.title || current.title,
      workUrl: receipt.workUrl || current.workUrl,
      views: receiptMetric(receipt.metrics, ['views', 'plays', 'reads', 'impressions']) || current.views,
      likes: receiptMetric(receipt.metrics, ['likes', 'likeCount']) || current.likes,
      comments: receiptMetric(receipt.metrics, ['comments', 'commentCount']) || current.comments,
      collects: receiptMetric(receipt.metrics, ['collects', 'favorites', 'saves']) || current.collects,
      shares: receiptMetric(receipt.metrics, ['shares', 'reposts']) || current.shares,
      source: 'bridge'
    }))
    setActiveReviewId('draft')
    setReviewPage(1)
    onNotify?.({ type: 'success', message: receipt.outcome === 'resolved' ? '平台结果已带回，并已填入作品复盘' : '平台操作已返回，已为你准备作品复盘' })
    onReceiptHandled?.()
  }, [draft.title, onNotify, onReceiptHandled, receipt])

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
    if (!bridgeStatus.detected) { notify('error', '未检测到 PublishLoop，请在扩展管理页重新加载后刷新本页'); return }
    if (!bridgeStatus.originMatches || !bridgeStatus.callbackMatches) { notify('error', `PublishLoop 回调应设置为 ${origin}${callbackPath}`); return }
    if (!bridgeStatus.debuggerEnabled) { notify('error', 'PublishLoop 缺少增强点击权限，请重新启用扩展并确认权限'); return }
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
    setAICandidate(null)
    setAIBusy(true)
    try {
      const result = await generatePublishCopy({ platform: selectedPlatform, brief: aiBrief.trim() }, activeConfig)
      setAICandidate({
        platform: selectedPlatform,
        provider: result.provider,
        title: result.draft?.title || '',
        content: result.draft?.content || '',
        tags: formatTagInput(result.draft?.tags || []),
        angle: result.draft?.angle || ''
      })
      notify('success', `${AI_PROVIDER_LABELS[result.provider] || 'AI'} 候选文案已生成，请确认后填入编辑栏`)
    } catch (error) {
      notify('error', error.message || 'AI 文案生成失败')
    } finally {
      setAIBusy(false)
    }
  }

  const applyAICandidate = () => {
    if (!aiCandidate) return
    if ((draft.title.trim() || draft.content.trim() || draft.tags.trim()) && !window.confirm('填入候选文案会替换中间编辑栏的标题、正文和话题，继续吗？')) return
    setDraft({ title: aiCandidate.title, content: aiCandidate.content, tags: aiCandidate.tags })
    notify('success', '候选文案已填入中间编辑栏，请核对后发布')
  }

  const updateReviewDraft = (key, value) => setReviewDraft(current => ({ ...current, [key]: value }))

  const bringCurrentDraftToReview = () => {
    setReviewDraft({ ...EMPTY_REVIEW, platform: selectedPlatform, title: draft.title })
    setActiveReviewId('draft')
    setReviewPage(1)
    notify('success', '当前平台与标题已带入作品复盘')
  }

  const editReview = item => {
    if (item.id === 'draft') {
      setReviewDraft({ ...EMPTY_REVIEW, platform: selectedPlatform, title: draft.title })
      setActiveReviewId('draft')
      return
    }
    setReviewDraft({
      ...EMPTY_REVIEW,
      platform: item.platform,
      title: item.title,
      workUrl: item.workUrl || '',
      views: String(item.views ?? ''),
      likes: String(item.likes ?? ''),
      comments: String(item.comments ?? ''),
      collects: String(item.collects ?? ''),
      shares: String(item.shares ?? ''),
      note: item.note || '',
      source: item.source || 'manual'
    })
    setActiveReviewId(item.id)
  }

  const saveReview = event => {
    event.preventDefault()
    if (!reviewDraft.title.trim()) { notify('error', '请先填写作品标题'); return }
    if (!reviewMetrics.views) { notify('error', '请填写大于 0 的浏览或播放量'); return }
    const rawUrl = reviewDraft.workUrl.trim()
    let workUrl = ''
    if (rawUrl) {
      try {
        const parsed = new URL(rawUrl)
        if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('unsupported protocol')
        workUrl = parsed.toString()
      } catch {
        notify('error', '作品链接应是完整的 http 或 https 公网地址')
        return
      }
    }
    const entry = {
      id: activeReviewId === 'draft' ? (globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`) : activeReviewId,
      platform: reviewDraft.platform,
      title: reviewDraft.title.trim(),
      workUrl,
      note: reviewDraft.note.trim(),
      source: reviewDraft.source || 'manual',
      ...reviewMetrics,
      savedAt: new Date().toISOString()
    }
    setReviews(current => {
      const next = activeReviewId === 'draft' ? [entry, ...current].slice(0, 12) : current.map(item => item.id === activeReviewId ? entry : item)
      localStorage.setItem(reviewKey, JSON.stringify(next))
      return next
    })
    setActiveReviewId(entry.id)
    setReviewPage(1)
    notify('success', '作品复盘已保存在当前浏览器')
  }

  const removeReview = id => {
    if (activeReviewId === id) {
      setReviewDraft({ ...EMPTY_REVIEW, platform: selectedPlatform, title: draft.title })
      setActiveReviewId('draft')
    }
    setReviews(current => {
      const next = current.filter(item => item.id !== id)
      localStorage.setItem(reviewKey, JSON.stringify(next))
      return next
    })
    setReviewPage(current => Math.min(current, Math.max(1, Math.ceil(reviews.length / 5))))
  }

  const draftListItem = activeReviewId === 'draft'
    ? { ...reviewDraft, ...reviewMetrics, id: 'draft' }
    : { ...EMPTY_REVIEW, id: 'draft', platform: selectedPlatform, title: draft.title }
  const reviewItems = [draftListItem, ...reviews]
  const reviewTotalPages = Math.max(1, Math.ceil(reviewItems.length / 5))
  const safeReviewPage = Math.min(reviewPage, reviewTotalPages)
  const visibleReviewItems = reviewItems.slice((safeReviewPage - 1) * 5, safeReviewPage * 5)
  const reviewWorkUrl = safeHttpUrl(reviewDraft.workUrl)
  const activeReview = activeReviewId === 'draft' ? null : reviews.find(item => item.id === activeReviewId)

  return <main className="publish-page">
    <section className="publish-heading">
      <div><p className="eyebrow">09 / PUBLISH DESK</p><h2>内容发布</h2><p>从一句门店灵感，到一条可核对、可交接的公开内容。</p></div>
    </section>

    <section className="publish-workbench">
      <div className="publish-preview-panel">
        <header className="publish-panel-head"><div><span>实时预览 / {platform.code}</span><h3>{guide.preview}</h3></div><b><i /> LIVE</b></header>
        <PlatformPreview draft={draft} tags={tags} platform={platform} author={author} xhsMode={xhsPreviewMode} onXhsModeChange={setXhsPreviewMode} />
        <p className="publish-preview-caption">预览只用于发布前核对文案；图片、封面与最终样式仍以{platform.label}官方页面为准。</p>
      </div>

      <div className="publish-compose-panel">
        <header className="publish-panel-head"><div><span>文案底稿 / {platform.code}</span><h3>{guide.editor}</h3><small>输入内容会同步显示在左侧预览</small></div><button type="button" onClick={clearDraft}>清空</button></header>
        <label className="publish-field"><span>{guide.titleLabel} <small className={draft.title.length > guide.titleLimit ? 'is-over' : ''}>{draft.title.length} / 建议 {guide.titleLimit}</small></span><input value={draft.title} maxLength={200} onChange={event => updateDraft('title', event.target.value)} placeholder="例如：晚市新菜单，今天先从这三道菜开始" /></label>
        <label className="publish-field publish-copy-field"><span>正文 <small className={draft.content.length > guide.contentLimit ? 'is-over' : ''}>{draft.content.length} / 建议 {guide.contentLimit.toLocaleString('zh-CN')}</small></span><textarea value={draft.content} maxLength={10000} onChange={event => updateDraft('content', event.target.value)} placeholder="写下准备公开给顾客看的内容。不要填写手机号、预算、库存或内部审批信息。" /></label>
        <label className="publish-field"><span>话题标签 <small>{tags.length} / 30</small></span><input value={draft.tags} onChange={event => updateDraft('tags', event.target.value)} onBlur={event => updateDraft('tags', formatTagInput(event.target.value))} placeholder="#新品 #晚餐 #城市探店" /></label>

        <div className="publish-editor-note"><b>接下来 3 步</b><ol><li>保存或复制这份公开文案</li><li>进入官方平台后选择图片并检查文案</li><li>完成发布后保持页面在前台，等待回执</li></ol></div>
        <div className="publish-editor-actions"><button type="button" className="secondary" onClick={saveDraft}>✓ 保存草稿</button><button type="button" className="secondary" onClick={downloadDraft}>↓ 下载文案</button><button type="button" className="primary" disabled={!draft.content.trim()} onClick={launch}>打开并导入{platform.label} ↗</button><button type="button" className="secondary" disabled={!previewCopy} onClick={() => copyText(previewCopy, 'copy', '完整文案')}>{copied === 'copy' ? '✓ 已复制' : '复制全文'}</button></div>
      </div>

      <aside className="publish-assistant-panel">
        <article className="publish-ai-card">
          <header><span className="publish-ai-mark">AI</span><div><h3>发布助手</h3><p>为当前{platform.label}生成标题、正文和话题。</p></div></header>
          <div className={`publish-ai-provider${aiConfig ? ' is-ready' : ''}`}><i /><span><b>{aiConfig ? `${AI_PROVIDER_LABELS[aiConfig.provider] || aiConfig.provider} 已接入` : '尚未配置 AI'}</b><small>{aiConfig?.modelId || '复用设置中的服务商与模型'}</small></span><button type="button" onClick={onOpenAISettings}>设置</button></div>
          <label className="publish-ai-brief"><span>你想写什么？</span><textarea value={aiBrief} maxLength={1000} onChange={event => setAIBrief(event.target.value)} placeholder={`例如：为周末晚市的新菜单写一条${platform.label}文案，语气轻松，突出三道新品`} /></label>
          <button type="button" className="publish-generate-button" disabled={aiBusy || !aiBrief.trim()} onClick={createWithAI}>{aiBusy ? <><i className="publish-ai-spinner" /> 正在生成…</> : <><span>✦</span> 生成发布文案</>}</button>
          {aiCandidate && <section className="publish-ai-result" aria-live="polite">
            <header><span>AI 候选文案</span><small>{platformFor(aiCandidate.platform).label}</small></header>
            <h4>{aiCandidate.title || '未生成标题'}</h4>
            <p>{aiCandidate.content || '未生成正文'}</p>
            <div>{parsePublishTags(aiCandidate.tags).map(tag => <span key={tag}>#{tag}</span>)}</div>
            {aiCandidate.angle && <small className="publish-ai-result-angle">写作角度：{aiCandidate.angle}</small>}
            <button type="button" onClick={applyAICandidate}>↓ 填入中间编辑栏</button>
          </section>}
          <small className="publish-ai-disclaimer">生成结果会先显示在这里；确认填入前不会改动编辑栏，也不会自动发布。</small>
        </article>

        <div className="publish-channel-control publish-channel-control-sidebar">
          <header><span><b>当前发布渠道</b><small>编辑提示与预览会随渠道一起切换</small></span><em className={bridgeReady ? 'is-ready' : ''}><i />{bridgeStatus.checking ? '正在检测' : bridgeReady ? '桥接就绪' : bridgeStatus.detected ? '需修正' : '未连接'}</em></header>
          <div role="tablist" aria-label="选择目标发布平台">{PUBLISH_PLATFORMS.map(item => <button type="button" role="tab" aria-selected={selectedPlatform === item.id} className={`publish-channel-${item.id}${selectedPlatform === item.id ? ' is-active' : ''}`} onClick={() => { setSelectedPlatform(item.id); setAICandidate(null) }} key={item.id}><b className="publish-channel-logo"><PlatformBrandMark id={item.id} /></b><span><strong>{item.label}</strong><small>{selectedPlatform === item.id ? '正在编辑' : '切换到此渠道'}</small></span><i>{selectedPlatform === item.id ? '✓' : '→'}</i></button>)}</div>
        </div>
      </aside>
    </section>

    <div className="publish-privacy-note"><b>只交接公开文案</b><span>标题、正文和话题通过浏览器地址片段进入扩展；账号、Cookie、本地素材与 AI 密钥不会进入发布交接内容。</span></div>

    <section className="publish-retro-section">
      <header className="publish-retro-head">
        <div><span>POST-PUBLISH REVIEW</span><h3>作品复盘</h3><p>按作品查看发布后的公开表现，并把结论留给下一次创作。</p></div>
        <button type="button" onClick={bringCurrentDraftToReview}>＋ 新建复盘</button>
      </header>

      <div className="publish-retro-console">
        <aside className="publish-retro-library">
          <header><div><b>作品列表</b><small>{reviewItems.length} 条</small></div><span>选择作品查看数据</span></header>
          <div className="publish-retro-library-list">{visibleReviewItems.map(item => {
            const itemPlatform = platformFor(item.platform)
            const hasData = metricValue(item.views) > 0
            return <button type="button" className={activeReviewId === item.id ? 'is-active' : ''} onClick={() => editReview(item)} key={item.id}>
              <span className={`publish-retro-platform-pill is-${item.platform}`}>{itemPlatform.label}</span>
              <em className={hasData ? 'is-ready' : ''}>{hasData ? '数据已就绪' : '待录入'}</em>
              <strong>{item.title?.trim() || '未命名作品'}</strong>
              <small>{hasData ? `${formatMetric(item.views)} 次浏览 / 播放` : item.id === 'draft' ? '当前正在编辑的文案' : '暂无数据'}</small>
            </button>
          })}</div>
          <footer><button type="button" disabled={safeReviewPage <= 1} onClick={() => setReviewPage(page => Math.max(1, page - 1))}>上一页</button><span>{safeReviewPage} / {reviewTotalPages}</span><button type="button" disabled={safeReviewPage >= reviewTotalPages} onClick={() => setReviewPage(page => Math.min(reviewTotalPages, page + 1))}>下一页</button></footer>
        </aside>

        <form className="publish-retro-detail" onSubmit={saveReview}>
          <header className="publish-retro-detail-head">
            <div className="publish-retro-detail-title">
              <div><span className={`publish-retro-platform-pill is-${reviewDraft.platform}`}>{platformFor(reviewDraft.platform).label}</span><em className={reviewMetrics.views ? 'is-ready' : ''}>{reviewMetrics.views ? '数据已就绪' : '等待数据'}</em></div>
              <label><span>作品标题</span><input value={reviewDraft.title} maxLength={200} onChange={event => updateReviewDraft('title', event.target.value)} placeholder="填写作品标题" /></label>
              <p>直接在下方数据卡中录入平台公开数据，系统会同步生成复盘判断。</p>
            </div>
            {reviewWorkUrl ? <a href={reviewWorkUrl} target="_blank" rel="noreferrer">打开作品链接 ↗</a> : <button type="button" disabled>↻ 等待作品链接</button>}
          </header>

          <div className="publish-retro-link-row">
            <label><span>公开作品链接 <small>选填</small></span><input value={reviewDraft.workUrl} inputMode="url" onChange={event => updateReviewDraft('workUrl', event.target.value)} placeholder="作品公开后粘贴 https://..." /></label>
            <div className="publish-retro-platform-choice" role="group" aria-label="选择复盘平台">{PUBLISH_PLATFORMS.map(item => <button type="button" className={reviewDraft.platform === item.id ? 'is-active' : ''} aria-pressed={reviewDraft.platform === item.id} onClick={() => updateReviewDraft('platform', item.id)} key={item.id}>{item.label}</button>)}</div>
          </div>

          <div className="publish-retro-metric-board">
            {REVIEW_METRICS.map(([key, label]) => <label key={key}><span>{label}</span><input type="number" min="0" step="1" inputMode="numeric" value={reviewDraft[key]} onChange={event => updateReviewDraft(key, event.target.value)} placeholder="0" /></label>)}
            <div><span>互动总量</span><strong>{formatMetric(reviewMetrics.engagement)}</strong></div>
            <div><span>互动率</span><strong>{reviewMetrics.views ? `${reviewMetrics.engagementRate.toFixed(1)}%` : '暂无数据'}</strong></div>
            <div><span>收藏率</span><strong>{reviewMetrics.views ? `${(reviewMetrics.collects / reviewMetrics.views * 100).toFixed(1)}%` : '暂无数据'}</strong></div>
            <div><span>评论率</span><strong>{reviewMetrics.views ? `${(reviewMetrics.comments / reviewMetrics.views * 100).toFixed(1)}%` : '暂无数据'}</strong></div>
          </div>

          <p className="publish-retro-detail-meta">记录时间：{activeReview?.savedAt ? new Date(activeReview.savedAt).toLocaleString('zh-CN') : '尚未保存'} · 数据来源：{reviewDraft.source === 'bridge' ? '发布桥接回传' : '手动录入'}</p>

          <div className="publish-retro-support-grid">
            <section className="publish-retro-snapshot"><header><span>↶</span><b>数据快照</b></header><div><span>{activeReview?.savedAt ? new Date(activeReview.savedAt).toLocaleString('zh-CN') : '保存后生成第一份快照'}</span><b>赞 {formatMetric(reviewMetrics.likes)} · 评 {formatMetric(reviewMetrics.comments)} · 藏 {formatMetric(reviewMetrics.collects)} · 转 {formatMetric(reviewMetrics.shares)}</b></div></section>
            <section className="publish-retro-guidance"><header><span>✦</span><b>内容复盘</b><em>{reviewMetrics.views ? '已根据数据更新' : '等待数据'}</em></header><h4>{currentReviewReading.title}</h4><p>{currentReviewReading.detail}</p></section>
          </div>

          <div className="publish-retro-detail-actions">
            <label><span>复盘备注 <small>选填</small></span><input value={reviewDraft.note} maxLength={500} onChange={event => updateReviewDraft('note', event.target.value)} placeholder="例如：换了封面，发布时间提前到 18:00" /></label>
            {activeReviewId !== 'draft' && <button type="button" className="publish-retro-delete" onClick={() => removeReview(activeReviewId)}>删除记录</button>}
            <button type="submit" className="publish-retro-save">{activeReviewId === 'draft' ? '保存复盘记录' : '更新复盘记录'}</button>
          </div>
          <small className="publish-retro-method">互动率＝（点赞＋评论＋收藏＋分享）÷ 浏览/播放；建议连续记录 3 条以上再比较。</small>
        </form>
      </div>
    </section>
  </main>
}
