import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { TrendChart, DepartmentsComparisonChart } from '../components/charts'

interface WeeklySummary {
  total_sales: number
  total_customers: number
  total_transactions: number
  log_count: number
  week_start: string
  week_end: string
}

interface TrendData {
  date: string
  sales: number
  customers: number
  transactions: number
  weather?: string
}

interface DepartmentComparisonData {
  department_id: number
  department_name: string
  department_code: string
  sales: number
  customers: number
  transactions: number
  log_count: number
}

const Dashboard = () => {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const navigate = useNavigate()
  const [summary, setSummary] = useState<WeeklySummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [trendData, setTrendData] = useState<TrendData[]>([])
  const [departmentsData, setDepartmentsData] = useState<DepartmentComparisonData[]>([])
  const [isLoadingCharts, setIsLoadingCharts] = useState(false)
  const [selectedDepartmentId] = useState<number | null>(null)

  // マネージャー/head向けの表示判定
  const isManagerOrHead = user?.role === 'manager' || user?.role === 'admin' || user?.role === 'head'

  useEffect(() => {
    fetchSummary()
    if (isManagerOrHead) {
      fetchCharts()
    }
  }, [isManagerOrHead])

  useEffect(() => {
    if (isManagerOrHead && selectedDepartmentId !== null) {
      fetchTrendChart(selectedDepartmentId)
    }
  }, [selectedDepartmentId, isManagerOrHead])

  const fetchSummary = async () => {
    try {
      const response = await api.get('/api/daily-logs/summary/week')
      setSummary(response.data)
    } catch (error) {
      console.error('サマリー取得エラー:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchCharts = async () => {
    setIsLoadingCharts(true)
    try {
      // トレンドグラフ（自部署）
      const trendResponse = await api.get(`/api/daily-logs/chart/trend?days=14`)
      setTrendData(trendResponse.data)

      // 部署間比較グラフ（head/managerのみ）
      if (user?.role === 'head' || user?.role === 'admin') {
        const deptResponse = await api.get('/api/daily-logs/chart/departments-comparison')
        setDepartmentsData(deptResponse.data)
      }
    } catch (error) {
      console.error('グラフデータ取得エラー:', error)
    } finally {
      setIsLoadingCharts(false)
    }
  }

  const fetchTrendChart = async (departmentId: number) => {
    try {
      const response = await api.get(`/api/daily-logs/chart/trend?department_id=${departmentId}&days=14`)
      setTrendData(response.data)
    } catch (error) {
      console.error('トレンドグラフ取得エラー:', error)
    }
  }

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'おはようございます'
    if (hour < 18) return 'こんにちは'
    return 'こんばんは'
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount)
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* ヘッダー */}
      <header className="bg-mikamo-blue text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">
              {getGreeting()}、{user?.full_name}さん！🍵
            </h1>
            <p className="text-sm opacity-90 mt-1">
              {format(new Date(), 'yyyy年M月d日(E)', { locale: ja })}
            </p>
          </div>
          <button
            onClick={logout}
            className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
          >
            ログアウト
          </button>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* マネージャー/head向けグラフセクション */}
        {isManagerOrHead && (
          <div className="space-y-6">
            {/* トレンドグラフ */}
            <div className="card">
              <h2 className="text-xl font-bold mb-4 text-mikamo-blue">
                売上・客数トレンド（14日間）
              </h2>
              {isLoadingCharts ? (
                <div className="flex items-center justify-center h-64">
                  <div className="text-gray-500">読み込み中...</div>
                </div>
              ) : trendData.length > 0 ? (
                <TrendChart data={trendData} />
              ) : (
                <div className="text-center py-8 text-gray-500">
                  データがありません
                </div>
              )}
            </div>

            {/* 部署間比較グラフ（head/adminのみ） */}
            {(user?.role === 'head' || user?.role === 'admin') && (
              <div className="card">
                <h2 className="text-xl font-bold mb-4 text-mikamo-blue">
                  部署間比較（今日の状況）
                </h2>
                {isLoadingCharts ? (
                  <div className="flex items-center justify-center h-64">
                    <div className="text-gray-500">読み込み中...</div>
                  </div>
                ) : departmentsData.length > 0 ? (
                  <DepartmentsComparisonChart data={departmentsData} />
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    データがありません
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* 今週の頑張り */}
        {!isLoading && summary && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4 text-mikamo-blue">
              今週のあなたはすごい！✨
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">合計売上</p>
                <p className="text-2xl font-bold text-mikamo-blue">
                  {formatCurrency(summary.total_sales)}
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">投稿回数</p>
                <p className="text-2xl font-bold text-mikamo-orange">
                  {summary.log_count}件
                </p>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">お客様数</p>
                <p className="text-2xl font-bold text-green-600">
                  {summary.total_customers}人
                </p>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">取引数</p>
                <p className="text-2xl font-bold text-purple-600">
                  {summary.total_transactions}件
                </p>
              </div>
            </div>
          </div>
        )}

        {/* チームの状況 */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4 text-mikamo-blue">
            チームの状況
          </h2>
          <p className="text-gray-600">
            今日の投稿数：準備中（v0.3で実装予定）
          </p>
        </div>

        {/* クイックアクション */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4 text-mikamo-blue">
            クイックアクション
          </h2>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/daily-log')}
              className="btn-primary w-full"
            >
              今日の振り返りを入力
            </button>
            <button
              onClick={() => navigate('/ai')}
              className="btn-secondary w-full"
            >
              AIに相談する
            </button>
          </div>
        </div>
      </div>

      {/* フローティングアクションボタン */}
      <div className="fixed bottom-6 right-6">
        <button
          onClick={() => navigate('/daily-log')}
          className="bg-mikamo-orange text-white w-16 h-16 rounded-full shadow-lg flex items-center justify-center text-2xl hover:bg-orange-600 transition-colors"
          aria-label="振り返りを入力"
        >
          ✏️
        </button>
      </div>
    </div>
  )
}

export default Dashboard
