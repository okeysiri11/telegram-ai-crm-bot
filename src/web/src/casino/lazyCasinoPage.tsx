import { lazy, Suspense, type ComponentType } from "react";
import { RoomSkeleton } from "./components/RoomSkeleton";

/** Route-level lazy page with Odessa Prime loading fallback. */
export function lazyCasinoPage(loader: () => Promise<{ default: ComponentType }>) {
  const Page = lazy(loader);
  return function LazyCasinoPage() {
    return (
      <Suspense fallback={<RoomSkeleton />}>
        <Page />
      </Suspense>
    );
  };
}
