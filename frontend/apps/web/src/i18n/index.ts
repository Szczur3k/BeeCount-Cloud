import type { LocaleDictionaries } from '@beecount/ui'

import en from './en'
import pl from './pl'
import zhCN from './zh-CN'
import zhTW from './zh-TW'

export const dictionaries: LocaleDictionaries = {
  en,
  pl,
  'zh-CN': zhCN,
  'zh-TW': zhTW
}

export type TranslationKey = keyof typeof en
