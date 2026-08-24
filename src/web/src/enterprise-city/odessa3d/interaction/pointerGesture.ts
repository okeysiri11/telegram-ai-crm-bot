/**
 * Click vs orbit/pan: only treat pointer-up as a click when movement is small.
 */

export const CLICK_DRAG_THRESHOLD_PX = 8;

export type PointerXY = { x: number; y: number };

export function pointerDeltaPx(a: PointerXY, b: PointerXY): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

export function isClickGesture(down: PointerXY, up: PointerXY, alreadyMoved = false): boolean {
  if (alreadyMoved) return false;
  return pointerDeltaPx(down, up) <= CLICK_DRAG_THRESHOLD_PX;
}

export function exceedsDragThreshold(down: PointerXY, current: PointerXY): boolean {
  return pointerDeltaPx(down, current) > CLICK_DRAG_THRESHOLD_PX;
}
