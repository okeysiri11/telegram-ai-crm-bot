import { UniversalCommandPalette } from "./UniversalCommandPalette";

/** Dedicated omnibox surface — same engine, omnibox mode. */
export function Omnibox({ open, onClose }: { open: boolean; onClose: () => void }) {
  return <UniversalCommandPalette open={open} onClose={onClose} initialMode="omnibox" />;
}
