const PROVIDERS = new Set(['deepseek', 'doubao', 'openai', 'gemini'])

/** Return the active provider config for a single upload request. */
export function readActiveAIConfig() {
  try {
    const saved = JSON.parse(localStorage.getItem('rmdas-ai-settings') || 'null')
    const candidates = [saved?.activeProvider, ...PROVIDERS]
    const provider = candidates.find(key => PROVIDERS.has(key) && saved?.providers?.[key]?.apiKey?.trim())
    const config = saved?.providers?.[provider]
    if (!provider || !config?.apiKey?.trim()) return null
    return { provider, ...config }
  } catch {
    return null
  }
}
