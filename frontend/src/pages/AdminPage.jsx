import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  clearAdminUserData,
  deleteAdminDataset,
  deleteAdminUser,
  getAdminOverview,
  purgeAdminPending,
  setAdminUserStatus
} from '../services/api'

const ACTION_LABELS = {
  user_enabled: '启用账号',
  user_disabled: '停用账号',
  dataset_deleted: '删除数据集',
  user_data_cleared: '清理账号数据',
  user_deleted: '删除账号',
  expired_pending_purged: '清理临时文件'
}

const formatBytes = value => {
  const bytes = Number(value || 0)
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`
}

const formatDate = value => {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('zh-CN', { hour12: false })
}

export default function AdminPage({ currentUser, onNotify }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [query, setQuery] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [actionBusy, setActionBusy] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      setData(await getAdminOverview())
    } catch (err) {
      setError(err?.message || '管理数据加载失败')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    if (!confirm) return undefined
    const close = event => { if (event.key === 'Escape' && !actionBusy) setConfirm(null) }
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [confirm, actionBusy])

  const users = useMemo(() => {
    const token = query.trim().toLowerCase()
    return (data?.users || []).filter(user => !token || `${user.email} ${user.display_name}`.toLowerCase().includes(token))
  }, [data?.users, query])

  const requestAction = action => setConfirm(action)
  const executeAction = async () => {
    if (!confirm?.run) return
    setActionBusy(true)
    try {
      const result = await confirm.run()
      onNotify?.({ type: 'success', message: result?.message || '管理操作已完成' })
      setConfirm(null)
      await load()
    } catch (err) {
      setError(err?.message || '管理操作失败')
      onNotify?.({ type: 'error', message: err?.message || '管理操作失败' })
    } finally {
      setActionBusy(false)
    }
  }

  const summary = data?.summary || {}
  return <main className="admin-page">
    <section className="admin-ledger" aria-label="系统保管概况">
      <div className="admin-ledger-intro">
        <span><i /> ADMIN LIVE</span>
        <h2>懂单儿数据保管账</h2>
        <p>管理账号和存储，不展示用户订单明细。</p>
      </div>
      <div className="admin-ledger-metrics">
        <div><span>账号</span><strong>{summary.user_count ?? '—'}</strong><small>{summary.active_user_count ?? 0} 个启用</small></div>
        <div><span>数据集</span><strong>{summary.dataset_count ?? '—'}</strong><small>{formatBytes(summary.dataset_bytes)}</small></div>
        <div><span>临时文件</span><strong>{summary.pending_count ?? '—'}</strong><small>{formatBytes(summary.pending_bytes)}</small></div>
        <div><span>待清理</span><strong>{summary.expired_pending_count ?? '—'}</strong><small>已过期文件</small></div>
      </div>
    </section>

    {error && <div className="admin-error" role="alert"><span>!</span><p>{error}</p><button type="button" onClick={load}>重新加载</button></div>}
    {loading && !data ? <div className="admin-loading"><span />正在核对账号与存储…</div> : <>
      <section className="admin-section">
        <header className="admin-section-head">
          <div><p>ACCOUNT CONTROL</p><h3>账号管理</h3><span>停用后用户会立即失去访问权限；删除账号会一并删除其数据。</span></div>
          <label className="admin-search"><span>⌕</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="搜索邮箱或名称" /></label>
        </header>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead><tr><th>账号</th><th>状态</th><th>数据保管</th><th>注册时间</th><th>操作</th></tr></thead>
            <tbody>{users.map(user => {
              const isSelf = user.id === currentUser?.id
              return <tr key={user.id}>
                <td><div className="admin-account"><span>{(user.display_name || user.email).slice(0, 1).toUpperCase()}</span><div><strong>{user.display_name}</strong><small>{user.email}</small></div></div></td>
                <td><span className={`admin-status ${user.is_active ? 'is-active' : 'is-disabled'}`}><i />{user.is_active ? '启用' : '停用'}</span>{user.is_admin && <span className="admin-role">管理员</span>}</td>
                <td><strong className="admin-data-count">{user.dataset_count} 份</strong><small className="admin-data-meta">{formatBytes(user.dataset_bytes)} · {user.pending_count} 个临时文件</small></td>
                <td className="admin-date">{formatDate(user.created_at)}</td>
                <td><div className="admin-row-actions">
                  {isSelf || user.is_admin ? <span className="admin-protected">当前管理员 · 已保护</span> : <>
                    <button type="button" onClick={() => requestAction({ title: user.is_active ? '停用这个账号？' : '重新启用这个账号？', body: user.is_active ? `${user.email} 将立即无法登录懂单儿，数据仍会保留。` : `${user.email} 将恢复登录和数据访问权限。`, label: user.is_active ? '确认停用' : '确认启用', run: () => setAdminUserStatus(user.id, !user.is_active) })}>{user.is_active ? '停用' : '启用'}</button>
                    <button type="button" disabled={!user.dataset_count && !user.pending_count} onClick={() => requestAction({ title: '清理这个账号的数据？', body: `将永久删除 ${user.email} 的 ${user.dataset_count} 份数据集和临时上传文件，但保留账号。`, label: '确认清理数据', danger: true, run: () => clearAdminUserData(user.id) })}>清数据</button>
                    <button className="is-danger" type="button" onClick={() => requestAction({ title: '删除账号和全部数据？', body: `${user.email} 的账号、数据集和临时文件都会被永久删除，此操作无法撤销。`, label: '永久删除', danger: true, run: () => deleteAdminUser(user.id) })}>删除</button>
                  </>}
                </div></td>
              </tr>
            })}</tbody>
          </table>
          {!users.length && <div className="admin-empty">没有符合条件的账号</div>}
        </div>
      </section>

      <div className="admin-lower-grid">
        <section className="admin-section admin-datasets">
          <header className="admin-section-head"><div><p>STORAGE INDEX</p><h3>数据集目录</h3><span>只列出文件信息，不读取订单内容。</span></div></header>
          <div className="admin-dataset-list">
            {(data?.datasets || []).map(item => <article key={item.id}>
              <div className="admin-file-mark">{item.filename?.split('.').pop()?.slice(0, 3).toUpperCase() || 'DATA'}</div>
              <div><strong title={item.filename}>{item.filename}</strong><span>{item.owner_email}</span><small>{item.row_count.toLocaleString()} 行 · {formatBytes(item.size_bytes)} · {formatDate(item.created_at)}</small></div>
              <button type="button" onClick={() => requestAction({ title: '删除这个数据集？', body: `${item.filename} 将从服务器永久删除，所属用户之后无法再访问。`, label: '永久删除', danger: true, run: () => deleteAdminDataset(item.id) })}>删除</button>
            </article>)}
            {!data?.datasets?.length && <div className="admin-empty">服务器中暂无已确认的数据集</div>}
          </div>
        </section>

        <section className="admin-section admin-audit">
          <header className="admin-section-head"><div><p>AUDIT TRAIL</p><h3>管理操作记录</h3><span>最近 80 条管理动作。</span></div><button className="admin-purge" type="button" onClick={() => requestAction({ title: '清理过期临时文件？', body: '只删除超过保留期限的待确认上传文件，不影响已确认的数据集。', label: '开始清理', run: purgeAdminPending })}>清理过期文件</button></header>
          <div className="admin-audit-list">
            {(data?.audit_logs || []).map(log => <article key={log.id}><i /><div><strong>{ACTION_LABELS[log.action] || log.action}</strong><span>{log.admin_email}</span></div><time>{formatDate(log.created_at)}</time></article>)}
            {!data?.audit_logs?.length && <div className="admin-empty">还没有管理操作记录</div>}
          </div>
        </section>
      </div>
    </>}

    {confirm && <div className="admin-dialog-backdrop" onMouseDown={event => { if (event.target === event.currentTarget && !actionBusy) setConfirm(null) }}>
      <section className="admin-dialog" role="alertdialog" aria-modal="true" aria-labelledby="admin-dialog-title">
        <span className={`admin-dialog-mark${confirm.danger ? ' is-danger' : ''}`}>{confirm.danger ? '!' : '✓'}</span>
        <p>MANAGEMENT CHECK</p>
        <h3 id="admin-dialog-title">{confirm.title}</h3>
        <div>{confirm.body}</div>
        <footer><button type="button" onClick={() => setConfirm(null)} disabled={actionBusy}>取消</button><button className={confirm.danger ? 'is-danger' : ''} type="button" onClick={executeAction} disabled={actionBusy}>{actionBusy ? '正在处理…' : confirm.label}</button></footer>
      </section>
    </div>}
  </main>
}
