import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { Logo } from '../components/Logo'
import { useAuth } from '../context/AuthContext'

function AuthFrame({ title, subtitle, children }: { title: string; subtitle: string; children: React.ReactNode }) {
  return <div className="auth-page"><div className="auth-brand"><Logo /><div><span className="eyebrow">EcoRevive Dubai</span><h1>Community infrastructure for responsible e-waste action.</h1><p>Coordinate every request from first contact through verified recycler handover.</p></div></div><div className="auth-panel"><div className="auth-card"><h2>{title}</h2><p>{subtitle}</p>{children}</div></div></div>
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/dashboard" replace />
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(''); try { await login(email, password); navigate('/dashboard') } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) } }
  return <AuthFrame title="Welcome back" subtitle="Sign in to your EcoRevive workspace."><form onSubmit={submit} className="form-stack"><label>Email<input type="email" required value={email} onChange={e => setEmail(e.target.value)} autoComplete="email"/></label><label>Password<input type="password" required value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password"/></label>{error && <div className="alert alert-error">{error}</div>}<button className="button" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button></form><p className="auth-switch">New to EcoRevive? <Link to="/register">Create an account</Link></p></AuthFrame>
}

export function RegisterPage() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', full_name: '', phone_number: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/dashboard" replace />
  const submit = async (event: FormEvent) => { event.preventDefault(); setBusy(true); setError(''); try { await register(form); navigate('/requests/new') } catch (err) { setError(errorMessage(err)) } finally { setBusy(false) } }
  return <AuthFrame title="Join EcoRevive" subtitle="Create a resident account to request a collection."><form onSubmit={submit} className="form-stack"><label>Full name<input required value={form.full_name} onChange={e => setForm({...form, full_name:e.target.value})}/></label><label>Email<input type="email" required value={form.email} onChange={e => setForm({...form, email:e.target.value})}/></label><label>WhatsApp / phone<input value={form.phone_number} onChange={e => setForm({...form, phone_number:e.target.value})} placeholder="+971…"/></label><label>Password<input type="password" minLength={10} required value={form.password} onChange={e => setForm({...form, password:e.target.value})}/><small>Use at least 10 characters and avoid common passwords.</small></label>{error && <div className="alert alert-error">{error}</div>}<button className="button" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button></form><p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p></AuthFrame>
}
