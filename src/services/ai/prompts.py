"""AI prompt 模板 — 文档 Q&A(A1)+ 记账提取(B2 截图 / B3 文本)。

设计文档:
- A1 文档 Q&A:`.docs/web-cmdk-ai-doc-search.md`
- B2 截图记账:`.docs/web-cmdk-ai-paste-screenshot.md`
- B3 文字记账:`.docs/web-cmdk-ai-paste-text.md`

通用规则:
- 文档没说的不要编;明确说"文档没找到",不要发挥(A1)
- 必须用 user locale 对应语言回答 / 输出(避免中英 mixing)
- LLM 输出 JSON 时强制 array(`tx_drafts: [...]`),前端不分单/多笔
"""
from __future__ import annotations

from datetime import datetime

from .docs_index import RetrievedChunk


_SYSTEM_PL = """\
Jesteś asystentem księgowości domowej. Odpowiadaj WYŁĄCZNIE na podstawie
poniższych «Dokumentów».

Zasady:
1. Odpowiadaj po polsku.
2. Jeśli w dokumentach czegoś nie ma — napisz, że nie ma tego w dokumentacji. Nie zmyślaj.
3. Krótko: kroki numerowane albo 1–2 zdania.
4. Nie dopisuj listy źródeł (system doda je sam).
5. Pytania niezwiązane z księgowością / tą aplikacją — odmów krótko.
"""


_SYSTEM_EN = """\
You are the assistant for BeeCount, a personal finance app. Answer ONLY based on the
"Relevant Docs" provided below.

Rules:
1. **You MUST answer in English**. Translate any non-English docs into English.
2. If the docs don't clearly say something, answer "Sorry, the docs don't cover this"
   instead of making things up.
3. Be concise. Step-by-step for how-to questions; one or two sentences for concept questions.
4. Don't list source references at the end (the system appends them automatically).
5. Don't mix unrelated languages into English output unless quoting a UI label.
6. If the user asks something unrelated to BeeCount / personal finance, reply "That's outside
   what I can answer".
"""


def build_ask_messages(
    *,
    query: str,
    chunks: list[RetrievedChunk],
    lang: str = "pl",
) -> list[dict[str, str]]:
    """拼出 OpenAI-compatible /chat/completions 的 messages 数组。"""
    lang_key = (lang or "pl").lower()
    if lang_key.startswith("en"):
        system = _SYSTEM_EN
    else:
        system = _SYSTEM_PL
    parts: list[str] = []
    for i, c in enumerate(chunks, 1):
        # 给每段加上 doc 路径作为 anchor,LLM 看上下文更好
        header = f"### [{i}] {c.chunk.doc_title}"
        if c.chunk.section:
            header += f" — {c.chunk.section}"
        parts.append(f"{header}\n{c.chunk.content.strip()}")
    docs_block = "\n\n".join(parts) if parts else (
        "(no relevant docs found)"
        if lang_key.startswith("en")
        else "(brak fragmentów dokumentacji)"
    )

    if lang_key.startswith("en"):
        user_content = (
            f"## Relevant Docs\n\n{docs_block}\n\n## User Question\n\n{query}"
        )
    else:
        user_content = (
            f"## Dokumenty\n\n{docs_block}\n\n## Pytanie\n\n{query}"
        )

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]


# ────────────────────────────────────────────────────────────────────────
# B2 / B3 记账提取 — 截图 / 文字 → 1-N 笔 tx draft
# ────────────────────────────────────────────────────────────────────────

# Shared JSON schema for B2/B3

_TX_DRAFTS_SCHEMA_PL = """\
**FORMAT WYJŚCIA**: zwróć obiekt JSON (nie tablicę) z jednym kluczem `tx_drafts`
(wartość = tablica).

Poprawnie: `{"tx_drafts": [{...}, {...}]}`
Źle: `[{...}]`, `{"transactions": [...]}`, pojedynczy obiekt `{...}`.
Zawsze tablica, nawet dla 1 transakcji. 0 pozycji: `{"tx_drafts": []}`.

Pola każdej transakcji:
  - `type`: "expense" | "income" | "transfer"
  - `amount`: liczba, wartość bezwzględna (bez znaku)
  - `happened_at`: ISO 8601; zgadnij z źródła; brak daty → "{{NOW}}"
  - `category_name`: z listy dostępnych kategorii; inaczej ""
  - `account_name`: z listy kont; inaczej "" (expense/income)
  - `from_account_name` / `to_account_name`: tylko transfer
  - `note`: ≤15 znaków (sklep / opis)
  - `currency`: 3-literowy kod ISO 4217 wielkimi literami — nigdy symbol ani nazwa
    - Mapowanie: dolar/$ → USD, jen → JPY, euro/€ → EUR, funt/£ → GBP,
      dolar HK → HKD, dolar TW → TWD, won → KRW, baht → THB, złoty/zł → PLN
    - Zostaw "" gdy to waluta księgi
    - Wypełnij, gdy źródło podaje inną walutę (nazwa, symbol lub kod)
    - np. "wydałem 45 dolarów" → "USD"; "Starbucks $6.5" → "USD"
  - `tags`: tablica, może być pusta
  - `confidence`: "high" | "medium" | "low"
"""

_TX_DRAFTS_SCHEMA_EN = """\
**STRICT OUTPUT FORMAT**: Return a JSON object — **the top level MUST be a dict, NOT an array** —
with exactly one key `tx_drafts` whose value is an array.

Correct: `{"tx_drafts": [{...}, {...}]}`
**WRONG** (don't do): `[{...}]`, `{"transactions": [...]}`, `{"items": [...]}`,
or a single object `{...}`. Always use array even for a single tx. For 0 tx return `{"tx_drafts": []}`.

Each draft has fields:
  - `type`: "expense" | "income" | "transfer"
  - `amount`: number, absolute value (no signs)
  - `happened_at`: ISO 8601 datetime; infer from source; fallback to "{{NOW}}"
  - `category_name`: pick from available categories; "" if no match
  - `account_name`: pick from available accounts; "" if no match (for expense/income)
  - `from_account_name` / `to_account_name`: only for transfer
  - `note`: ≤15 chars merchant/item/short description
  - `currency`: MUST be a 3-letter uppercase ISO 4217 code — **never a currency
    symbol, never a currency name**
    - Mapping: dollar/dollars/$ → USD, yen/円 → JPY, euro/€ → EUR, pound/£ → GBP,
      HK dollar → HKD, NT dollar → TWD, won → KRW, baht → THB
    - Leave "" when it equals the ledger's base currency
    - Fill it whenever the source states a foreign currency in ANY form (name,
      symbol or code) — don't skip it
    - e.g. "spent 45 dollars" → "USD"; "Starbucks $6.5" → "USD"; "1200 yen" → "JPY"
  - `tags`: array, can be empty
  - `confidence`: "high" | "medium" | "low"
"""

# B2 截图 prompt

_PARSE_TX_IMAGE_EN = """\
You are BeeCount's bookkeeping assistant. I'll give you a payment receipt screenshot
(could be Alipay/WeChat/credit-card notification/bank statement). Extract every
transaction visible.

Current time: {NOW}
Available categories in this ledger: {CATEGORIES}
Available accounts in this ledger: {ACCOUNTS}
{CURRENCY_HINT}

{SCHEMA}

Rules:
1. If the image is clearly NOT a payment receipt (e.g. chat screenshot), return
   `{{"tx_drafts": []}}`.
2. Multi-tx: credit card statements / bill lists / monthly summary — extract every
   clear entry.
3. **Don't fabricate**: leave fields as "" or null when unclear; if amount is unclear
   skip that whole tx (don't include it).

Output JSON only, no prefix/suffix text.
"""

# B3 文本 prompt

_PARSE_TX_TEXT_EN = """\
You are BeeCount's bookkeeping assistant. I'll give you a piece of text (could be a
WeChat/Alipay/credit-card statement excerpt, or a user's hand-written list of pending
transactions). Extract every transaction.

Current time: {NOW}
Available categories in this ledger: {CATEGORIES}
Available accounts in this ledger: {ACCOUNTS}
{CURRENCY_HINT}

Text:
{TEXT}

{SCHEMA}

Rules:
1. Field inference:
   - No explicit date → infer ("dinner yesterday" → yesterday's date + reasonable hour)
   - No date info at all → use "{NOW}"
   - No explicit category → infer (Starbucks → Coffee/Food); leave "" if unclear
2. Multi-tx: each line / list item is one tx
3. Plain chitchat / not a bill → return `{{"tx_drafts": []}}`
4. **Don't fabricate amounts**: skip the whole tx if amount unclear

Output JSON only, no prefix/suffix text.
"""

_PARSE_TX_IMAGE_PL = """\
Jesteś asystentem księgowości. Z zrzutu paragonu / powiadomienia banku wyciągnij każdą transakcję.

Czas teraz: {NOW}
Dostępne kategorie: {CATEGORIES}
Dostępne konta: {ACCOUNTS}
{CURRENCY_HINT}

{SCHEMA}

Zasady:
1. Jeśli to nie jest paragon / wyciąg — zwróć `{{"tx_drafts": []}}`.
2. Przy liście wielu pozycji wyciągnij każdą czytelną.
3. Nie zmyślaj kwot ani dat. Niepewne pole: "" lub null; bez kwoty — pomiń pozycję.

Tylko JSON, bez komentarza.
"""

_PARSE_TX_TEXT_PL = """\
Jesteś asystentem księgowości. Z tekstu (SMS, wyciąg, lista) wyciągnij transakcje.

Czas teraz: {NOW}
Dostępne kategorie: {CATEGORIES}
Dostępne konta: {ACCOUNTS}
{CURRENCY_HINT}

Tekst:
{TEXT}

{SCHEMA}

Zasady:
1. Brak daty → wywnioskuj albo użyj "{NOW}".
2. Brak kategorii → zgadnij z opisu albo "".
3. Pogawędka bez kwot → `{{"tx_drafts": []}}`.
4. Nie zmyślaj kwot.

Tylko JSON, bez komentarza.
"""


def _locale_kind(locale: str | None) -> str:
    key = (locale or "pl").lower()
    if key.startswith("en"):
        return "en"
    return "pl"


def _format_categories_hint(categories: list[str]) -> str:
    """把类目列表格式化成 LLM 友好的字符串。空列表返回 "(无,请用户在前端选)"。"""
    if not categories:
        return "(none — leave category_name empty for user to pick)"
    return ", ".join(c for c in categories if c)


def _format_accounts_hint(
    accounts: list[tuple[str, str | None]], ledger_currency: str,
) -> str:
    """账户清单。**只有币种 ≠ 账本主币种的账户才标注币种** —— 单币种用户看到的
    字符串与加多币种支持之前逐字相同(零噪声、零回归)。"""
    if not accounts:
        return "(none — leave account_name empty for user to pick)"
    base = (ledger_currency or "").strip().upper()
    parts: list[str] = []
    for name, ccy in accounts:
        if not name:
            continue
        code = (ccy or "").strip().upper()
        parts.append(f"{name}({code})" if code and code != base else name)
    return ", ".join(parts)


def _format_currency_hint(
    accounts: list[tuple[str, str | None]], ledger_currency: str, *, lang: str = "pl",
) -> str:
    """One-line currency context for the LLM (base + any foreign account codes)."""
    kind = _locale_kind(lang)
    base = (ledger_currency or "PLN").strip().upper()
    others = sorted(
        {(c or "").strip().upper() for _, c in accounts if (c or "").strip()} - {base, ""}
    )
    if kind == "en":
        line = f"Ledger base currency: {base}"
        if others:
            line += f"; foreign-currency accounts present: {', '.join(others)}"
        return line
    line = f"Waluta księgi: {base}"
    if others:
        line += f"; konta w innej walucie: {', '.join(others)}"
    return line


def build_parse_tx_image_messages(
    *,
    categories: list[str],
    accounts: list[tuple[str, str | None]],
    ledger_currency: str = "PLN",
    now: datetime,
    locale: str = "pl",
    image_data_url: str,
    custom_prompt_template: str | None = None,
) -> list[dict[str, object]]:
    """B2 截图记账 — 拼 OpenAI vision API messages。

    image_data_url: `data:image/jpeg;base64,...` 格式
    accounts: (名称, 币种) 列表;币种 ≠ 账本主币种时会在 prompt 里标注
    custom_prompt_template: 用户自定义 prompt(从 user.ai_config_json 来),为 None 则用 default
        —— 自定义模板不含 `{CURRENCY_HINT}` 时 `.format()` 直接忽略该 kwarg,老模板零影响
    """
    kind = _locale_kind(locale)
    if custom_prompt_template:
        template = custom_prompt_template
    elif kind == "en":
        template = _PARSE_TX_IMAGE_EN
    else:
        template = _PARSE_TX_IMAGE_PL
    schema = _TX_DRAFTS_SCHEMA_EN if kind == "en" else _TX_DRAFTS_SCHEMA_PL
    prompt = template.format(
        NOW=now.isoformat(timespec="seconds"),
        CATEGORIES=_format_categories_hint(categories),
        ACCOUNTS=_format_accounts_hint(accounts, ledger_currency),
        CURRENCY_HINT=_format_currency_hint(accounts, ledger_currency, lang=locale),
        SCHEMA=schema,
    )
    return [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_data_url}},
                {"type": "text", "text": prompt},
            ],
        }
    ]


def build_parse_tx_text_messages(
    *,
    text: str,
    categories: list[str],
    accounts: list[tuple[str, str | None]],
    ledger_currency: str = "PLN",
    now: datetime,
    locale: str = "pl",
    custom_prompt_template: str | None = None,
) -> list[dict[str, object]]:
    """B3 文字记账 — 拼 OpenAI chat API messages。参数语义同 [build_parse_tx_image_messages]。"""
    kind = _locale_kind(locale)
    if custom_prompt_template:
        template = custom_prompt_template
    elif kind == "en":
        template = _PARSE_TX_TEXT_EN
    else:
        template = _PARSE_TX_TEXT_PL
    schema = _TX_DRAFTS_SCHEMA_EN if kind == "en" else _TX_DRAFTS_SCHEMA_PL
    prompt = template.format(
        NOW=now.isoformat(timespec="seconds"),
        CATEGORIES=_format_categories_hint(categories),
        ACCOUNTS=_format_accounts_hint(accounts, ledger_currency),
        CURRENCY_HINT=_format_currency_hint(accounts, ledger_currency, lang=locale),
        TEXT=text,
        SCHEMA=schema,
    )
    return [{"role": "user", "content": prompt}]
