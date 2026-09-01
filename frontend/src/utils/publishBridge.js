export const PUBLISH_SOURCE = 'publish-review-demo'
export const BRIDGE_PING_EVENT = 'rodas:publish-bridge-ping'
export const BRIDGE_STATUS_EVENT = 'rodas:publish-bridge-status'

export const PUBLISH_PLATFORMS = [
  {
    id: 'douyin',
    label: '抖音',
    code: 'DY',
    destination: '创作者中心 · 图文发布',
    note: '在官方页面选择图片，再核对标题、正文与话题。',
    url: 'https://creator.douyin.com/creator-micro/content/upload?default-tab=3'
  },
  {
    id: 'xiaohongshu',
    label: '小红书',
    code: 'RED',
    destination: '创作服务平台 · 发布笔记',
    note: '素材仍由你手动选择，桥接助手只交接公开文案。',
    url: 'https://creator.xiaohongshu.com/publish'
  },
  {
    id: 'weibo',
    label: '微博',
    code: 'WB',
    destination: '微博 · 发布动态',
    note: '标题会并入正文；返回只代表已触发，不代表审核通过。',
    url: 'https://weibo.com/'
  }
]

const PLATFORM_IDS = new Set(PUBLISH_PLATFORMS.map(item => item.id))
const WORK_HOSTS = {
  douyin: ['douyin.com'],
  xiaohongshu: ['xiaohongshu.com', 'xhslink.com'],
  weibo: ['weibo.com']
}

function encodeBase64Url(value) {
  const bytes = new TextEncoder().encode(value)
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '=')
  const bytes = Uint8Array.from(atob(normalized), character => character.charCodeAt(0))
  return new TextDecoder().decode(bytes)
}

function safeWorkUrl(platform, value) {
  if (!value) return undefined
  try {
    const url = new URL(String(value))
    const allowed = url.protocol === 'https:' && (WORK_HOSTS[platform] || []).some(host => url.hostname === host || url.hostname.endsWith(`.${host}`))
    return allowed ? url.toString() : undefined
  } catch {
    return undefined
  }
}

export function parsePublishTags(value) {
  const values = Array.isArray(value) ? value : [value]
  const source = values.flatMap(item => String(item || '').split(/[,，\n]+|(?=[#＃])/))
  return [...new Set(source.map(tag => tag.replace(/^[#＃]+/, '').trim()).filter(Boolean))].slice(0, 30)
}

export function formatPublishCopy({ title, content, tags }) {
  const tagLine = parsePublishTags(tags).map(tag => `#${tag}`).join(' ')
  return [String(title || '').trim(), String(content || '').trim(), tagLine].filter(Boolean).join('\n\n')
}

export function buildPublishHandoffUrl({ platform, title, content, tags, returnTarget = 'workspace' }) {
  const target = PUBLISH_PLATFORMS.find(item => item.id === platform)
  if (!target) throw new Error('暂不支持这个发布平台')
  const payload = {
    version: 1,
    source: PUBLISH_SOURCE,
    platform,
    returnTarget: returnTarget === 'wizard' ? 'wizard' : 'workspace',
    title: String(title || '').trim().slice(0, 200),
    content: String(content || '').trim().slice(0, 10000),
    tags: parsePublishTags(tags)
  }
  const url = new URL(target.url)
  url.hash = `publish_review_draft=${encodeURIComponent(encodeBase64Url(JSON.stringify(payload)))}`
  return url.toString()
}

export function parsePublicationReceipt(hash) {
  const params = new URLSearchParams(String(hash || '').replace(/^#/, ''))
  const encoded = params.get('publication_receipt')
  if (!encoded) return null
  if (encoded.length > 50000) throw new Error('发布回执内容过大')

  const value = JSON.parse(decodeBase64Url(encoded))
  if (!value || typeof value !== 'object') throw new Error('发布回执格式无效')
  if (value.version !== 1 || !PLATFORM_IDS.has(value.platform)) throw new Error('发布回执平台不受支持')
  if (!['triggered', 'resolved'].includes(value.outcome)) throw new Error('发布回执状态不受支持')
  if (!['workspace', 'wizard'].includes(value.returnMode)) throw new Error('发布回执返回方式不受支持')
  if (typeof value.completedAt !== 'string' || !Number.isFinite(Date.parse(value.completedAt))) throw new Error('发布回执时间无效')

  const metrics = value.metrics && typeof value.metrics === 'object'
    ? Object.fromEntries(Object.entries(value.metrics).filter(([key, metric]) => key.length <= 40 && Number.isFinite(Number(metric)) && Number(metric) >= 0).slice(0, 20).map(([key, metric]) => [key, Number(metric)]))
    : undefined

  return {
    version: 1,
    platform: value.platform,
    outcome: value.outcome,
    returnMode: value.returnMode,
    completedAt: value.completedAt,
    workUrl: safeWorkUrl(value.platform, value.workUrl),
    title: typeof value.title === 'string' ? value.title.trim().slice(0, 200) : undefined,
    metrics
  }
}

export function publicationReceiptId(receipt) {
  return [receipt?.platform, receipt?.outcome, receipt?.completedAt, receipt?.workUrl || ''].join(':')
}

export function normalizePublishBridgeStatus(value, expected = {}) {
  const source = value && typeof value === 'object' ? value : {}
  const version = typeof source.version === 'string' && /^\d+\.\d+\.\d+$/.test(source.version) ? source.version : ''
  const appBaseUrl = typeof source.appBaseUrl === 'string' ? source.appBaseUrl.replace(/\/$/, '') : ''
  const callbackPath = typeof source.callbackPath === 'string' && source.callbackPath.startsWith('/') ? source.callbackPath : ''
  const expectedOrigin = String(expected.origin || '').replace(/\/$/, '')
  const expectedCallbackPath = String(expected.callbackPath || '/zh')
  const detected = source.ok === true && Boolean(version)
  const originMatches = detected && appBaseUrl === expectedOrigin
  const callbackMatches = detected && callbackPath === expectedCallbackPath
  const debuggerEnabled = detected && source.debuggerEnabled === true
  return {
    detected,
    ready: detected && originMatches && callbackMatches && debuggerEnabled,
    version,
    appBaseUrl,
    callbackPath,
    originMatches,
    callbackMatches,
    debuggerEnabled,
    error: typeof source.error === 'string' ? source.error.slice(0, 240) : ''
  }
}
