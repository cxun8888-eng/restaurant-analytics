import assert from 'node:assert/strict'
import test from 'node:test'
import { buildPublishHandoffUrl, normalizePublishBridgeStatus, parsePublicationReceipt, parsePublishTags, PUBLISH_SOURCE } from '../src/utils/publishBridge.js'

function decodeBase64Url(value) {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '=')
  return Buffer.from(normalized, 'base64').toString('utf8')
}

function encodeReceipt(value) {
  return Buffer.from(JSON.stringify(value), 'utf8').toString('base64url')
}

test('buildPublishHandoffUrl creates a bounded public draft for the selected official platform', () => {
  const url = new URL(buildPublishHandoffUrl({
    platform: 'xiaohongshu',
    title: '  晚市新品  ',
    content: '今晚见。',
    tags: ['#新品', '新品', '晚餐']
  }))
  const encoded = new URLSearchParams(url.hash.slice(1)).get('publish_review_draft')
  const payload = JSON.parse(decodeBase64Url(encoded))

  assert.equal(url.hostname, 'creator.xiaohongshu.com')
  assert.equal(payload.version, 1)
  assert.equal(payload.source, PUBLISH_SOURCE)
  assert.equal(payload.platform, 'xiaohongshu')
  assert.equal(payload.title, '晚市新品')
  assert.deepEqual(payload.tags, ['新品', '晚餐'])
})

test('parsePublishTags normalizes Chinese separators and removes duplicates', () => {
  assert.deepEqual(parsePublishTags('#新品，新品, 晚餐\n城市探店'), ['新品', '晚餐', '城市探店'])
  assert.deepEqual(parsePublishTags('#周末套餐 #学生党 #美食推荐'), ['周末套餐', '学生党', '美食推荐'])
})

test('parsePublicationReceipt keeps supported metrics and official work links', () => {
  const encoded = encodeReceipt({
    version: 1,
    platform: 'douyin',
    outcome: 'resolved',
    returnMode: 'workspace',
    completedAt: '2026-09-01T02:00:00.000Z',
    workUrl: 'https://www.douyin.com/video/123',
    title: '晚市新品',
    metrics: { views: 1200, likes: 80, invalid: 'not-a-number' }
  })
  const receipt = parsePublicationReceipt(`#publication_receipt=${encoded}`)

  assert.equal(receipt.workUrl, 'https://www.douyin.com/video/123')
  assert.deepEqual(receipt.metrics, { views: 1200, likes: 80 })
})

test('parsePublicationReceipt removes untrusted work links and rejects unsupported contracts', () => {
  const encoded = encodeReceipt({
    version: 1,
    platform: 'xiaohongshu',
    outcome: 'triggered',
    returnMode: 'workspace',
    completedAt: '2026-09-01T02:00:00.000Z',
    workUrl: 'https://example.com/phishing'
  })
  assert.equal(parsePublicationReceipt(`#publication_receipt=${encoded}`).workUrl, undefined)
  assert.throws(() => parsePublicationReceipt(`#publication_receipt=${encodeReceipt({ version: 2 })}`), /不受支持/)
})

test('normalizePublishBridgeStatus only marks an exact configured and permitted bridge ready', () => {
  const expected = { origin: 'http://localhost:4815', callbackPath: '/zh' }
  const ready = normalizePublishBridgeStatus({
    ok: true,
    version: '0.1.2',
    appBaseUrl: 'http://localhost:4815',
    callbackPath: '/zh',
    debuggerEnabled: true
  }, expected)
  assert.equal(ready.ready, true)

  const wrongCallback = normalizePublishBridgeStatus({ ...ready, ok: true, callbackPath: '/index.html' }, expected)
  assert.equal(wrongCallback.detected, true)
  assert.equal(wrongCallback.ready, false)
  assert.equal(wrongCallback.callbackMatches, false)

  const spoofed = normalizePublishBridgeStatus({ ok: true, version: 'latest', appBaseUrl: expected.origin, callbackPath: '/zh', debuggerEnabled: true }, expected)
  assert.equal(spoofed.detected, false)
  assert.equal(spoofed.ready, false)
})
