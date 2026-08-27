export default function Avatar({ avatar, fallback, className = '' }) {
  const generatedStyle = avatar?.type === 'generated'
    ? { '--avatar-color': avatar.color, '--avatar-accent': avatar.accent, '--avatar-angle': `${avatar.angle || 0}deg` }
    : undefined
  return <span className={`avatar${avatar?.type === 'generated' ? ' avatar-generated' : ''}${avatar?.type === 'image' ? ' avatar-image' : ''} ${className}`.trim()} style={generatedStyle} aria-hidden="true">
    {avatar?.type === 'image' ? <img src={avatar.src} alt="" /> : fallback}
  </span>
}
