import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface DepartmentData {
  department_id: number
  department_name: string
  department_code: string
  sales: number
  customers: number
  transactions: number
  log_count: number
}

interface DepartmentsComparisonChartProps {
  data: DepartmentData[]
}

const departmentNameMap: Record<string, string> = {
  coating: 'SOUP',
  mnet: 'M-NET',
  gas: 'ミカモ石油',
  cafe: 'ミカモ喫茶',
  head: '本部',
}

export const DepartmentsComparisonChart = ({ data }: DepartmentsComparisonChartProps) => {
  // データを整形
  const chartData = data.map((item) => ({
    name: departmentNameMap[item.department_code] || item.department_name,
    sales: item.sales,
    customers: item.customers,
    transactions: item.transactions,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value: number, name: string) => {
            if (name === 'sales') {
              return [`${value.toLocaleString()}円`, '売上']
            }
            if (name === 'customers') {
              return [`${value}人`, '客数']
            }
            if (name === 'transactions') {
              return [`${value}件`, '取引数']
            }
            return [value, name]
          }}
        />
        <Legend />
        <Bar dataKey="sales" fill="#1e40af" name="売上" />
        <Bar dataKey="customers" fill="#f97316" name="客数" />
      </BarChart>
    </ResponsiveContainer>
  )
}

