const AVATAR_COLORS = [
  ['#29453a', '#4b806d'],
  ['#294c5c', '#3f7891'],
  ['#303a35', '#687a78'],
  ['#5b456c', '#9a6fb1'],
  ['#6b4b3e', '#b88162'],
  ['#3f566f', '#6f9bc0']
]

export function avatarStorageKey(userId) {
  return `raota-avatar-${userId || 'guest'}`
}

export function createGeneratedAvatar() {
  const [color, accent] = AVATAR_COLORS[Math.floor(Math.random() * AVATAR_COLORS.length)]
  return { type: 'generated', color, accent, angle: Math.floor(Math.random() * 360) }
}

export function loadAvatar(userId) {
  try {
    const saved = JSON.parse(localStorage.getItem(avatarStorageKey(userId)) || 'null')
    if (saved?.type === 'generated' && saved.color && saved.accent) return saved
    if (saved?.type === 'image' && saved.src) return saved
  } catch { /* 使用新的随机头像 */ }
  const generated = createGeneratedAvatar()
  localStorage.setItem(avatarStorageKey(userId), JSON.stringify(generated))
  return generated
}

export function saveAvatar(userId, avatar) {
  localStorage.setItem(avatarStorageKey(userId), JSON.stringify(avatar))
}
