import { useEffect, useState } from 'react'
import AppShell, { NAV } from './components/AppShell'
import BrandMark from './components/BrandMark'
import { Toast } from './components/ui'
import { confirmDataset, getAnomalies, getCurrentUser, getForecast, getOverview, getPreview, getProducts, getQuality, getReport, getUsers, inspectDataset, logout as logoutRequest, updateAnomalyReview } from './services/api'
import ForecastPage from './pages/ForecastPage'
import OverviewPage from './pages/OverviewPage'
import ProductPage from './pages/ProductsPage'
import ReportPage from './pages/ReportPage'
import ScreenPage from './pages/ScreenPage'
import UploadPage from './pages/UploadPage'
import UsersPage from './pages/UsersPage'
import AnomaliesPage from './pages/AnomaliesPage'
import AuthPage from './pages/AuthPage'
import LandingPage from './pages/LandingPage'
import PublishPage from './pages/PublishPage'
import { readActiveAIConfig } from './utils/ai'
import { buildReportExportHtml, buildWordExportHtml } from './utils/reportExport'
import { parsePublicationReceipt } from './utils/publishBridge'

function readRoute() { const route = window.location.hash.replace('#', ''); return NAV.some(([key]) => key === route) ? route : 'upload' }
function readDataset() { try { return JSON.parse(localStorage.getItem('restaurant-analytics-dataset') || 'null') || {} } catch { return {} } }
function readEntryRoute() { const path = window.location.pathname.replace(/\/+$/, '') || '/'; const queryMode = new URLSearchParams(window.location.search).get('mode'); const mode = queryMode === 'register' || path.endsWith('/register') ? 'register' : 'login'; return { isAuth: path.endsWith('/login') || path.endsWith('/register') || queryMode === 'login' || queryMode === 'register', mode } }

export default function App() {
  const [tab, setTab] = useState(readRoute); const [user, setUser] = useState(null); const [authReady, setAuthReady] = useState(false); const [datasetId, setDatasetId] = useState(''); const [filename, setFilename] = useState(''); const [quality, setQuality] = useState(null); const [preview, setPreview] = useState(null)
  const [inspection, setInspection] = useState(null)
  const [publicationReceipt, setPublicationReceipt] = useState(null)
  const [overview, setOverview] = useState(null); const [products, setProducts] = useState(null); const [users, setUsers] = useState(null); const [forecast, setForecast] = useState(null); const [anomalies, setAnomalies] = useState(null); const [report, setReport] = useState(''); const [reportData, setReportData] = useState(null); const [reportInfo, setReportInfo] = useState(null)
  const [busy, setBusy] = useState(false); const [progress, setProgress] = useState(0); const [toast, setToast] = useState(null); const [error, setError] = useState(''); const [entryRoute, setEntryRoute] = useState(readEntryRoute); const [openSettingsRequest, setOpenSettingsRequest] = useState(0)

  useEffect(() => {
    const onHash = () => {
      try {
        const receipt = parsePublicationReceipt(window.location.hash)
        if (receipt) {
          setPublicationReceipt(receipt)
          setTab('publish')
          window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#publish`)
          return
        }
        setTab(readRoute())
      } catch (receiptError) {
        setTab('publish')
        window.history.replaceState(null, '', `${window.location.pathname}${window.location.search}#publish`)
        setToast({ type: 'error', message: receiptError?.message || '无法读取平台发布回执' })
      }
    }
    onHash()
    window.addEventListener('hashchange', onHash)
    return () => window.removeEventListener('hashchange', onHash)
  }, [])
  useEffect(() => { const onPopState = () => setEntryRoute(readEntryRoute()); window.addEventListener('popstate', onPopState); return () => window.removeEventListener('popstate', onPopState) }, [])
  useEffect(() => {
    getCurrentUser().then(payload => setUser(payload.user)).catch(() => setUser(null)).finally(() => setAuthReady(true))
  }, [])
  useEffect(() => {
    if (!user) return
    const savedDataset = readDataset()
    if (!savedDataset.id) {
      if (readRoute() === 'publish') return
      try {
        const preferences = JSON.parse(localStorage.getItem('raota-preferences') || '{}')
        if (NAV.some(([key]) => key === preferences.defaultTab)) { window.location.hash = preferences.defaultTab; setTab(preferences.defaultTab) }
      } catch { /* 使用默认上传页 */ }
      return
    }
    setDatasetId(savedDataset.id)
    setFilename(savedDataset.filename || '')
    loadDataset(savedDataset.id, readRoute() !== 'publish')
    // 后端数据已持久化，登录后自动恢复当前账户最近一次工作区。
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id])
  useEffect(() => {
    const onKey = event => {
      let shortcut = 'mod+u'
      try { shortcut = JSON.parse(localStorage.getItem('raota-preferences') || '{}').uploadShortcut || shortcut } catch { /* 使用默认快捷键 */ }
      if (shortcut === 'none') return
      const key = shortcut.split('+').pop()
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === key) {
        event.preventDefault()
        document.querySelector('.dropzone input')?.click()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const fail = (err) => { const message = err?.message || '操作失败'; setError(message); setToast({ type: 'error', message }); }
  const loadDataset = async (id, navigate = true) => {
    setBusy(true); setError('')
    try { const [o, p, u, a, q, sample] = await Promise.all([getOverview(id), getProducts(id), getUsers(id), getAnomalies(id), getQuality(id), getPreview(id)]); setOverview(o); setProducts(p); setUsers(u); setAnomalies(a); setQuality(q.quality); setPreview(sample); if (navigate) { window.location.hash = 'overview'; setTab('overview'); setToast({ type: 'success', message: '数据已导入，分析结果已准备好' }) } }
    catch (err) { if ([401, 403, 404].includes(err.status)) { setDatasetId(''); setFilename(''); localStorage.removeItem('restaurant-analytics-dataset') } fail(err) } finally { setBusy(false) }
  }
  const handleUpload = async (file) => {
    if (!file) return
    const valid = ['.csv', '.xlsx', '.xls'].some(ext => file.name.toLowerCase().endsWith(ext)); if (!valid) { fail(new Error('仅支持 CSV、XLSX 或 XLS 文件')); return }
    setBusy(true); setProgress(0); setError('')
    try { const result = await inspectDataset(file, setProgress, readActiveAIConfig()); setInspection(result); setQuality(result.quality); setPreview({ columns: result.columns || [], rows: result.sample_rows || [] }); setToast({ type: 'success', message: '文件已检查，请确认字段识别结果' }) }
    catch (err) { fail(err) } finally { setBusy(false); setProgress(0) }
  }
  const cancelInspection = () => { setInspection(null); setQuality(null); setPreview(null); setError(''); setToast(null) }
  const handleConfirm = async mapping => {
    if (!inspection?.inspection_id) return
    setBusy(true); setError('')
    try {
      const result = await confirmDataset(inspection.inspection_id, mapping)
      setDatasetId(result.dataset_id); setFilename(result.filename || inspection.filename); localStorage.setItem('restaurant-analytics-dataset', JSON.stringify({ id: result.dataset_id, filename: result.filename || inspection.filename })); setInspection(null); await loadDataset(result.dataset_id)
    } catch (err) { throw err } finally { setBusy(false) }
  }
  const runForecast = async () => { setBusy(true); setError(''); try { setForecast(await getForecast(datasetId)); setToast({ type: 'success', message: '预测结果已更新' }) } catch (err) { fail(err) } finally { setBusy(false) } }
  const reviewAnomaly = async (orderId, status) => {
    try { await updateAnomalyReview(datasetId, orderId, status); setAnomalies(await getAnomalies(datasetId)); setToast({ type: 'success', message: '复核状态已保存' }) }
    catch (err) { fail(err) }
  }
  const generateReport = async () => { setBusy(true); setError(''); try { const result = await getReport(datasetId, readActiveAIConfig()); setReport(result.report || ''); setReportData(result.ai_report || null); setReportInfo({ mode: result.report_mode || 'rules', provider: result.provider, model: result.model, warning: result.ai_warning }); setToast({ type: 'success', message: result.report_mode === 'ai' ? 'AI 经营解读已生成' : result.ai_warning || '本地经营报告已生成' }) } catch (err) { fail(err) } finally { setBusy(false) } }
  const downloadReport = (format = 'md') => {
    if (!report) return
    const now = new Date()
    const exportDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
    const baseName = `懂单儿_${exportDate}_分析报告`
    const triggerDownload = (blob, extension) => { const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = `${baseName}.${extension}`; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000) }
    const exportHtml = buildReportExportHtml({ report, reportData, reportInfo, filename, includeAppendix: false })
    if (format === 'word') {
      triggerDownload(new Blob(['\ufeff', buildWordExportHtml({ report, reportData, reportInfo, filename })], { type: 'application/msword;charset=utf-8' }), 'doc')
      setToast({ type: 'success', message: 'Word 报告下载已开始' })
      return
    }
    if (format === 'pdf') {
      const printWindow = window.open('', '_blank', 'width=960,height=760')
      if (!printWindow) { setToast({ type: 'error', message: '打印窗口被浏览器拦截，请允许弹窗后重试' }); return }
      printWindow.document.write(exportHtml)
      printWindow.document.close(); printWindow.document.title = baseName; printWindow.focus(); window.setTimeout(() => { printWindow.print(); printWindow.close() }, 250)
      setToast({ type: 'success', message: '已打开 PDF 打印窗口，请选择“另存为 PDF”' })
      return
    }
    triggerDownload(new Blob([report], { type: 'text/markdown;charset=utf-8' }), 'md')
    setToast({ type: 'success', message: 'Markdown 报告下载已开始' })
  }
  const enterAuth = mode => { const safeMode = mode === 'register' ? 'register' : 'login'; setEntryRoute({ isAuth: true, mode: safeMode }); window.history.pushState({ auth: safeMode }, '', `/zh/${safeMode}`); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const leaveAuth = () => { setEntryRoute({ isAuth: false, mode: 'login' }); window.history.pushState({}, '', '/zh'); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const handleAuthenticated = nextUser => { setUser(nextUser); setEntryRoute({ isAuth: false, mode: 'login' }); window.history.replaceState({}, '', '/zh') }
  const handleLogout = async () => {
    try { await logoutRequest() } catch { /* 即使会话已过期，也要清理本地界面状态。 */ }
    setUser(null); setDatasetId(''); setFilename(''); setQuality(null); setPreview(null); setOverview(null); setProducts(null); setUsers(null); setForecast(null); setAnomalies(null); setReport(''); setReportData(null); setReportInfo(null); localStorage.removeItem('restaurant-analytics-dataset'); window.location.hash = 'upload'; setTab('upload'); setEntryRoute({ isAuth: false, mode: 'login' }); window.history.replaceState({}, '', '/zh')
  }
  const handleUserUpdated = updatedUser => setUser(updatedUser)
  const handleDatasetDeleted = () => { setDatasetId(''); setFilename(''); setQuality(null); setPreview(null); setOverview(null); setProducts(null); setUsers(null); setForecast(null); setAnomalies(null); setReport(''); setReportData(null); setReportInfo(null); window.location.hash = 'upload'; setTab('upload'); setToast({ type: 'success', message: '当前数据集已删除' }) }
  const view = { upload: <UploadPage quality={quality} preview={preview} inspection={inspection} onUpload={handleUpload} onConfirm={handleConfirm} onCancelInspection={cancelInspection} busy={busy} progress={progress} onOpenSettings={() => setOpenSettingsRequest(current => current + 1)} />, overview: <OverviewPage overview={overview} products={products} />, products: <ProductPage products={products} />, users: <UsersPage users={users} />, anomalies: <AnomaliesPage data={anomalies} onReview={reviewAnomaly} />, forecast: <ForecastPage forecast={forecast} onForecast={runForecast} />, screen: <ScreenPage overview={overview} products={products} />, report: <ReportPage report={report} reportData={reportData} reportInfo={reportInfo} onGenerate={generateReport} onDownload={downloadReport} busy={busy} />, publish: <PublishPage user={user} receipt={publicationReceipt} onReceiptHandled={() => setPublicationReceipt(null)} onNotify={setToast} /> }

  if (!authReady) return <main className="auth-page auth-loading"><BrandMark variant="square" className="auth-loading-mark" /><span>正在连接经营台…</span></main>
  if (!user && !entryRoute.isAuth) return <LandingPage onAuth={enterAuth} />
  if (!user) return <AuthPage initialMode={entryRoute.mode} onAuthenticated={handleAuthenticated} onBack={leaveAuth} />
  return <><AppShell tab={tab} setTab={key => { window.location.hash = key; setTab(key) }} user={user} onLogout={handleLogout} onUserUpdated={handleUserUpdated} onDatasetDeleted={handleDatasetDeleted} filename={filename} datasetId={datasetId} error={error} busy={busy} openSettingsRequest={openSettingsRequest} openSettingsSection="ai">{view[tab]}</AppShell><Toast toast={toast} onClose={() => setToast(null)} /></>
}
