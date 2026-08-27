import { useEffect, useState } from 'react'

import { login, register } from '../services/api'
import BrandMark from '../components/BrandMark'

export default function AuthPage({ onAuthenticated, initialMode = 'login', onBack }) {
  const [mode, setMode] = useState(initialMode)
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { setMode(initialMode); setError('') }, [initialMode])

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setError('')
  }

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const payload = mode === 'register'
        ? await register({ display_name: displayName, email, password })
        : await login({ email, password })
      onAuthenticated(payload.user)
    } catch (err) {
      setError(err.message || '操作失败，请稍后重试')
    } finally {
      setBusy(false)
    }
  }

  return <main className="auth-page"><section className="auth-panel">{onBack && <button className="auth-back" type="button" onClick={onBack}>← 返回首页</button>}<div className="auth-brand"><BrandMark variant="light" /><div className="auth-brand-copy"><b>懂单儿</b><small className="brand-code">RODAS</small><small className="brand-description">餐饮订单数据分析系统</small></div></div><div className="auth-intro"><p className="eyebrow">RESTAURANT ORDER DATA ANALYSIS / 2026</p><h1>{mode === 'login' ? '欢迎回来。' : '建立你的经营台。'}</h1><p>{mode === 'login' ? '登录后继续查看你的订单数据和经营洞察。' : '注册一个账户，开始整理订单并发现经营信号。'}</p></div><div className="auth-tabs" role="tablist" aria-label="账户操作"><button className={mode === 'login' ? 'active' : ''} type="button" onClick={() => switchMode('login')}>登录</button><button className={mode === 'register' ? 'active' : ''} type="button" onClick={() => switchMode('register')}>注册</button></div><form className="auth-form" onSubmit={submit}>{mode === 'register' && <label><span>显示名称</span><input value={displayName} onChange={event => setDisplayName(event.target.value)} autoComplete="name" placeholder="例如：你的餐厅名称" required /></label>}<label><span>邮箱</span><input type="email" value={email} onChange={event => setEmail(event.target.value)} autoComplete="email" placeholder="you@example.com" required /></label><label><span>密码</span><input type="password" value={password} onChange={event => setPassword(event.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder={mode === 'register' ? '至少 8 位字符' : '请输入密码'} minLength={mode === 'register' ? 8 : 1} required /></label>{error && <p className="auth-error" role="alert">{error}</p>}<button className="auth-submit" type="submit" disabled={busy}>{busy ? '处理中…' : mode === 'login' ? '登录工作台' : '创建账户'}</button></form><p className="auth-footnote">把平台报表，变成看得懂的经营答案。</p></section></main>
}
