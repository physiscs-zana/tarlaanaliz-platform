/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* SEC: Input sanitization utilities to prevent XSS attacks. */

/**
 * Sanitize user input by stripping HTML tags and dangerous characters.
 * Use for any user-provided text before displaying or sending to API.
 */
export function sanitizeText(input: string): string {
  return input
    .replace(/[<>]/g, "") // Strip angle brackets (prevents HTML injection)
    .replace(/javascript:/gi, "") // Strip javascript: protocol
    .replace(/on\w+\s*=/gi, "") // Strip inline event handlers (onerror=, onclick=, etc.)
    .trim();
}

/**
 * Sanitize a string for safe use in HTML context.
 * Escapes HTML entities to prevent script injection.
 */
export function escapeHtml(input: string): string {
  const map: Record<string, string> = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#x27;",
  };
  return input.replace(/[&<>"']/g, (char) => map[char] ?? char);
}

/**
 * Validate and sanitize a phone number input.
 * Only allows digits, plus sign, and spaces.
 */
export function sanitizePhone(input: string): string {
  return input.replace(/[^\d+\s-]/g, "").trim();
}

/**
 * Sanitize a PIN input — only digits, max 6 chars.
 */
export function sanitizePin(input: string): string {
  return input.replace(/\D/g, "").slice(0, 6);
}
