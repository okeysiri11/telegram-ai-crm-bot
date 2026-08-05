import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

function prefersReducedMotion() {
  if (typeof window === "undefined") return false;
  return (
    window.matchMedia("(prefers-reduced-motion: reduce)").matches ||
    document.documentElement.getAttribute("data-reduced-motion") === "true"
  );
}

export function Charts({ labels, values }: { labels: string[]; values: number[] }) {
  const reduced = prefersReducedMotion();
  return (
    <div className="edm-partial-update">
      <Line
        data={{
          labels,
          datasets: [
            {
              label: "KPI",
              data: values,
              borderColor: "var(--eds-primary, #0f6a5a)",
              backgroundColor: "color-mix(in oklab, var(--eds-primary) 15%, transparent)",
              tension: 0.35,
            },
          ],
        }}
        options={{
          responsive: true,
          animation: reduced ? false : { duration: 320, easing: "easeOutQuart" },
          plugins: { legend: { display: false } },
        }}
      />
    </div>
  );
}
