export default function BrandMark({ className = '', variant = 'square' }) {
  const source = variant === 'light' ? '/myx-logo-light.png' : '/myx-logo-square.png'
  return <span className={`brand-mark brand-mark-${variant} ${className}`.trim()} aria-label="懂单儿 Logo">
    <img src={source} alt="" />
  </span>
}
