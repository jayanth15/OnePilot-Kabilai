const IST_TIME_ZONE = "Asia/Kolkata"

function toDate(value: string | number | Date): Date | null {
  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return null
  return d
}

export function formatDateIST(value: string | number | Date): string {
  const d = toDate(value)
  if (!d) return "—"
  return d.toLocaleDateString("en-IN", { timeZone: IST_TIME_ZONE })
}

export function formatDateTimeIST(value: string | number | Date): string {
  const d = toDate(value)
  if (!d) return "—"
  return d.toLocaleString("en-IN", { timeZone: IST_TIME_ZONE })
}

export function formatTimeIST(
  value: string | number | Date,
  options: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit" }
): string {
  const d = toDate(value)
  if (!d) return ""
  return d.toLocaleTimeString("en-IN", { ...options, timeZone: IST_TIME_ZONE })
}
