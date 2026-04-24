/**
 * Prerequisite depth bands: same order and colours as the knowledge graph legend
 * (left → right: Fundamentals … Further).
 */
export const DEPTH_LABELS = ['Fundamentals', 'Early', 'Core', 'Stretch', 'Advanced', 'Further'];

export const DEPTH_BAND_FILLS = [
  '#d8e9ff',
  '#d9f2e6',
  '#fff2c8',
  '#f9ddeb',
  '#e6ddfb',
  '#fde3cf',
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
