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

/** Dark-mode fill/tint colors — lighter and more saturated than uniform-darkening
 * output so nodes from different directories remain visually distinguishable.
 * Each value preserves the semantic identity of its light-mode counterpart. */
export const DIRECTORY_TINTS_DARK: Record<string, string> = {
  'user/facts': '#2D2A28',
  'user/observations': '#363330',
  'user/preferences': '#3D3528',
  'user/decisions': '#3D2828',
  'user/feelings': '#3D3020',
  'user/people': '#322A3D',
  'user/beliefs': '#1A2E21',
  'user/moments': '#3D2E28',
  'user/snapshots': '#2E2D2C',
  'api': '#1E2D3D',
  'schemas': '#2D2A28',
}

/** Default color for directories not in the known palette */
export const DEFAULT_COLOR = '#57534E'
export const DEFAULT_TINT = '#FDFBF5'
/** Default dark-mode tint — darker than the uniform 82%-black blend */
export const DEFAULT_TINT_DARK = '#2D2A28'

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
