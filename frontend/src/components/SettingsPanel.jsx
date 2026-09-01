import { useEffect, useMemo, useState } from 'react'
import { changePassword, deleteDataset, updateProfile } from '../services/api'
import { Icon } from './ui'
import Avatar from './Avatar'
import { createGeneratedAvatar } from '../utils/avatar'

const THEME_OPTIONS = [
  ['sage', '鼠尾草绿', '自然沉稳'],
  ['ocean', '深海蓝', '专业理性'],
  ['ink', '墨石黑', '克制高级']
]

const AI_PROVIDERS = [
  {
    key: 'deepseek', label: 'DeepSeek', mark: 'DS', tone: 'deepseek',
    description: '深度思考与经营洞察',
    help: '在 DeepSeek 开放平台获取 API 密钥',
    keyUrl: 'https://platform.deepseek.com/sign_in',
    fields: [{ key: 'apiKey', label: 'API Key', placeholder: 'sk-…', secret: true }],
    defaults: { apiKey: '', modelId: 'deepseek-chat', endpoint: 'https://api.deepseek.com/v1' }
  },
  {
    key: 'doubao', label: '豆包', mark: '豆', tone: 'doubao',
    description: '中文经营问答与总结',
    help: '在火山引擎获取 API 密钥和模型 ID',
    keyUrl: 'https://console.volcengine.com/ark/region:cn-beijing/overview',
    fields: [
      { key: 'apiKey', label: 'API Key', placeholder: '输入火山引擎 API Key', secret: true },
      { key: 'modelId', label: '模型 ID', placeholder: 'ep-…' }
    ],
    defaults: { apiKey: '', modelId: '', endpoint: 'https://ark.cn-beijing.volces.com/api/v3' }
  },
  {
    key: 'openai', label: 'OpenAI', mark: '◎', tone: 'openai',
    description: '通用智能分析与报告',
    help: '在 OpenAI 或兼容 OpenAI 格式的开放平台获取 API 密钥',
    keyUrl: 'https://platform.openai.com/login?next=%2Fapi-keys',
    fields: [
      { key: 'apiKey', label: 'API Key', placeholder: 'sk-…', secret: true },
      { key: 'modelId', label: '模型 ID', placeholder: 'gpt-4o-mini' },
      { key: 'endpoint', label: 'API 端点', placeholder: 'https://api.openai.com/v1' }
    ],
    defaults: { apiKey: '', modelId: 'gpt-4o-mini', endpoint: 'https://api.openai.com/v1' }
  },
  {
    key: 'gemini', label: 'Gemini', mark: '✦', tone: 'gemini',
    description: '多模态数据解读',
    help: '在 Google AI Studio 获取 API 密钥',
    keyUrl: 'https://accounts.google.com/v3/signin/identifier?continue=https://aistudio.google.com/app/apikey&followup=https://aistudio.google.com/app/apikey&passive=1209600&flowName=GlifWebSignIn&flowEntry=ServiceLogin&dsh=S1392743199:1787814655050367',
    fields: [
      { key: 'apiKey', label: 'API Key', placeholder: 'AIza…', secret: true },
      { key: 'modelId', label: '模型 ID', placeholder: 'gemini-2.0-flash' }
    ],
    defaults: { apiKey: '', modelId: 'gemini-2.0-flash', endpoint: 'https://generativelanguage.googleapis.com/v1beta' }
  }
]

const DEFAULT_PREFERENCES = {
  defaultTab: 'upload',
  dateRange: '30d',
  showNumbers: true,
  compactCharts: false,
  platform: 'all',
  duplicatePolicy: 'latest',
  autoClean: true,
  uploadShortcut: 'mod+u',
  alerts: { salesDrop: true, orderDrop: true, productChange: false, repeatDrop: false },
  browserNotice: false
}

const DEFAULT_AI_SETTINGS = {
  activeProvider: '',
  providers: Object.fromEntries(AI_PROVIDERS.map(provider => [provider.key, { ...provider.defaults }]))
}

function readPreferences() {
  try {
    const saved = JSON.parse(localStorage.getItem('raota-preferences') || 'null')
    return { ...DEFAULT_PREFERENCES, ...saved, alerts: { ...DEFAULT_PREFERENCES.alerts, ...(saved?.alerts || {}) } }
  } catch {
    return DEFAULT_PREFERENCES
  }
}

function readAISettings() {
  try {
    const saved = JSON.parse(localStorage.getItem('rmdas-ai-settings') || 'null')
    const providers = Object.fromEntries(AI_PROVIDERS.map(provider => [provider.key, { ...provider.defaults, ...(saved?.providers?.[provider.key] || {}) }]))
    const activeProvider = AI_PROVIDERS.some(provider => provider.key === saved?.activeProvider) ? saved.activeProvider : ''
    return { activeProvider, providers }
  } catch {
    return DEFAULT_AI_SETTINGS
  }
}

const PROVIDER_IMAGE_ICONS = {
  doubao: '/provider-icons/doubao-transparent.png',
  openai: '/provider-icons/openai-transparent.png'
}

function ProviderMark({ provider }) {
  if (PROVIDER_IMAGE_ICONS[provider.key]) return <span className={`provider-mark provider-image-mark provider-mark-${provider.tone}`} aria-hidden="true"><img src={PROVIDER_IMAGE_ICONS[provider.key]} alt="" /></span>
  if (provider.key === 'deepseek') return <span className="provider-mark provider-icon-mark provider-mark-deepseek" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M23.748 4.651c-.254-.124-.364.113-.512.233-.051.04-.094.09-.137.137-.372.397-.806.657-1.373.626-.829-.046-1.537.214-2.163.848-.133-.782-.575-1.248-1.247-1.548-.352-.155-.708-.311-.955-.65-.172-.24-.219-.509-.305-.774-.055-.16-.11-.323-.293-.35-.2-.031-.278.136-.356.276-.313.572-.434 1.202-.422 1.84.027 1.436.633 2.58 1.838 3.393.137.094.172.187.129.323-.082.28-.18.553-.266.833-.055.179-.137.218-.328.14a5.5 5.5 0 0 1-1.737-1.179c-.857-.828-1.631-1.743-2.597-2.46a12 12 0 0 0-.689-.47c-.985-.957.13-1.743.387-1.836.27-.098.094-.433-.778-.428-.872.003-1.67.295-2.687.685a3 3 0 0 1-.465.136 9.6 9.6 0 0 0-2.883-.101c-1.885.21-3.39 1.1-4.497 2.622C.082 8.776-.231 10.854.152 13.02c.403 2.284 1.568 4.175 3.36 5.653 1.857 1.533 3.997 2.284 6.438 2.14 1.482-.085 3.132-.284 4.994-1.86.47.234.962.328 1.78.398.629.058 1.235-.031 1.705-.129.735-.155.684-.836.418-.961-2.155-1.004-1.682-.595-2.112-.926 1.095-1.295 2.768-3.598 3.284-6.733.05-.346.115-.834.108-1.114-.004-.171.035-.238.23-.257a4.2 4.2 0 0 0 1.545-.475c1.397-.763 1.96-2.016 2.093-3.517.02-.23-.004-.467-.247-.588M11.58 18.168c-2.088-1.642-3.101-2.183-3.52-2.16-.39.024-.32.472-.234.763.09.288.207.487.371.74.114.167.192.416-.113.603-.673.416-1.842-.14-1.897-.168-1.361-.801-2.5-1.86-3.301-3.306-.775-1.393-1.225-2.888-1.299-4.482-.02-.385.094-.522.477-.592a4.7 4.7 0 0 1 1.53-.038c2.131.311 3.946 1.264 5.467 2.774.868.86 1.525 1.887 2.202 2.89.72 1.066 1.494 2.082 2.48 2.915.348.291.626.513.892.677-.802.09-2.14.109-3.055-.615zm1.001-6.44a.306.306 0 0 1 .415-.287.3.3 0 0 1 .113.074.3.3 0 0 1 .086.214c0 .17-.136.307-.308.307a.303.303 0 0 1-.306-.307m3.11 1.596c-.2.081-.4.151-.591.16a1.25 1.25 0 0 1-.798-.254c-.274-.23-.47-.358-.551-.758a1.7 1.7 0 0 1 .015-.588c.07-.327-.007-.537-.238-.727-.188-.156-.426-.199-.689-.199a.6.6 0 0 1-.254-.078.253.253 0 0 1-.114-.358 1 1 0 0 1 .192-.21c.356-.202.767-.136 1.146.016.352.144.618.408 1.001.782.392.451.462.576.685.915.176.264.336.536.446.848.066.194-.02.353-.25.45" /></svg></span>
  if (provider.key === 'gemini') return <span className="provider-mark provider-icon-mark provider-mark-gemini" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81" /></svg></span>
  if (provider.key === 'doubao') return <span className="provider-mark provider-icon-mark provider-mark-doubao" aria-hidden="true"><svg viewBox="0 0 24 24"><defs><linearGradient id="doubao-gradient" x1="0" x2="1" y1="1" y2="0"><stop offset="0" stopColor="#6947ff" /><stop offset=".55" stopColor="#a14dff" /><stop offset="1" stopColor="#35e2c0" /></linearGradient></defs><path fill="url(#doubao-gradient)" d="M12 2.4c3.6 0 6.7 2.6 6.7 6.1 0 2.3-1.3 4.1-3.1 5.5l-2.1 1.7c-.9.7-1.5 1.6-1.5 2.8v2.1c-3.8-.5-6.7-3.5-6.7-7.3 0-2.8 1.5-5.3 3.8-6.7-.1-.4-.2-.8-.2-1.2 0-1.7 1.3-3 3.1-3z" /><path fill="#35e2c0" d="M18.5 9.2c1.1-.8 2.2-.9 3.1-.4-.1 1.8-1.1 3.2-2.8 4.2l-2.4 1.3c.8-1.8 1.5-3.4 2.1-5.1z" /></svg></span>
  return <span className="provider-mark provider-icon-mark provider-mark-openai" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M12 3.1a4 4 0 0 1 3.8 2.7 4 4 0 0 1 4.1 4.8 4 4 0 0 1-1.2 7.6 4 4 0 0 1-6.7 2.1 4 4 0 0 1-7-3.8A4 4 0 0 1 6.2 9a4 4 0 0 1 5.8-5.9Zm0 2a2 2 0 0 0-1.8 2.8l.4.8-.8.3a2 2 0 0 0-2.8 1.8 2 2 0 0 0 .3 1l.4.7-.7.4a2 2 0 0 0 .9 3.8 2 2 0 0 0 1-.3l.7-.4.3.8a2 2 0 0 0 3.9-.6v-.8l.8.1a2 2 0 0 0 2.3-2.8l-.4-.7.7-.4a2 2 0 0 0-1.1-3.7 2 2 0 0 0-1 .3l-.7.4-.3-.8A2 2 0 0 0 12 5.1Z" /></svg></span>
}

export default function SettingsPanel({ theme, setTheme, user, avatar, onAvatarUpdated, datasetId, filename, onUserUpdated, onDatasetDeleted, initialSection = null }) {
  const [section, setSection] = useState(initialSection)
  const [preferences, setPreferences] = useState(readPreferences)
  const [aiSettings, setAISettings] = useState(readAISettings)
  const [selectedProvider, setSelectedProvider] = useState('deepseek')
  const [profileName, setProfileName] = useState(user?.display_name || '')
  const [profileBusy, setProfileBusy] = useState(false)
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '', confirm: '' })
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => { localStorage.setItem('raota-preferences', JSON.stringify(preferences)) }, [preferences])
  useEffect(() => { localStorage.setItem('rmdas-ai-settings', JSON.stringify(aiSettings)) }, [aiSettings])
  useEffect(() => { setProfileName(user?.display_name || '') }, [user?.display_name])

  const setPreference = (key, value) => setPreferences(current => ({ ...current, [key]: value }))
  const setAlert = (key, value) => setPreferences(current => ({ ...current, alerts: { ...current.alerts, [key]: value } }))
  const feedback = (nextMessage = '', nextError = '') => { setMessage(nextMessage); setError(nextError); if (nextMessage) window.setTimeout(() => setMessage(''), 2400) }

  const sections = useMemo(() => [
    ['theme', '主题', THEME_OPTIONS.find(([key]) => key === theme)?.[1] || '鼠尾草绿'],
    ['workspace', '工作台偏好', '默认页面与展示方式'],
    ['shortcuts', '快捷键', '快速添加订单文件'],
    ['import', '数据导入', '平台、字段与清洗规则'],
    ['alerts', '预警与通知', '经营信号提醒'],
    ['ai', 'AI 服务商', aiSettings.activeProvider ? `${AI_PROVIDERS.find(provider => provider.key === aiSettings.activeProvider)?.label} 已启用` : '配置经营分析助手'],
    ['account', '账户与安全', '资料、密码与会话'],
    ['privacy', '数据与隐私', '数据集、缓存与保留'],
    ['about', '关于懂单儿', '版本与使用帮助']
  ], [theme, aiSettings.activeProvider])

  const updateName = async event => {
    event.preventDefault(); setError(''); setMessage('')
    if (!profileName.trim()) { setError('请输入显示名称'); return }
    setProfileBusy(true)
    try { const result = await updateProfile({ display_name: profileName.trim() }); onUserUpdated?.(result.user); feedback('显示名称已更新') } catch (err) { setError(err.message || '更新失败') } finally { setProfileBusy(false) }
  }

  const updatePassword = async event => {
    event.preventDefault(); setError(''); setMessage('')
    if (passwords.new_password.length < 8) { setError('新密码至少需要 8 位'); return }
    if (passwords.new_password !== passwords.confirm) { setError('两次输入的新密码不一致'); return }
    setPasswordBusy(true)
    try { await changePassword({ current_password: passwords.current_password, new_password: passwords.new_password }); setPasswords({ current_password: '', new_password: '', confirm: '' }); feedback('密码已更新，请妥善保管') } catch (err) { setError(err.message || '密码更新失败') } finally { setPasswordBusy(false) }
  }

  const removeDataset = async () => {
    if (!datasetId) { feedback('当前没有可删除的数据集'); return }
    if (!window.confirm(`确定删除“${filename || '当前数据集'}”吗？删除后无法恢复。`)) return
    try { await deleteDataset(datasetId); localStorage.removeItem('restaurant-analytics-dataset'); onDatasetDeleted?.(); feedback('当前数据集已删除') } catch (err) { setError(err.message || '数据集删除失败') }
  }

  const requestBrowserNotice = async () => {
    if (!('Notification' in window)) { setAlert('browserNotice', false); feedback('', '当前浏览器不支持通知'); return }
    const permission = await Notification.requestPermission()
    setAlert('browserNotice', permission === 'granted')
    feedback(permission === 'granted' ? '浏览器通知已开启' : '浏览器通知未开启')
  }

  const randomizeAvatar = () => { onAvatarUpdated?.(createGeneratedAvatar()); feedback('已生成新的随机头像') }
  const uploadAvatar = event => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    if (!file.type.startsWith('image/')) { feedback('', '请选择图片文件'); return }
    if (file.size > 2 * 1024 * 1024) { feedback('', '头像图片不能超过 2 MB'); return }
    const reader = new FileReader()
    reader.onload = () => { onAvatarUpdated?.({ type: 'image', src: reader.result }); feedback('自定义头像已保存') }
    reader.readAsDataURL(file)
  }

  const renderTheme = () => <div className="settings-section"><p className="settings-section-note">选择一套适合你的经营台风格</p><div className="theme-options">{THEME_OPTIONS.map(([key, label, description]) => <button className={`theme-option theme-option-${key}${theme === key ? ' active' : ''}`} type="button" onClick={() => { setTheme(key); feedback(`${label}主题已应用`) }} aria-pressed={theme === key} key={key}><i aria-hidden="true" /><span><b>{label}</b><small>{description}</small></span><em>{theme === key ? '✓' : ''}</em></button>)}</div></div>

  const renderWorkspace = () => <div className="settings-form settings-section"><label><span>默认打开页面</span><select value={preferences.defaultTab} onChange={event => setPreference('defaultTab', event.target.value)}><option value="upload">数据上传</option><option value="overview">运营概览</option><option value="products">商品分析</option><option value="users">用户分析</option><option value="anomalies">异常诊断</option><option value="forecast">智能预测</option><option value="screen">可视化大屏</option><option value="report">分析报告</option></select></label><label><span>默认时间范围</span><select value={preferences.dateRange} onChange={event => setPreference('dateRange', event.target.value)}><option value="7d">最近 7 天</option><option value="30d">最近 30 天</option><option value="90d">最近 90 天</option><option value="all">全部数据</option></select></label><label className="settings-check"><input type="checkbox" checked={preferences.showNumbers} onChange={event => setPreference('showNumbers', event.target.checked)} /><span>显示菜单编号</span></label><label className="settings-check"><input type="checkbox" checked={preferences.compactCharts} onChange={event => setPreference('compactCharts', event.target.checked)} /><span>使用紧凑图表布局</span></label><p className="settings-help">偏好设置会自动保存到当前浏览器。</p></div>

  const renderShortcuts = () => <div className="settings-form settings-section"><p className="settings-section-note">在任意页面快速打开文件选择器</p><label><span>添加订单文件</span><select value={preferences.uploadShortcut} onChange={event => setPreference('uploadShortcut', event.target.value)}><option value="mod+u">Ctrl / ⌘ + U</option><option value="mod+o">Ctrl / ⌘ + O</option><option value="none">不使用快捷键</option></select></label><p className="settings-help">Windows / Linux 使用 Ctrl，macOS 使用 ⌘。设置会自动保存。</p></div>

  const renderImport = () => <div className="settings-form settings-section"><label><span>默认平台</span><select value={preferences.platform} onChange={event => setPreference('platform', event.target.value)}><option value="all">自动识别</option><option value="meituan">美团</option><option value="wechat">微信/小程序</option><option value="eleme">饿了么</option></select></label><label><span>重复订单处理</span><select value={preferences.duplicatePolicy} onChange={event => setPreference('duplicatePolicy', event.target.value)}><option value="latest">保留最新记录</option><option value="first">保留首次记录</option><option value="mark">标记后保留</option></select></label><label className="settings-check"><input type="checkbox" checked={preferences.autoClean} onChange={event => setPreference('autoClean', event.target.checked)} /><span>上传后自动清洗异常值</span></label><p className="settings-help">这些规则会作为后续上传和分析时的默认偏好。</p></div>

  const renderAlerts = () => <div className="settings-form settings-section"><label className="settings-check"><input type="checkbox" checked={preferences.alerts.salesDrop} onChange={event => setAlert('salesDrop', event.target.checked)} /><span>营业额下降提醒</span></label><label className="settings-check"><input type="checkbox" checked={preferences.alerts.orderDrop} onChange={event => setAlert('orderDrop', event.target.checked)} /><span>订单量异常提醒</span></label><label className="settings-check"><input type="checkbox" checked={preferences.alerts.productChange} onChange={event => setAlert('productChange', event.target.checked)} /><span>商品销量变化提醒</span></label><label className="settings-check"><input type="checkbox" checked={preferences.alerts.repeatDrop} onChange={event => setAlert('repeatDrop', event.target.checked)} /><span>会员复购率下降提醒</span></label><button className="settings-action" type="button" onClick={requestBrowserNotice}><span className={`settings-status-dot${preferences.browserNotice ? ' enabled' : ''}`} />{preferences.browserNotice ? '浏览器通知已开启' : '开启浏览器通知'}</button></div>

  const selectedAIProvider = AI_PROVIDERS.find(provider => provider.key === selectedProvider) || AI_PROVIDERS[0]
  const selectedAIConfig = aiSettings.providers[selectedAIProvider.key] || selectedAIProvider.defaults
  const setAIField = (key, value) => setAISettings(current => ({ ...current, providers: { ...current.providers, [selectedAIProvider.key]: { ...current.providers[selectedAIProvider.key], [key]: value } } }))
  const toggleAIProvider = providerKey => {
    const provider = AI_PROVIDERS.find(item => item.key === providerKey)
    const config = aiSettings.providers[providerKey] || {}
    const missing = provider?.fields.find(field => !config[field.key]?.trim())
    if (missing) { feedback('', `请先填写${missing.label}，再启用服务商`); return }
    setAISettings(current => ({ ...current, activeProvider: current.activeProvider === providerKey ? '' : providerKey }))
    feedback(aiSettings.activeProvider === providerKey ? 'AI 服务商已停用' : `${AI_PROVIDERS.find(provider => provider.key === providerKey)?.label} 已启用`)
  }
  const saveAIConfig = () => {
    const missing = selectedAIProvider.fields.find(field => !selectedAIConfig[field.key]?.trim())
    if (missing) { feedback('', `请先填写${missing.label}`); return }
    setAISettings(current => ({ ...current, activeProvider: current.activeProvider || selectedAIProvider.key }))
    feedback(`${selectedAIProvider.label} 配置已保存`)
  }
  const renderAI = () => <div className="ai-settings-section settings-section"><div className="ai-provider-layout"><div className="ai-provider-list"><p className="settings-section-note">选择服务商，配置后可用于经营问答、报告解读和异常说明。</p>{AI_PROVIDERS.map(provider => { const configured = Boolean(aiSettings.providers[provider.key]?.apiKey?.trim()); const enabled = aiSettings.activeProvider === provider.key; return <button className={`ai-provider-item${selectedProvider === provider.key ? ' selected' : ''}`} type="button" onClick={() => setSelectedProvider(provider.key)} key={provider.key}><ProviderMark provider={provider} /><span className="ai-provider-copy"><b>{provider.label}</b><small>{configured ? '已配置' : '未配置'}</small></span><span className={`provider-toggle${enabled ? ' enabled' : ''}`} role="img" aria-label={enabled ? '已启用' : '未启用'} onClick={event => { event.stopPropagation(); toggleAIProvider(provider.key) }}>{enabled ? '✓' : ''}</span></button> })}</div><div className="ai-provider-detail"><div className="ai-detail-heading"><ProviderMark provider={selectedAIProvider} /><div><h3>{selectedAIProvider.label}</h3><p>{selectedAIProvider.help}</p></div><a className="provider-key-link" href={selectedAIProvider.keyUrl} target="_blank" rel="noreferrer">获取 API Key <span>↗</span></a></div><div className="settings-form">{selectedAIProvider.fields.map(field => <label key={field.key}><span>{field.label}</span><input type={field.secret ? 'password' : 'text'} value={selectedAIConfig[field.key] || ''} placeholder={field.placeholder} onChange={event => setAIField(field.key, event.target.value)} autoComplete="off" />{field.key === 'endpoint' && <small className="field-hint">支持 OpenAI 兼容接口，可替换为自部署或国内代理地址。</small>}</label>)}<button className="settings-primary" type="button" onClick={saveAIConfig}>保存配置</button><p className="settings-help">密钥仅保存在当前浏览器，不会显示在经营报表中。配置后点击左侧圆形按钮启用。</p></div></div></div></div>

  const renderAccount = () => <div className="settings-section account-settings"><div className="avatar-settings"><Avatar avatar={avatar} fallback={(user?.display_name || user?.email || '账户').slice(0, 2).toUpperCase()} /><div><strong>账户头像</strong><small>支持 JPG、PNG，最大 2 MB</small><div className="avatar-actions"><label className="settings-upload">上传图片<input type="file" accept="image/png,image/jpeg,image/webp" onChange={uploadAvatar} /></label><button className="settings-action avatar-random" type="button" onClick={randomizeAvatar}>随机生成</button></div></div></div><form className="settings-form" onSubmit={updateName}><label><span>显示名称</span><input value={profileName} onChange={event => setProfileName(event.target.value)} maxLength={80} /></label><label><span>登录邮箱</span><input value={user?.email || ''} readOnly /></label><button className="settings-primary" type="submit" disabled={profileBusy}>{profileBusy ? '保存中…' : '保存资料'}</button></form><form className="settings-form settings-form-divider" onSubmit={updatePassword}><strong>修改密码</strong><label><span>当前密码</span><input type="password" value={passwords.current_password} onChange={event => setPasswords(current => ({ ...current, current_password: event.target.value }))} autoComplete="current-password" /></label><label><span>新密码</span><input type="password" value={passwords.new_password} onChange={event => setPasswords(current => ({ ...current, new_password: event.target.value }))} minLength={8} autoComplete="new-password" /></label><label><span>确认新密码</span><input type="password" value={passwords.confirm} onChange={event => setPasswords(current => ({ ...current, confirm: event.target.value }))} minLength={8} autoComplete="new-password" /></label><button className="settings-primary" type="submit" disabled={passwordBusy}>{passwordBusy ? '更新中…' : '更新密码'}</button></form><div className="session-note"><span className="settings-status-dot enabled" />当前浏览器会话有效</div></div>

  const renderPrivacy = () => <div className="settings-section privacy-settings"><div className="privacy-dataset"><strong>当前数据集</strong><span>{filename || '尚未上传数据'}</span><small>{datasetId ? `ID: ${datasetId.slice(0, 8)}…` : '上传数据后会显示在这里'}</small></div><button className="settings-danger" type="button" onClick={removeDataset} disabled={!datasetId}>删除当前数据集</button><button className="settings-action" type="button" onClick={() => { localStorage.removeItem('raota-preferences'); setPreferences(DEFAULT_PREFERENCES); feedback('本地偏好已清除') }}>清除本地偏好</button><p className="settings-help">删除数据集会同时清理服务器上的分析文件，操作不可恢复。</p></div>

  const renderAbout = () => <div className="settings-section about-settings"><div className="about-brand"><strong>懂单儿</strong><span className="about-code">RODAS</span><span className="about-description">餐饮订单数据分析系统</span><small>版本 v2.4.0 · 2026</small></div><div className="about-owner"><strong>项目负责人</strong><b>莫永信</b><span>产品设计 · 系统开发</span><a href="mailto:mo485868@163.com">mo485868@163.com</a></div><dl><div><dt>项目定位</dt><dd>把平台报表，变成看得懂的经营答案。</dd></div><div><dt>数据处理</dt><dd>上传文件仅用于当前账户的经营分析。</dd></div><div><dt>支持格式</dt><dd>CSV、XLSX、XLS，单文件最大 50 MB。</dd></div></dl><p className="about-copyright">© 2026 莫永信 · 懂单儿</p></div>

  const content = { theme: renderTheme(), workspace: renderWorkspace(), shortcuts: renderShortcuts(), import: renderImport(), alerts: renderAlerts(), ai: renderAI(), account: renderAccount(), privacy: renderPrivacy(), about: renderAbout() }[section]
  return <div className={`settings-popover settings-center${section === 'ai' ? ' ai-settings-center' : ''}`} role="dialog" aria-label="设置"><div className="settings-header">{section ? <button className="settings-back" type="button" onClick={() => { setSection(null); setError(''); setMessage('') }}>‹ <span>设置</span></button> : <strong>设置</strong>}{section && <small>{sections.find(([key]) => key === section)?.[1]}</small>}</div>{!section && <div className="settings-menu">{sections.map(([key, label, summary]) => <button className="settings-menu-item" type="button" onClick={() => { setSection(key); setError(''); setMessage('') }} key={key}><span><b>{label}</b><small>{summary}</small></span><b>›</b></button>)}</div>}{section && content}{message && <p className="settings-message">{message}</p>}{error && <p className="settings-error">{error}</p>}</div>
}
