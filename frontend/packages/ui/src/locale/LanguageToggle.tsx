import { Languages } from 'lucide-react'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../ui/select'
import { useLocale } from './LocaleProvider'
import { SUPPORTED_LOCALES, type Locale } from './locale-script'

type LanguageToggleProps = {
  /** Compact trigger for the app header. */
  compact?: boolean
}

export function LanguageToggle({ compact = false }: LanguageToggleProps) {
  const { locale, setLocale, t } = useLocale()

  return (
    <Select
      value={locale}
      onValueChange={(next) => setLocale(next as Locale)}
    >
      <SelectTrigger
        aria-label={t('shell.language')}
        className={
          compact
            ? 'h-8 w-[9.5rem] border-border/50 bg-transparent px-2 text-xs shadow-none'
            : 'h-9 w-full min-w-[12rem] bg-transparent'
        }
        title={t('shell.language')}
      >
        <span className="flex min-w-0 items-center gap-1.5">
          <Languages className="h-3.5 w-3.5 shrink-0 opacity-70" />
          <SelectValue />
        </span>
      </SelectTrigger>
      <SelectContent>
        {SUPPORTED_LOCALES.map((code) => (
          <SelectItem key={code} value={code}>
            {t(`locale.name.${code}`)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
