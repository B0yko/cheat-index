const ENTITIES: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

/** Escape the characters that matter in HTML text and attribute values. */
export function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => ENTITIES[char]);
}
