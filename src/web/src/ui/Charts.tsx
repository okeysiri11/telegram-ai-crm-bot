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

export function Charts({ labels, values }: { labels: string[]; values: number[] }) {
  return (
    <Line
      data={{
        labels,
        datasets: [
          {
            label: "KPI",
            data: values,
            borderColor: "#0f6a5a",
            backgroundColor: "rgba(15,106,90,0.15)",
            tension: 0.35,
          },
        ],
      }}
      options={{ responsive: true, plugins: { legend: { display: false } } }}
    />
  );
}
