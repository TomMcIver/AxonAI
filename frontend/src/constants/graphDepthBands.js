/**
 * Prerequisite depth bands: same order and colours as the knowledge graph legend
 * (left → right: Fundamentals … Further).
 */
export const DEPTH_LABELS = ['Fundamentals', 'Early', 'Core', 'Stretch', 'Advanced', 'Further'];

export const DEPTH_BAND_FILLS = [
  '#a8d4ff',
  '#7ee0b8',
  '#ffe566',
  '#ffb8d9',
  '#cdb8ff',
  '#ffc9a3',
];

export const DEPTH_COUNT = DEPTH_LABELS.length;

export function clampDepthIndex(d) {
  if (d == null || Number.isNaN(d)) return 0;
  return Math.max(0, Math.min(DEPTH_LABELS.length - 1, Math.floor(d)));
}

export function depthLabel(depthIndex) {
  return DEPTH_LABELS[clampDepthIndex(depthIndex)] ?? '-';
}

export function depthBandFill(depthIndex) {
  return DEPTH_BAND_FILLS[clampDepthIndex(depthIndex)] ?? '#e2e8f0';
}
