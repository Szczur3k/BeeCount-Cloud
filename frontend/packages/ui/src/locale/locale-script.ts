export const LOCALE_STORAGE_KEY = 'beecount.locale'

export const SUPPORTED_LOCALES = ['pl', 'en'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

export function normalizeLocale(raw: string | null | undefined): Locale {
  if (!raw) return 'pl'
  const input = raw.toLowerCase()
  if (input === 'en' || input.startsWith('en-') || input.startsWith('en_')) return 'en'
  if (input === 'pl' || input.startsWith('pl-') || input.startsWith('pl_')) return 'pl'
  // Former zh / unknown → Polish (this fork does not ship a Chinese UI).
  return 'pl'
}

export function detectBrowserLocale(): Locale {
  if (typeof navigator === 'undefined') return 'pl'
  const candidates: Array<string | null | undefined> = [
    navigator.language,
    ...(Array.isArray(navigator.languages) ? navigator.languages : [])
  ]
  for (const candidate of candidates) {
    if (!candidate) continue
    const n = candidate.toLowerCase()
    if (n === 'en' || n.startsWith('en-') || n.startsWith('en_')) return 'en'
    if (n === 'pl' || n.startsWith('pl-') || n.startsWith('pl_')) return 'pl'
  }
  return 'pl'
}

export function initialLocale(): Locale {
  if (typeof window === 'undefined') return 'pl'
  const raw = window.localStorage.getItem(LOCALE_STORAGE_KEY)
  return raw ? normalizeLocale(raw) : detectBrowserLocale()
}

export function persistLocale(locale: Locale): void {
  if (typeof window === 'undefined') return
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale)
}

export function applyDocumentLocale(locale: Locale): void {
  if (typeof document === 'undefined') return
  document.documentElement.setAttribute('lang', locale === 'en' ? 'en' : 'pl')
}
