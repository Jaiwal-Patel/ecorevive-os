import { Recycle } from 'lucide-react'

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <span className="logo" aria-label="EcoRevive OS">
      <span className="logo-mark"><Recycle size={22} strokeWidth={2.4} /></span>
      {!compact && <span><strong>EcoRevive</strong><small>OS</small></span>}
    </span>
  )
}
