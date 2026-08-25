export function chipFlightDuration(distancePx: number): number {
  return Math.min(700, Math.max(280, distancePx * 2));
}
