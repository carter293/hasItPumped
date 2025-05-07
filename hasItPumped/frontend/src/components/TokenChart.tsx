import { useState } from "react";
import {
  ComposedChart,
  Area,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Customized,
} from "recharts";

interface TokenDataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: TokenDataPoint;
    dataKey?: string;
    color?: string;
    name?: string;
    value?: number;
  }>;
  label?: string;
}

const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-gray-800 border border-gray-700 p-2 rounded shadow text-xs">
        <p className="font-medium text-white">{new Date(data.date).toLocaleDateString()}</p>
        <p className="text-gray-300">Open: ${data.open.toFixed(6)}</p>
        <p className="text-gray-300">High: ${data.high.toFixed(6)}</p>
        <p className="text-gray-300">Low: ${data.low.toFixed(6)}</p>
        <p className="text-gray-300">Close: ${data.close.toFixed(6)}</p>
        <p className="text-gray-300">Volume: ${new Intl.NumberFormat().format(data.volume)}</p>
      </div>
    );
  }
  return null;
};

interface TokenChartProps {
  data: TokenDataPoint[];
  loading: boolean;
}

export default function TokenChart({ data, loading }: TokenChartProps) {
  const [chartType, setChartType] = useState("candlestick");

  if (loading || !data || data.length === 0) {
    return (
      <div className="w-full h-64 flex items-center justify-center bg-gray-800/50 rounded">
        <div className="animate-pulse text-gray-400">Loading chart data...</div>
      </div>
    );
  }

  const sortedData = [...data].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const allPrices = sortedData.flatMap((d) => [d.open, d.high, d.low, d.close]);
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);
  const pricePadding = (maxPrice - minPrice) * 0.1;

  const maxVolume = Math.max(...sortedData.map((d) => d.volume));

  const formatXAxis = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.getDate() + "/" + (date.getMonth() + 1);
  };

  // Prepare data for area chart with proper price field
  const areaChartData = sortedData.map((item) => ({
    ...item,
    price: item.close,
  }));

  return (
    <div className="w-full h-full">
      <div className="flex justify-end mb-4">
        <div className="inline-flex rounded-md shadow-sm" role="group">
          <button
            type="button"
            onClick={() => setChartType("candlestick")}
            className={`px-3 py-1 text-xs font-medium rounded-l ${chartType === "candlestick"
                ? "bg-blue-600 text-white"
                : "bg-gray-700 text-gray-300"
              }`}
          >
            Candlestick
          </button>
          <button
            type="button"
            onClick={() => setChartType("area")}
            className={`px-3 py-1 text-xs font-medium rounded-r ${chartType === "area"
                ? "bg-blue-600 text-white"
                : "bg-gray-700 text-gray-300"
              }`}
          >
            Area
          </button>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart
          data={chartType === "area" ? areaChartData : sortedData}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            type="category"
            scale="band"
            interval={Math.max(0, Math.floor(sortedData.length / 10))} // Show fewer ticks for clarity
            tickFormatter={formatXAxis}
            stroke="#9ca3af"
            tick={{ fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            padding={{ left: 0, right: 0 }}
          />
          <YAxis
            yAxisId="price"
            domain={[minPrice - pricePadding, maxPrice + pricePadding]}
            tickFormatter={(value) => value.toFixed(6)}
            stroke="#9ca3af"
            tick={{ fontSize: 12 }}
            width={80}
          />
          <YAxis
            yAxisId="volume"
            orientation="right"
            domain={[0, maxVolume * 1.1]}
            tickFormatter={(value) =>
              value === 0 ? "0" : value >= 1_000_000 ? `${(value / 1_000_000).toFixed(1)}M` : `${(value / 1_000).toFixed(1)}K`
            }
            stroke="#9ca3af"
            tick={{ fontSize: 12 }}
            width={50}
          />
          <Tooltip
            content={<CustomTooltip />}
            cursor={chartType === "candlestick" ? <CenteredCursor /> : { stroke: "#ffffff", strokeWidth: 1, opacity: 0.2 }}
            isAnimationActive={false}
          />
          <Legend />

          <Bar
            dataKey="volume"
            yAxisId="volume"
            fill="#4b5563"
            opacity={0.5}
            name="Volume"
          />

          {chartType === "candlestick" ? (
            <Customized component={CandlestickRenderer} />
          ) : (
            <>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <Area
                type="monotone"
                dataKey="price"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#colorPrice)"
                yAxisId="price"
                name="Price"
                activeDot={{ r: 6, stroke: "#fff", strokeWidth: 1 }}
                isAnimationActive={false}
              />
            </>
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

const CandlestickRenderer = (props: any) => {
  const { xAxisMap, yAxisMap, data, tooltipItem } = props;
  const xAxis = xAxisMap["0"];
  const yAxis = yAxisMap["price"];
  if (!xAxis || !yAxis || !data) return null;

  const totalDataPoints = data.length;
  const totalChartWidth = xAxis.width ?? 800;
  const bandwidth = xAxis.bandwidth ? xAxis.bandwidth() : totalChartWidth / totalDataPoints;

  const candleWidth = Math.min(Math.max(bandwidth * 0.7, 4), 20);
  const minBodyHeight = 3; // ensures visible body even with very close open/close

  return (
    <g className="recharts-layer recharts-candlestick">
      {data.map((entry: TokenDataPoint, index: number) => {
        const x = xAxis.scale(entry.date);
        if (x == null) return null;

        const yHigh = yAxis.scale(entry.high);
        const yLow = yAxis.scale(entry.low);
        const yOpen = yAxis.scale(entry.open);
        const yClose = yAxis.scale(entry.close);

        const isGrowing = entry.close >= entry.open;
        const color = isGrowing ? "#10b981" : "#ef4444";

        const bodyY = Math.min(yOpen, yClose);
        const rawBodyHeight = Math.abs(yClose - yOpen);
        const bodyHeight = Math.max(minBodyHeight, rawBodyHeight);

        const centerX = x + bandwidth / 2;
        const bodyX = centerX - candleWidth / 2;

        const strokeWidth = 1;
        const opacity = 0.9;

        return (
          <g key={`candle-${index}`} className="recharts-layer">
            {/* Wick */}
            <line
              x1={centerX}
              y1={yHigh}
              x2={centerX}
              y2={yLow}
              stroke={color}
              strokeWidth={strokeWidth}
              opacity={opacity}
              className="recharts-candlestick-wick"
            />
            {/* Body (with minimum height for visibility) */}
            <rect
              x={bodyX}
              y={bodyY}
              width={candleWidth}
              height={bodyHeight}
              fill={color}
              stroke={"#ffffff"}
              strokeWidth={0}
              opacity={opacity}
              className="recharts-candlestick-body"
            />
          </g>
        );
      })}
    </g>
  );
};

const CenteredCursor = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const centerX = x != null && width != null ? x + width / 2 : x;

  return (
    <g>
      <line
        x1={centerX}
        x2={centerX}
        y1={0}
        y2={height}
        stroke="#ffffff"
        strokeWidth={1}
        strokeDasharray="3 3"
        opacity={0.4}
      />
      <line
        x1={0}
        x2="100%"
        y1={y}
        y2={y}
        stroke="#ffffff"
        strokeWidth={1}
        strokeDasharray="3 3"
        opacity={0.4}
      />
    </g>
  );
};