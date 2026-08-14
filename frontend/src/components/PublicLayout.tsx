import { Menu, Recycle, X } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Link, NavLink } from 'react-router-dom'

const navigation = [
  { to: '/', label: 'Home', end: true },
  { to: '/about', label: 'About' },
  { to: '/how-it-works', label: 'How it works' },
  { to: '/impact', label: 'Impact' },
]

export function PublicLayout({
  children,
}: {
  children: ReactNode
}) {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <div className="public-page">
      <header className="site-header">
        <nav className="site-nav">
          <Link
            to="/"
            className="site-brand"
            aria-label="EcoRevive Dubai home"
            onClick={() => setMenuOpen(false)}
          >
            <span className="site-brand-mark">
              <Recycle size={22} strokeWidth={2.4} />
            </span>

            <span className="site-brand-name">
              <strong>EcoRevive</strong>
              <small>Dubai</small>
            </span>
          </Link>

          <div
            className={
              menuOpen
                ? 'site-nav-links site-nav-links-open'
                : 'site-nav-links'
            }
          >
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  isActive ? 'active' : undefined
                }
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}

            <Link
              className="button button-small button-ghost"
              to="/login"
              onClick={() => setMenuOpen(false)}
            >
              Log in
            </Link>

            <Link
              className="button button-small"
              to="/register"
              onClick={() => setMenuOpen(false)}
            >
              Make an impact
            </Link>
          </div>

          <button
            type="button"
            className="site-menu-button"
            aria-label={menuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((current) => !current)}
          >
            {menuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </nav>
      </header>

      <main>{children}</main>

      <footer className="site-footer">
        <div>
          <Link
            to="/"
            className="site-brand site-brand-footer"
          >
            <span className="site-brand-mark">
              <Recycle size={20} strokeWidth={2.4} />
            </span>

            <span className="site-brand-name">
              <strong>EcoRevive</strong>
              <small>Dubai</small>
            </span>
          </Link>

          <p>
            Community-led collection. Responsible recycling.
            Measurable impact.
          </p>
        </div>

        <div className="site-footer-links">
          <Link to="/about">About</Link>
          <Link to="/how-it-works">How it works</Link>
          <Link to="/impact">Impact</Link>
          <Link to="/register">Request a pickup</Link>
        </div>

        <span className="site-footer-copy">
          © {new Date().getFullYear()} EcoRevive Dubai
        </span>
      </footer>
    </div>
  )
}
