import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'

interface TrendData {
  date: string
  sales: number
  customers: number
  transactions: number
  weather?: string
}

interface TrendChartProps {
  data: TrendData[]
}

const weatherEmoji: Record<string, string> = {
  sunny: '☀️',
  cloudy: '☁️',
  rainy: '🌧️',
  snow: '❄️',
}

export const TrendChart = ({ data }: TrendChartProps) => {
  // データを整形（日付を短縮形式に）
  const chartData = data.map((item) => ({
    ...item,
    dateLabel: format(new Date(item.date), 'M/d'),
    weatherEmoji: item.weather ? weatherEmoji[item.weather] : '',
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="dateLabel"
          tick={{ fontSize: 12 }}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 12 }}
          label={{ value: '売上（円）', angle: -90, position: 'insideLeft' }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 12 }}
          label={{ value: '客数', angle: 90, position: 'insideRight' }}
        />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'sales') {
              return [`${value.toLocaleString()}円`, '売上']
            }
            if (name === 'customers') {
              return [`${value}人`, '客数']
            }
            return [value, name]
          }}
        />
        <Legend />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="sales"
          stroke="#1e40af"
          strokeWidth={2}
          name="売上"
          dot={{ r: 4 }}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="customers"
          stroke="#f97316"
          strokeWidth={2}
          name="客数"
          dot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

