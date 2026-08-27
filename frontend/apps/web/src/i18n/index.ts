import type { LocaleDictionaries } from '@beecount/ui'

import en from './en'
import pl from './pl'

export const dictionaries: LocaleDictionaries = {
  en,
  pl
}

export type TranslationKey = keyof typeof en
