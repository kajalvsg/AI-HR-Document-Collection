const EMAIL_RE = /[a-z0-9][a-z0-9._%+-]*@[a-z0-9.-]+\.[a-z]{2,}/gi

// Looser matcher for "email-like" tokens that may include prefixes/symbols.
const EMAILISH_TOKEN_RE =
  /(?:mailto:)?[^\s<>()\[\]]{0,40}[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}/gi

function normalizeSingleEmailLikeToken(token: string, canonicalEmail?: string) {
  let t = token.trim()

  // Remove mailto: prefix.
  t = t.replace(/^mailto:\s*/i, '')

  // Remove leading separators often produced by PDF extraction.
  t = t.replace(/^[\/\\|:;.,-]+/g, '')

  // Remove envel-* prefix if glued before the local-part.
  t = t.replace(/^(?:envel[-_/]+)+/i, '')

  // Remove extra leading slashes directly before local-part.
  t = t.replace(/^\/{1,}(?=[a-z0-9._%+-]+@)/i, '')

  // If token still has junk before email, keep only the last email-like substring.
  const matches = t.match(EMAIL_RE)
  if (!matches || matches.length === 0) return t
  let email = matches[matches.length - 1].toLowerCase()

  // If we know the canonical extracted email, prefer it when token is a noisy variant.
  if (canonicalEmail) {
    const canon = canonicalEmail.toLowerCase()
    if (email === canon) return canon

    // Common PDF noise: local-part gets prefixed with "pe" (e.g., pekajal...).
    const [canonLocal, canonDomain] = canon.split('@')
    const [emailLocal, emailDomain] = email.split('@')
    if (emailDomain === canonDomain && emailLocal === `pe${canonLocal}`) {
      return canon
    }

    // If token ends with canonical email (extra prefix glued), normalize to canonical.
    if (email.endsWith(canon)) return canon
  }

  return email
}

function stripEmailNoise(text: string, canonicalEmail?: string) {
  // Remove common prefixes that sometimes get glued to emails in PDF extraction.
  // We only clean the *rendered preview*; backend extraction stays unchanged.
  let out = text

  // Normalize obvious mail link prefixes.
  out = out.replace(/mailto:\s*/gi, '')

  // Normalize noisy email-like tokens to clean emails.
  out = out.replace(EMAILISH_TOKEN_RE, (token) =>
    normalizeSingleEmailLikeToken(token, canonicalEmail),
  )

  return out
}

function normalizeWhitespace(text: string) {
  // Remove Unicode replacement chars and zero-width spaces that break readability.
  let out = text
    .replace(/\uFFFD/g, '') // �
    .replace(/[\u200B-\u200D\uFEFF]/g, '') // zero-width

  // Normalize line endings.
  out = out.replace(/\r\n/g, '\n').replace(/\r/g, '\n')

  // Collapse excessive horizontal whitespace but keep new lines.
  out = out.replace(/[ \t]+/g, ' ')

  // Trim each line and drop ultra-noisy empty lines.
  out = out
    .split('\n')
    .map((line) => line.trim())
    .join('\n')

  // Collapse multiple blank lines to at most 2.
  out = out.replace(/\n{3,}/g, '\n\n')

  return out.trim()
}

export function cleanResumePreviewText(
  text: string | null | undefined,
  canonicalEmail?: string | null,
) {
  if (!text) return ''
  const noEmailNoise = stripEmailNoise(text, canonicalEmail ?? undefined)
  return normalizeWhitespace(noEmailNoise)
}

