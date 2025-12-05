import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import { TrendChart, DepartmentsComparisonChart } from '../components/charts'
import Layout from '../components/Layout'

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

interface BusinessUnit {
  id: number
  name: string
  code: string
  type: string
  description?: string
}

const Dashboard = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { businessUnitLabel, primaryColor } = useTenantSettings()
  const [summary, setSummary] = useState<WeeklySummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [trendData, setTrendData] = useState<TrendData[]>([])
  const [departmentsData, setDepartmentsData] = useState<DepartmentComparisonData[]>([])
  const [isLoadingCharts, setIsLoadingCharts] = useState(false)
  const [selectedDepartmentId] = useState<number | null>(null)
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([])
  const [isLoadingBusinessUnits, setIsLoadingBusinessUnits] = useState(false)

  // マネージャー/head向けの表示判定
  const isManagerOrHead = user?.role === 'manager' || user?.role === 'admin' || user?.role === 'head'

  useEffect(() => {
    fetchSummary()
    if (isManagerOrHead) {
      fetchCharts()
    }
    // 本部ユーザー（head/admin）の場合は事業部門一覧を取得
    if (user?.role === 'head' || user?.role === 'admin') {
      fetchBusinessUnits()
    }
  }, [isManagerOrHead, user])

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

  const fetchBusinessUnits = async () => {
    setIsLoadingBusinessUnits(true)
    try {
      const response = await api.get('/api/portal/business-units')
      setBusinessUnits(response.data)
    } catch (error) {
      console.error('事業部門取得エラー:', error)
    } finally {
      setIsLoadingBusinessUnits(false)
    }
  }

  const getBusinessUnitRoute = (code: string) => {
    // 事業部門コードからルートパスを取得
    const routeMap: Record<string, string> = {
      'gas': '/portal/gas-station',
      'coating': '/portal/car-coating',
      'mnet': '/portal/used-car',
      'cafe': '/portal/cafe',
      'head': '/portal/hq',
      'hq': '/portal/hq',  // 後方互換性のため両方対応
    }
    return routeMap[code] || '/dashboard'
  }

  // 事業部門の表示名を取得（APIから取得した名前を使用）
  const getBusinessUnitDisplayName = (bu: BusinessUnit) => {
    return bu.name || bu.code
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount)
  }

  return (
    <Layout showFab onFabClick={() => navigate('/daily-log')} fabLabel="✏️">
      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* 本部ユーザー向け: 事業部門ポータル切り替えカード */}
        {(user?.role === 'head' || user?.role === 'admin') && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
              {businessUnitLabel}ポータル
            </h2>
            {isLoadingBusinessUnits ? (
              <div className="flex items-center justify-center h-32">
                <div className="text-gray-500">読み込み中...</div>
              </div>
            ) : businessUnits.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {businessUnits
                  .filter((bu) => bu.code !== 'head' && bu.code !== 'hq')  // 本部以外の部門を表示
                  .map((bu) => (
                    <button
                      key={bu.id}
                      onClick={() => navigate(getBusinessUnitRoute(bu.code))}
                      className="p-4 bg-white border-2 border-gray-200 rounded-lg hover:bg-blue-50 transition-all text-left"
                      style={{ borderColor: 'transparent' }}
                      onMouseEnter={(e) => (e.currentTarget.style.borderColor = primaryColor)}
                      onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'transparent')}
                    >
                      <div className="font-semibold" style={{ color: primaryColor }}>
                        {getBusinessUnitDisplayName(bu)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">
                        {bu.description || `${businessUnitLabel}ポータルへ`}
                      </div>
                    </button>
                  ))}
                {/* 本部ビューへのリンク */}
                <button
                  onClick={() => navigate('/portal/hq')}
                  className="p-4 text-white border-2 rounded-lg hover:opacity-90 transition-all text-left"
                  style={{ backgroundColor: primaryColor, borderColor: primaryColor }}
                >
                  <div className="font-semibold">本部ビュー（全社ダッシュボード）</div>
                  <div className="text-sm opacity-90 mt-1">
                    全{businessUnitLabel}を横断して状況を把握
                  </div>
                </button>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                事業部門情報が取得できませんでした
              </div>
            )}
          </div>
        )}

        {/* マネージャー/head向けグラフセクション */}
        {isManagerOrHead && (
          <div className="space-y-6">
            {/* トレンドグラフ */}
            <div className="card">
              <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
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
                <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
                  {businessUnitLabel}間比較（今日の状況）
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
            <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
              今週のサマリー
            </h2>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">合計売上</p>
                <p className="text-2xl font-bold" style={{ color: primaryColor }}>
                  {formatCurrency(summary.total_sales)}
                </p>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">投稿回数</p>
                <p className="text-2xl font-bold text-orange-600">
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
          <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
            チームの状況
          </h2>
          <p className="text-gray-600">
            今日の投稿数：準備中
          </p>
        </div>

        {/* クイックアクション */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
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
            <button
              onClick={() => navigate('/knowledge')}
              className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              ナレッジベースを見る
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default Dashboard
