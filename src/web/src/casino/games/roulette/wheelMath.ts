export const EUROPEAN_ORDER = [
  0, 32, 15, 19, 4, 21, 2, 25, 17, 34, 6, 27, 13, 36, 11, 30, 8, 23, 10, 5, 24, 16, 33, 1, 20, 14, 31, 9, 22, 18, 29, 7,
  28, 12, 35, 3, 26,
] as const;

export const WHEEL_SLICE = 360 / 37;

export function wheelIndexForNumber(n: number): number {
  return EUROPEAN_ORDER.indexOf(n as (typeof EUROPEAN_ORDER)[number]);
}

export function wheelDegreesForNumber(n: number, extraSpins = 6): number {
  const index = wheelIndexForNumber(n);
  if (index < 0) return extraSpins * 360;
  return extraSpins * 360 + (360 - index * WHEEL_SLICE);
}

export function ballDegreesForNumber(n: number, extraSpins = 6): number {
  return extraSpins * 360 * 1.35 + wheelIndexForNumber(n) * WHEEL_SLICE;
}
