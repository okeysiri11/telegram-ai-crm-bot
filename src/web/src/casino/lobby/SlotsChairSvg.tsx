import { HALL_ART } from "./hallZones";

type ChairPath = {
  id: string;
  d: string;
};

type ChairGroup = {
  id: "slot-chair-1" | "slot-chair-2" | "slot-chair-3";
  paths: ChairPath[];
};

/**
 * Open gold rims on photographed chair edges only.
 * Same 1600×1066 space as hall.jpg. Hidden geometry is omitted.
 */
export const SLOTS_CHAIR_GROUPS: readonly ChairGroup[] = [
  {
    id: "slot-chair-1",
    paths: [
      { id: "c1-seat", d: "M 1282 734 C 1286 732 1289 732 1292 736" },
      { id: "c1-footring", d: "M 1290 822 C 1294 819 1300 820 1306 826" },
    ],
  },
  {
    id: "slot-chair-2",
    paths: [
      { id: "c2-seat", d: "M 1400 756 C 1408 753 1416 754 1424 758" },
    ],
  },
  {
    id: "slot-chair-3",
    paths: [],
  },
];

export function chairPathClosed(d: string): boolean {
  return /z\s*$/i.test(d.trim());
}

type Props = {
  active: boolean;
};

export function SlotsChairSvg({ active }: Props) {
  return (
    <svg
      className={`op-slots-chairs${active ? " is-on" : ""}`}
      data-testid="slots-chair-overlay"
      viewBox={`0 0 ${HALL_ART.width} ${HALL_ART.height}`}
      preserveAspectRatio="xMidYMid meet"
      aria-hidden
    >
      <defs>
        <filter id="op-chair-rim-glow" x="-20%" y="-20%" width="140%" height="140%" colorInterpolationFilters="sRGB">
          <feGaussianBlur in="SourceGraphic" stdDeviation="1.15" result="blur" />
          <feFlood floodColor="#f7c85a" floodOpacity="0.28" result="gold" />
          <feComposite in="gold" in2="blur" operator="in" result="glow" />
          <feMerge>
            <feMergeNode in="glow" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {SLOTS_CHAIR_GROUPS.map((chair) => (
        <g key={chair.id} id={chair.id} data-chair={chair.id} filter="url(#op-chair-rim-glow)">
          {chair.paths.map((path) => (
            <path
              key={path.id}
              data-chair-path={path.id}
              className="op-chair-core"
              d={path.d}
              fill="none"
            />
          ))}
        </g>
      ))}
    </svg>
  );
}
