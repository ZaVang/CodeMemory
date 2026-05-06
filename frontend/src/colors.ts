// Shared directory color palette — single source of truth for GraphCanvas and Legend

/** Border colors for nodes by directory */
export const DIRECTORY_COLORS: Record<string, string> = {
  'user/facts': '#1C1917',
  'user/observations': '#57534E',
  'user/preferences': '#B8860B',
  'user/decisions': '#991B1B',
  'user/feelings': '#CA8A04',
  'user/people': '#7C3AED',
  'user/beliefs': '#166534',
  'user/moments': '#D97757',
  'user/snapshots': '#A8A29E',
  'api': '#1E40AF',
  'schemas': '#1C1917',
}

/** Fill/tint colors for nodes by directory */
export const DIRECTORY_TINTS: Record<string, string> = {
  'user/facts': '#F5F5F4',
  'user/observations': '#F5F5F4',
  'user/preferences': '#FDF6E8',
  'user/decisions': '#FDF2F2',
  'user/feelings': '#FEF9F0',
  'user/people': '#F5F0FE',
  'user/beliefs': '#EDF7F0',
  'user/moments': '#FDF3EE',
  'user/snapshots': '#F5F5F4',
  'api': '#EEF2FA',
  'schemas': '#FDFBF5',
}

/** Default color for directories not in the known palette */
export const DEFAULT_COLOR = '#57534E'
export const DEFAULT_TINT = '#FDFBF5'

/** Fallback colors cycled through for unknown directories */
export const FALLBACK_COLORS = [
  '#1E40AF', '#7C3AED', '#166534', '#991B1B', '#CA8A04',
  '#D97757', '#0F766E', '#BE185D', '#854D0E', '#4F46E5',
]

/**
 * Resolve a color for the given directory.
 * Checks known mappings, then prefix matches, then falls back to the palette.
 */
export function getColorForDirectory(dir: string, extraIndex: number): string {
  if (DIRECTORY_COLORS[dir]) return DIRECTORY_COLORS[dir]
  for (const [key, color] of Object.entries(DIRECTORY_COLORS)) {
    if (dir.startsWith(key + '/') || key.startsWith(dir + '/')) return color
  }
  return FALLBACK_COLORS[extraIndex % FALLBACK_COLORS.length]
}

/**
 * Resolve a tint for the given directory.
 */
export function getTintForDirectory(dir: string): string {
  if (DIRECTORY_TINTS[dir]) return DIRECTORY_TINTS[dir]
  for (const [key, tint] of Object.entries(DIRECTORY_TINTS)) {
    if (dir.startsWith(key + '/') || key.startsWith(dir + '/')) return tint
  }
  return DEFAULT_TINT
}
