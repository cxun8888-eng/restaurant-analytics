import { useEffect, useRef, useState } from 'react'
import { Icon } from './ui'
import BrandMark from './BrandMark'
import Avatar from './Avatar'
import SettingsPanel from './SettingsPanel'
import { loadAvatar, saveAvatar } from '../utils/avatar'

export const NAV = [['upload', '数据上传', 'upload'], ['overview', '运营概览', 'overview'], ['products', '商品分析', 'products'], ['users', '用户分析', 'users'], ['anomalies', '异常诊断', 'anomalies'], ['forecast', '智能预测', 'forecast'], ['screen', '可视化大屏', 'screen'], ['report', '分析报告', 'report']]

export default function AppShell({ tab, setTab, filename, datasetId, error, busy, user, onLogout, onUserUpdated, onDatasetDeleted, openSettingsRequest = 0, openSettingsSection = null, children }) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('raota-sidebar-collapsed') === '1')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [settingsSection, setSettingsSection] = useState(null)
  const [avatar, setAvatar] = useState(() => loadAvatar(user?.id))
  const [theme, setTheme] = useState(() => {
    const savedTheme = localStorage.getItem('raota-theme')
    const normalizedTheme = savedTheme === 'terracotta' ? 'ink' : savedTheme
    return ['sage', 'ocean', 'ink'].includes(normalizedTheme) ? normalizedTheme : 'sage'
  })
  const settingsAreaRef = useRef(null)
  const currentTitle = NAV.find(([key]) => key === tab)?.[1] || '餐饮经营分析'
  const displayName = user?.display_name || user?.email || '账户'
  const avatarText = displayName.slice(0, 2).toUpperCase()

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('raota-theme', theme)
  }, [theme])
  useEffect(() => {
    if (!settingsOpen) return undefined
    const closeOnOutsideClick = event => {
      if (!settingsAreaRef.current?.contains(event.target)) setSettingsOpen(false)
    }
    document.addEventListener('pointerdown', closeOnOutsideClick)
    return () => document.removeEventListener('pointerdown', closeOnOutsideClick)
  }, [settingsOpen])
  useEffect(() => { setAvatar(loadAvatar(user?.id)) }, [user?.id])
  useEffect(() => { if (openSettingsRequest) { setSettingsSection(openSettingsSection); setSettingsOpen(true) } }, [openSettingsRequest, openSettingsSection])

  const toggleSidebar = () => setCollapsed(current => { const next = !current; localStorage.setItem('raota-sidebar-collapsed', next ? '1' : '0'); return next })
  const toggleSettings = () => setSettingsOpen(current => { if (!current) setSettingsSection(null); return !current })
  const updateAvatar = nextAvatar => { saveAvatar(user?.id, nextAvatar); setAvatar(nextAvatar) }
  const navigate = key => {
    setTab(key)
    window.history.replaceState(null, '', `#${key}`)
    window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
  }

  return <div className="app">
    <aside className={`sidebar${collapsed ? ' sidebar-collapsed' : ''}`}>
      <div className="brand"><BrandMark variant="square" /><div className="brand-copy"><b>懂单儿</b><small className="brand-code">RODAS</small><small className="brand-description">餐饮订单数据分析系统</small></div><button className="sidebar-toggle" type="button" onClick={toggleSidebar} aria-label={collapsed ? '展开侧边栏' : '收起侧边栏'} title={collapsed ? '展开侧边栏' : '收起侧边栏'}>{collapsed ? '›' : '‹'}</button></div>
      <p className="side-label">工作台</p>
      <nav>{NAV.map(([key, label, icon], index) => <button className={tab === key ? 'active' : ''} onClick={() => navigate(key)} aria-current={tab === key ? 'page' : undefined} key={key}><span className="nav-index">0{index + 1}</span><Icon name={icon} /><span className="nav-label">{label}</span></button>)}</nav>
      <div className="side-bottom"><div className="sidebar-profile"><div className="sidebar-user"><Avatar avatar={avatar} fallback={avatarText} /><span className="user-copy"><strong>{displayName}</strong><small>{user?.email || '已登录账户'}</small></span></div><div className="account-actions"><button className="sidebar-logout" type="button" onClick={onLogout} title={`退出登录（${user?.email || '账户'}）`}><Icon name="logout" /><span>退出登录</span></button><div className="settings-control" ref={settingsAreaRef}><button className="sidebar-settings" type="button" onClick={toggleSettings} aria-expanded={settingsOpen} aria-label="设置" title="设置"><Icon name="settings" /></button>{settingsOpen && <SettingsPanel initialSection={settingsSection} theme={theme} setTheme={setTheme} user={user} avatar={avatar} onAvatarUpdated={updateAvatar} datasetId={datasetId} filename={filename} onUserUpdated={onUserUpdated} onDatasetDeleted={onDatasetDeleted} />}</div></div></div></div>
    </aside>
<div className="content"><header className="topbar"><div className="breadcrumbs"><span>工作台</span><b>/</b><strong>{currentTitle}</strong></div></header><div className="page"><div className={`page-title${['overview', 'products', 'users', 'anomalies', 'forecast', 'screen', 'report'].includes(tab) ? ` page-title-${tab}` : ''}`}><div><p className="eyebrow">OPERATING SYSTEM <span>/</span> 2026</p><h1>{currentTitle}</h1><p>{tab === 'upload' ? '把订单流水变成下一个经营动作。' : '从数据到行动，每一个数字都应该有用。'}</p></div></div>{error && <div className="error">{error}</div>}{busy && tab !== 'upload' && tab !== 'report' && <div className="loading"><span />正在处理数据…</div>}{children}</div></div>
  </div>
}
