import {
  useState,
  type FormEvent,
  type ReactNode,
} from 'react'
import {
  Link,
  Navigate,
  useNavigate,
} from 'react-router-dom'

import { errorMessage } from '../api/client'
import { Logo } from '../components/Logo'
import { useAuth } from '../context/AuthContext'

type AccountType =
  | 'resident'
  | 'volunteer'

interface RegistrationForm {
  email: string
  full_name: string
  phone_number: string
  password: string
  account_type: AccountType
}

interface AuthFrameProps {
  title: string
  subtitle: string
  children: ReactNode
}

function AuthFrame({
  title,
  subtitle,
  children,
}: AuthFrameProps) {
  return (
    <div className="auth-page">
      <div className="auth-brand">
        <Logo />

        <div>
          <span className="eyebrow">
            EcoRevive Dubai
          </span>

          <h1>
            Community infrastructure for
            responsible e-waste action.
          </h1>

          <p>
            Coordinate every request from
            first contact through verified
            recycler handover.
          </p>
        </div>
      </div>

      <div className="auth-panel">
        <div className="auth-card">
          <h2>{title}</h2>
          <p>{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  )
}

export function LoginPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()

  const [
    identifier,
    setIdentifier,
  ] = useState('')

  const [password, setPassword] =
    useState('')
  const [error, setError] =
    useState('')
  const [busy, setBusy] =
    useState(false)

  if (user) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    )
  }

  const submit = async (
    event: FormEvent,
  ) => {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      await login(
        identifier,
        password,
      )
      navigate('/dashboard')
    } catch (err) {
      setError(
        errorMessage(err),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthFrame
      title="Welcome back"
      subtitle={
        'Sign in to your EcoRevive workspace.'
      }
    >
      <form
        onSubmit={submit}
        className="form-stack"
      >
        <label>
          Email or phone
          <input
            type="text"
            required
            value={identifier}
            onChange={(event) =>
              setIdentifier(
                event.target.value,
              )
            }
            autoComplete="username"
            placeholder={
              'Email address or phone number'
            }
          />
        </label>

        <label>
          Password
          <input
            type="password"
            required
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value,
              )
            }
            autoComplete={
              'current-password'
            }
          />
        </label>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="button"
          disabled={busy}
        >
          {busy
            ? 'Signing in…'
            : 'Sign in'}
        </button>
      </form>

      <p className="auth-switch">
        New to EcoRevive?{' '}
        <Link to="/register">
          Create an account
        </Link>
      </p>
    </AuthFrame>
  )
}

export function RegisterPage() {
  const { user, register } =
    useAuth()
  const navigate = useNavigate()

  const [form, setForm] =
    useState<RegistrationForm>({
      email: '',
      full_name: '',
      phone_number: '',
      password: '',
      account_type: 'resident',
    })

  const [error, setError] =
    useState('')
  const [busy, setBusy] =
    useState(false)

  if (user) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    )
  }

  const residentWithoutEmail =
    form.account_type === 'resident'
    && !form.email.trim()

  const submit = async (
    event: FormEvent,
  ) => {
    event.preventDefault()
    setBusy(true)
    setError('')

    try {
      await register(form)

      navigate(
        form.account_type
          === 'volunteer'
          ? '/dashboard'
          : '/requests/new',
      )
    } catch (err) {
      setError(
        errorMessage(err),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthFrame
      title="Join EcoRevive"
      subtitle={
        'Create an account as a resident or volunteer.'
      }
    >
      <form
        onSubmit={submit}
        className="form-stack"
      >
        <label>
          I want to join as
          <select
            required
            value={
              form.account_type
            }
            onChange={(event) =>
              setForm({
                ...form,
                account_type:
                  event.target
                    .value as AccountType,
              })
            }
          >
            <option value="resident">
              Resident requesting an
              e-waste collection
            </option>

            <option value="volunteer">
              Volunteer helping with
              collections
            </option>
          </select>
        </label>

        {form.account_type
          === 'volunteer' && (
          <div className="alert">
            Your volunteer registration
            will require administrator
            approval before you can
            receive pickup assignments.
          </div>
        )}

        <label>
          Full name
          <input
            required
            value={form.full_name}
            onChange={(event) =>
              setForm({
                ...form,
                full_name:
                  event.target.value,
              })
            }
            autoComplete="name"
          />
        </label>

        <label>
          {form.account_type
            === 'resident'
            ? 'Email (optional)'
            : 'Email'}

          <input
            type="email"
            required={
              form.account_type
              === 'volunteer'
            }
            value={form.email}
            onChange={(event) =>
              setForm({
                ...form,
                email:
                  event.target.value,
              })
            }
            autoComplete="email"
          />

          {form.account_type
            === 'resident' && (
            <small>
              Optional. If you leave
              this blank, use your
              phone number to sign in.
              Email notifications will
              be disabled for your
              account.
            </small>
          )}
        </label>

        <label>
          {residentWithoutEmail
            ? 'WhatsApp / phone (required)'
            : 'WhatsApp / phone'}

          <input
            type="tel"
            required={
              residentWithoutEmail
            }
            value={
              form.phone_number
            }
            onChange={(event) =>
              setForm({
                ...form,
                phone_number:
                  event.target.value,
              })
            }
            placeholder="+971…"
            autoComplete="tel"
          />

          {residentWithoutEmail && (
            <small>
              Required because this
              number will be used to
              sign in when no email is
              provided.
            </small>
          )}
        </label>

        <label>
          Password
          <input
            type="password"
            minLength={10}
            required
            value={form.password}
            onChange={(event) =>
              setForm({
                ...form,
                password:
                  event.target.value,
              })
            }
            autoComplete={
              'new-password'
            }
          />

          <small>
            Use at least 10 characters
            and avoid common passwords.
          </small>
        </label>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="button"
          disabled={busy}
        >
          {busy
            ? 'Creating account…'
            : form.account_type
                === 'volunteer'
              ? 'Register as volunteer'
              : 'Create resident account'}
        </button>
      </form>

      <p className="auth-switch">
        Already registered?{' '}
        <Link to="/login">
          Sign in
        </Link>
      </p>
    </AuthFrame>
  )
}