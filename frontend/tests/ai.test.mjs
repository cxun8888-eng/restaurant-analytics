import assert from 'node:assert/strict'
import test from 'node:test'

const values = new Map()
globalThis.localStorage = {
  getItem: key => values.get(key) ?? null,
  setItem: (key, value) => values.set(key, value),
  removeItem: key => values.delete(key)
}

const { readActiveAIConfig } = await import('../src/utils/ai.js')

test('readActiveAIConfig returns only the provider explicitly enabled by the user', () => {
  localStorage.setItem('rmdas-ai-settings', JSON.stringify({
    activeProvider: 'gemini',
    providers: {
      deepseek: { apiKey: 'configured-but-disabled', modelId: 'deepseek-chat' },
      gemini: { apiKey: 'selected-key', modelId: 'gemini-2.0-flash', endpoint: 'https://example.test' }
    }
  }))

  assert.deepEqual(readActiveAIConfig(), {
    provider: 'gemini',
    apiKey: 'selected-key',
    modelId: 'gemini-2.0-flash',
    endpoint: 'https://example.test'
  })
})

test('readActiveAIConfig does not fall back to a disabled provider', () => {
  localStorage.setItem('rmdas-ai-settings', JSON.stringify({
    activeProvider: '',
    providers: { deepseek: { apiKey: 'configured-but-disabled' } }
  }))

  assert.equal(readActiveAIConfig(), null)
})
