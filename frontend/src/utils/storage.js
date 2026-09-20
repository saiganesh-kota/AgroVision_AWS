const AUTH_KEY   = 'agrovision_auth'
const USERS_KEY  = 'agrovision_users'
const LAST_KEY   = 'agrovision_last_result'

// ── Auth helpers ─────────────────────────────────────────────────────────────
export const isLoggedIn = () => {
  try {
    const u = JSON.parse(localStorage.getItem(AUTH_KEY))
    return !!(u && u.id)
  } catch {
    return false
  }
}

export const logout = () => {
  localStorage.removeItem(AUTH_KEY)
  localStorage.removeItem(LAST_KEY)  // clear last scan so next user starts fresh
}

export const getCurrentUser = () => {
  try { return JSON.parse(localStorage.getItem(AUTH_KEY) || 'null') } catch { return null }
}

// ── User registry ─────────────────────────────────────────────────────────────
const getUsers = () => {
  try { return JSON.parse(localStorage.getItem(USERS_KEY) || '[]') } catch { return [] }
}
const saveUsers = (users) => localStorage.setItem(USERS_KEY, JSON.stringify(users))

export const registerUser = ({ name, email, password, state, phone }) => {
  const users = getUsers()
  if (users.find(u => u.email.toLowerCase() === email.toLowerCase())) {
    return { ok: false, error: 'An account with this email already exists.' }
  }
  const user = {
    id: crypto.randomUUID(), name, email: email.toLowerCase(),
    password, state: state || '', phone: phone || '',
    createdAt: new Date().toISOString()
  }
  users.push(user)
  saveUsers(users)
  const session = { id: user.id, name: user.name, email: user.email, state: user.state }
  localStorage.setItem(AUTH_KEY, JSON.stringify(session))
  return { ok: true, user: session }
}

export const loginUser = (email, password) => {
  const users = getUsers()
  const user  = users.find(u => u.email.toLowerCase() === email.toLowerCase() && u.password === password)
  if (!user) return { ok: false, error: 'Invalid email or password.' }
  const session = { id: user.id, name: user.name, email: user.email, state: user.state }
  localStorage.setItem(AUTH_KEY, JSON.stringify(session))
  return { ok: true, user: session }
}

// ── Last result ───────────────────────────────────────────────────────────────
export const saveLastResult = (r) => { try { localStorage.setItem(LAST_KEY, JSON.stringify(r)) } catch {} }
export const getLastResult  = ()  => { try { return JSON.parse(localStorage.getItem(LAST_KEY) || 'null') } catch { return null } }

// Legacy compat
export const saveAuth = () => {}
