import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { loginRedirect, rememberReturnTo } from "@/navigation/safeReturnTo";

type GuestCtx = {
  openGuest: (returnTo: string) => void;
};

const Ctx = createContext<GuestCtx>({ openGuest: () => undefined });

export function useCasinoGuest() {
  return useContext(Ctx);
}

export function CasinoGuestProvider({ children }: { children: ReactNode }) {
  const [returnTo, setReturnTo] = useState<string | null>(null);
  const value = useMemo<GuestCtx>(
    () => ({
      openGuest: (path: string) => {
        rememberReturnTo(path);
        setReturnTo(path);
      },
    }),
    [],
  );

  return (
    <Ctx.Provider value={value}>
      {children}
      {returnTo ? <CasinoGuestModal returnTo={returnTo} onClose={() => setReturnTo(null)} /> : null}
    </Ctx.Provider>
  );
}

export function CasinoGuestModal({ returnTo, onClose }: { returnTo: string; onClose: () => void }) {
  const href = loginRedirect(returnTo);
  return (
    <div className="op-modal-veil" role="presentation" onClick={onClose} data-testid="casino-guest-modal">
      <div className="op-modal" role="dialog" aria-labelledby="op-guest-title" onClick={(e) => e.stopPropagation()}>
        <p className="op-kicker">ODESSA PRIME</p>
        <h2 id="op-guest-title">Нужен вход</h2>
        <p className="op-sub">Ставки PLAY доступны после входа. Реальных платежей нет. Вы останетесь в этом зале.</p>
        <div className="op-actions">
          <a className="op-cta" href={href}>
            ВОЙТИ
          </a>
          <button className="op-ghost" type="button" onClick={onClose}>
            ОСТАТЬСЯ ГОСТЕМ
          </button>
        </div>
      </div>
    </div>
  );
}
