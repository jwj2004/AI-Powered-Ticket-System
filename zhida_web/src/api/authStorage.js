/** 认证信息存 localStorage（不上 Pinia） */

const TOKEN_KEY = 'zhida_token'
const ROLE_KEY = 'zhida_role'
const USERNAME_KEY = 'zhida_username'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function getRole() {
  return localStorage.getItem(ROLE_KEY)
}

export function getUsername() {
  return localStorage.getItem(USERNAME_KEY)
}

export function setAuth({ token, role, username }) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(ROLE_KEY, role)
  localStorage.setItem(USERNAME_KEY, username)
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
  localStorage.removeItem(USERNAME_KEY)
}

export function isLoggedIn() {
  return Boolean(getToken())
}

export function isAdmin() {
  return getRole() === 'admin'
}
