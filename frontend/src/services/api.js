const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, { ...options, credentials: 'include' })
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) { const error = new Error(payload.detail || '请求失败，请检查后端服务'); error.status = response.status; throw error }
  return payload
}

export function uploadDataset(file, onProgress, aiConfig = null) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${API}/datasets/upload`)
    xhr.withCredentials = true
    xhr.responseType = 'json'
    xhr.upload.onprogress = (event) => { if (event.lengthComputable) onProgress?.(Math.round(event.loaded / event.total * 100)) }
    xhr.onload = () => {
      const payload = xhr.response || {}
      if (xhr.status >= 200 && xhr.status < 300) resolve(payload)
      else reject(new Error(payload.detail || '文件上传失败'))
    }
    xhr.onerror = () => reject(new Error('无法连接后端服务'))
    xhr.onabort = () => reject(new Error('上传已取消'))
    const form = new FormData(); form.append('file', file); if (aiConfig) form.append('ai_config', JSON.stringify(aiConfig)); xhr.send(form)
  })
}

export const register = (payload) => request('/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
export const login = (payload) => request('/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
export const getCurrentUser = () => request('/auth/me')
export const logout = () => request('/auth/logout', { method: 'POST' })
export const updateProfile = (payload) => request('/auth/profile', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
export const changePassword = (payload) => request('/auth/password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
export const getHealth = () => request('/health')
export const getQuality = (id) => request(`/datasets/${id}/quality`)
export const getPreview = (id, limit = 50) => request(`/datasets/${id}/preview?limit=${limit}`)
export const getOverview = (id) => request(`/overview/${id}`)
export const getProducts = (id, params = {}) => request(`/products/${id}?min_support=${params.minSupport || 0.01}&min_lift=${params.minLift || 1}`)
export const getUsers = (id, clusters = 4) => request(`/users/${id}?clusters=${clusters}`)
export const getAnomalies = (id) => request(`/anomalies/${id}`)
export const getForecast = (id, days = 14) => request(`/forecast/${id}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ forecast_days: days }) })
export const getReport = (id) => request(`/report/${id}`)
export const deleteDataset = (id) => request(`/datasets/${id}`, { method: 'DELETE' })
