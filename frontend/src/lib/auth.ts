import apiFetch from "@/lib/api"

export type CurrentUser = {
  role: "admin" | "user"
  name: string | null
}

function storedUser(): CurrentUser {
  const role = localStorage.getItem("role") === "admin" ? "admin" : "user"
  const name = localStorage.getItem("user_name")
  return { role, name }
}

export function getUser(): CurrentUser {
  return storedUser()
}

export function isAdmin(): boolean {
  return storedUser().role === "admin"
}

// Fallback: if the stored role is missing (e.g. logged in before roles existed),
// fetch the current user from the backend and cache it.
let mePromise: Promise<CurrentUser> | null = null

export function resolveUser(): Promise<CurrentUser> {
  const local = storedUser()
  if (localStorage.getItem("role")) {
    return Promise.resolve(local)
  }
  if (!mePromise) {
    mePromise = apiFetch<{ email: string; role: string; name?: string | null }>("/api/v1/auth/me")
      .then((r) => {
        const user: CurrentUser = { role: r.role === "admin" ? "admin" : "user", name: r.name ?? null }
        localStorage.setItem("role", user.role)
        if (user.name) localStorage.setItem("user_name", user.name)
        return user
      })
      .catch(() => local)
      .finally(() => {
        mePromise = null
      })
  }
  return mePromise
}

export function logout() {
  localStorage.removeItem("access_token")
  localStorage.removeItem("role")
  localStorage.removeItem("user_name")
  window.location.href = "/login"
}
