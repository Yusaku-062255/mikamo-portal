import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { TrendChart } from '../components/charts'

interface BusinessUnit {
  id: number
  name: string
  type: string
  code: string
  description?: string
}

interface PortalSummary {
  business_unit_id: number
  business_unit_name: string
  business_unit_code: string
  total_sales: number
  total_customers: number
  total_transactions: number
  log_count: number
  period_start: string
  period_end: string
}

interface TrendData {
  date: string
  sales: number
  customers: number
  transactions: number
  weather?: string
}

interface PortalBaseProps {
  businessUnitCode: string
  pageTitle: string
}

const PortalBase = ({ businessUnitCode, pageTitle }: PortalBaseProps) => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const [businessUnit, setBusinessUnit] = useState<BusinessUnit | null>(null)
  const [summary, setSummary] = useState<PortalSummary | null>(null)
  const [trendData, setTrendData] = useState<TrendData[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingCharts, setIsLoadingCharts] = useState(false)

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    fetchBusinessUnit()
  }, [user, businessUnitCode])

  useEffect(() => {
    if (businessUnit) {
      fetchSummary()
      fetchTrendChart()
    }
  }, [businessUnit])

  const fetchBusinessUnit = async () => {
    try {
      // 事業部門一覧から該当するものを取得
      const response = await api.get('/api/portal/business-units')
      const units = response.data as BusinessUnit[]
      const unit = units.find((u) => u.code === businessUnitCode)
      
      if (!unit) {
        console.error(`事業部門が見つかりません: ${businessUnitCode}`)
        navigate('/dashboard')
        return
      }
      
      // 権限チェック
      if (user?.role === 'staff' || user?.role === 'manager') {
        if (user.business_unit_id !== unit.id) {
          // 自分の事業部門以外は閲覧不可
          navigate('/dashboard')
          return
        }
      }
      
      setBusinessUnit(unit)
    } catch (error) {
      console.error('事業部門取得エラー:', error)
      navigate('/dashboard')
    }
  }

  const fetchSummary = async () => {
    if (!businessUnit) return
    
    setIsLoading(true)
    try {
      const response = await api.get(`/api/portal/business-units/${businessUnit.id}/summary?days=14`)
      setSummary(response.data)
    } catch (error) {
      console.error('サマリー取得エラー:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchTrendChart = async () => {
    if (!businessUnit) return
    
    setIsLoadingCharts(true)
    try {
      // Departmentのcodeからdepartment_idを取得する必要がある
      // 一旦、既存のAPIを使用
      const response = await api.get(`/api/daily-logs/chart/trend?days=14`)
      setTrendData(response.data)
    } catch (error) {
      console.error('トレンドグラフ取得エラー:', error)
    } finally {
      setIsLoadingCharts(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount)
  }

  if (!user || !businessUnit) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* ヘッダー */}
      <header className="bg-mikamo-blue text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">{pageTitle}</h1>
            <p className="text-sm opacity-90 mt-1">
              {format(new Date(), 'yyyy年M月d日(E)', { locale: ja })}
            </p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
          >
            ダッシュボードに戻る
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* サマリーカード */}
        {!isLoading && summary && (
          <div className="card">
            <h2 className="text-xl font-bold mb-4 text-mikamo-blue">
              {businessUnit.name} のサマリー（直近14日間）
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

        {/* トレンドグラフ */}
        {(user.role === 'manager' || user.role === 'head' || user.role === 'admin') && (
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
        )}

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
    </div>
  )
}

export default PortalBase

