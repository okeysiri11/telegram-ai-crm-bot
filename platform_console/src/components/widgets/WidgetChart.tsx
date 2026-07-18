import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
);

interface WidgetChartProps {
  type: 'bar' | 'line';
  data: Record<string, unknown>;
}

function extractSeries(data: Record<string, unknown>): { labels: string[]; values: number[] } {
  if (Array.isArray(data.series)) {
    const series = data.series as Array<{ label?: string; value?: number; name?: string; count?: number }>;
    return {
      labels: series.map((s) => s.label || s.name || ''),
      values: series.map((s) => Number(s.value ?? s.count ?? 0)),
    };
  }
  if (Array.isArray(data.items)) {
    const items = data.items as Array<{ label?: string; value?: number; name?: string; count?: number }>;
    return {
      labels: items.map((s) => s.label || s.name || ''),
      values: items.map((s) => Number(s.value ?? s.count ?? 0)),
    };
  }
  const entries = Object.entries(data).filter(([, v]) => typeof v === 'number');
  if (entries.length) {
    return { labels: entries.map(([k]) => k), values: entries.map(([, v]) => v as number) };
  }
  return { labels: ['n/a'], values: [0] };
}

export function WidgetChart({ type, data }: WidgetChartProps) {
  const { labels, values } = extractSeries(data);
  const chartData = {
    labels,
    datasets: [
      {
        label: String(data.title || 'Value'),
        data: values,
        backgroundColor: 'rgba(37, 99, 235, 0.5)',
        borderColor: 'rgb(37, 99, 235)',
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: { y: { beginAtZero: true } },
  };

  return (
    <div className="h-40">
      {type === 'line' ? <Line data={chartData} options={options} /> : <Bar data={chartData} options={options} />}
    </div>
  );
}
