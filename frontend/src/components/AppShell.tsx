import {
  BarChart3,
  CalendarCheck,
  ClipboardCheck,
  ClipboardList,
  FilePlus2,
  Home,
  LogOut,
  Menu,
  Settings,
  ShieldCheck,
  UserCog,
  Users,
  X,
} from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { Logo } from './Logo'

const adminRoles = new Set([
  'founder_guardian',
  'principal_admin',
  'operations_admin',
])

const governanceRoles = new Set([
  'founder_guardian',
  'founder_recovery',
  'principal_admin',
])

export function AppShell() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)

  const isAdmin = !!user && adminRoles.has(user.role)
  const isGovernance = !!user && governanceRoles.has(user.role)
  const isVolunteer = user?.role === 'volunteer'

  const links = [
    {
      to: '/dashboard',
      label: 'Dashboard',
      icon: Home,
    },
    {
      to: '/requests',
      label: isAdmin ? 'All requests' : 'My requests',
      icon: ClipboardList,
    },
    ...(isVolunteer
      ? [
          {
            to: '/assignments',
            label: 'My assignments',
            icon: ClipboardCheck,
          },
        ]
      : []),
    {
      to: '/requests/new',
      label: 'New collection',
      icon: FilePlus2,
    },
    ...(isAdmin
      ? [
          {
            to: '/operations',
            label: 'Operations',
            icon: Users,
          },
          {
            to: '/fulfillment',
            label: 'Fulfillment',
            icon: CalendarCheck,
          },
          {
            to: '/administration',
            label: 'Administration',
            icon: UserCog,
          },
          {
            to: '/impact-admin',
            label: 'Impact data',
            icon: BarChart3,
          },
        ]
      : []),
    ...(isGovernance
      ? [
          {
            to: '/governance',
            label: 'Governance',
            icon: ShieldCheck,
          },
        ]
      : []),
    {
      to: '/account',
      label: 'Account',
      icon: Settings,
    },
  ]

  return (
    <div className="app-layout">
      <aside className={`sidebar ${open ? 'sidebar-open' : ''}`}>
        <div className="sidebar-head">
          <Logo />

          <button
            className="icon-button mobile-only"
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            <X />
          </button>
        </div>

        <nav>
          {links.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setOpen(false)}
            >
              <Icon size={19} />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-user">
          <div className="avatar">
            {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
          </div>

          <div>
            <strong>{user?.full_name}</strong>
            <small>{user?.role.replaceAll('_', ' ')}</small>
          </div>

          <button
            className="icon-button"
            type="button"
            onClick={logout}
            aria-label="Log out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>

      <main className="app-main">
        <header className="mobile-header">
          <button
            className="icon-button"
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
          >
            <Menu />
          </button>

          <Logo compact />
          <span />
        </header>

        <Outlet />
      </main>
    </div>
  )
}