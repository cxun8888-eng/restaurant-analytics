const PROVIDERS = new Set(['deepseek', 'doubao', 'openai', 'gemini'])

export const AI_PROVIDER_LABELS = {
  deepseek: 'DeepSeek',
  doubao: '豆包',
  openai: 'OpenAI',
  gemini: 'Gemini'
}

/** Return the provider explicitly enabled for a single AI request. */
export function readActiveAIConfig() {
  try {
    const saved = JSON.parse(localStorage.getItem('rmdas-ai-settings') || 'null')
    const provider = saved?.activeProvider
    const config = saved?.providers?.[provider]
    if (!PROVIDERS.has(provider) || !config?.apiKey?.trim()) return null
    return { provider, ...config }
  } catch {
    return null
  }
}
