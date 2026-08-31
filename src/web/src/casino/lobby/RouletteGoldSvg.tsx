import { HALL_ART } from "./hallZones";

type GoldPath = {
  id: string;
  d: string;
};

type GoldGroup = {
  id: "roulette-sign" | "roulette-lamp" | "roulette-wheel" | "roulette-table" | "roulette-chair";
  paths: GoldPath[];
};

/**
 * Open gold rims on photographed roulette edges only.
 * Same 1600×1066 space as hall.jpg. Hidden or uncertain geometry is omitted.
 */
export const ROULETTE_GOLD_GROUPS: readonly GoldGroup[] = [
  {
    id: "roulette-sign",
    paths: [
      { id: "sign-top", d: "M 78 313 L 358 312" },
      { id: "sign-right", d: "M 358 312 L 362 376" },
      { id: "sign-bottom", d: "M 362 376 L 80 376" },
      { id: "sign-left", d: "M 80 376 L 78 313" },
    ],
  },
  {
    id: "roulette-lamp",
    paths: [
      { id: "lamp-shade-top", d: "M 394 494 L 408 493" },
      { id: "lamp-shade-left", d: "M 394 494 L 393 516" },
      { id: "lamp-shade-right", d: "M 408 493 L 415 516" },
      { id: "lamp-stem", d: "M 403 518 L 403 545" },
    ],
  },
  {
    id: "roulette-wheel",
    paths: [
      { id: "wheel-front-rim", d: "M 16 816 C 55 796 115 788 170 806" },
    ],
  },
  {
    id: "roulette-table",
    paths: [
      {
        id: "table-rail",
        d: "M 20 906 C 70 904 120 898 180 888 C 240 876 300 858 360 830 C 400 810 440 780 460 765",
      },
    ],
  },
  {
    id: "roulette-chair",
    paths: [
      { id: "chair-backrest", d: "M 488 768 C 510 752 535 752 556 770" },
    ],
  },
];

export function roulettePathClosed(d: string): boolean {
  return /z\s*$/i.test(d.trim());
}

type Props = {
  active: boolean;
};

export function RouletteGoldSvg({ active }: Props) {
  return (
    <svg
      className={`op-roulette-gold${active ? " is-on" : ""}`}
      data-testid="roulette-gold-overlay"
      viewBox={`0 0 ${HALL_ART.width} ${HALL_ART.height}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden
    >
      <defs>
        <filter id="op-roulette-rim-glow" x="-20%" y="-20%" width="140%" height="140%" colorInterpolationFilters="sRGB">
          <feGaussianBlur in="SourceGraphic" stdDeviation="1.15" result="blur" />
          <feFlood floodColor="#f7c85a" floodOpacity="0.28" result="gold" />
          <feComposite in="gold" in2="blur" operator="in" result="glow" />
          <feMerge>
            <feMergeNode in="glow" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {ROULETTE_GOLD_GROUPS.map((group) => (
        <g key={group.id} id={group.id} data-roulette-part={group.id} filter="url(#op-roulette-rim-glow)">
          {group.paths.map((path) => (
            <path
              key={path.id}
              data-roulette-path={path.id}
              className="op-gold-core"
              d={path.d}
              fill="none"
            />
          ))}
        </g>
      ))}
    </svg>
  );
}
