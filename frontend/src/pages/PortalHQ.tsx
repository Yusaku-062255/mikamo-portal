import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { DepartmentsComparisonChart } from '../components/charts'
import Layout from '../components/Layout'

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

interface DepartmentComparisonData {
  department_id: number
  department_name: string
  department_code: string
  sales: number
  customers: number
  transactions: number
  log_count: number
}

interface BusinessUnitHealth {
  business_unit_id: number
  business_unit_name: string
  risk_score: number
  opportunity_score: number
  last_updated_at: string
}

interface Insight {
  id: number
  title: string
  content: string
  type: string
  score: number
  business_unit_name: string | null
}

interface Issue {
  id: number
  title: string
  topic: string
  status: string
  business_unit_name: string | null
}

const PortalHQ = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { primaryColor } = useTenantSettings()
  const [summaries, setSummaries] = useState<PortalSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [departmentsData, setDepartmentsData] = useState<DepartmentComparisonData[]>([])
  const [isLoadingCharts, setIsLoadingCharts] = useState(false)
  const [healthData, setHealthData] = useState<BusinessUnitHealth[]>([])
  const [insights, setInsights] = useState<Insight[]>([])
  const [recentIssues, setRecentIssues] = useState<Issue[]>([])
  const [isLoadingHealth, setIsLoadingHealth] = useState(false)

  // 権限チェック
  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    if (user.role !== 'head' && user.role !== 'admin') {
      navigate('/dashboard')
      return
    }
  }, [user, navigate])

  useEffect(() => {
    if (user && (user.role === 'head' || user.role === 'admin')) {
      fetchHQSummary()
      fetchDepartmentsComparison()
      fetchHealthData()
      fetchTopInsights()
      fetchRecentIssues()
    }
  }, [user])

  const fetchHQSummary = async () => {
    setIsLoading(true)
    try {
      const response = await api.get('/api/portal/hq/summary?days=14')
      setSummaries(response.data)
    } catch (error) {
      console.error('本部サマリー取得エラー:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchDepartmentsComparison = async () => {
    setIsLoadingCharts(true)
    try {
      const response = await api.get('/api/daily-logs/chart/departments-comparison')
      setDepartmentsData(response.data)
    } catch (error) {
      console.error('部署間比較データ取得エラー:', error)
    } finally {
      setIsLoadingCharts(false)
    }
  }

  const fetchHealthData = async () => {
    setIsLoadingHealth(true)
    try {
      const response = await api.get('/api/portal/hq/health')
      setHealthData(response.data)
    } catch (error) {
      console.error('健康度スコア取得エラー:', error)
    } finally {
      setIsLoadingHealth(false)
    }
  }

  const fetchTopInsights = async () => {
    try {
      const response = await api.get('/api/insights?min_score=70&limit=5')
      setInsights(response.data)
    } catch (error) {
      console.error('Insight取得エラー:', error)
    }
  }

  const fetchRecentIssues = async () => {
    try {
      const response = await api.get('/api/issues?limit=10')
      setRecentIssues(response.data)
    } catch (error) {
      console.error('Issue取得エラー:', error)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ja-JP', {
      style: 'currency',
      currency: 'JPY',
    }).format(amount)
  }

  if (!user || (user.role !== 'head' && user.role !== 'admin')) {
    return null
  }

  return (
    <Layout>
      {/* 本部ビュー専用ヘッダー */}
      <div
        className="text-white p-4 shadow-md -mx-4 -mt-4 mb-6"
        style={{ backgroundColor: primaryColor }}
      >
        <div className="flex items-center justify-between max-w-6xl mx-auto">
          <div>
            <h1 className="text-xl font-bold">本部ビュー（全社ダッシュボード）</h1>
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
      </div>

      <div className="max-w-6xl mx-auto space-y-6">
        {/* 部署間比較グラフ */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
            部署間比較（直近14日間）
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

        {/* 健康度スコア */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
            各事業部門の健康度スコア
          </h2>
          {isLoadingHealth ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-gray-500">読み込み中...</div>
            </div>
          ) : healthData.length === 0 ? (
            <div className="text-center py-4 text-gray-500">データがありません</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {healthData.map((health) => (
                <div
                  key={health.business_unit_id}
                  className="bg-white p-4 rounded-lg border border-gray-200"
                >
                  <h3 className="font-bold text-lg mb-3" style={{ color: primaryColor }}>
                    {health.business_unit_name}
                  </h3>
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-600">リスクスコア</span>
                        <span className={`text-sm font-semibold ${
                          health.risk_score >= 70 ? 'text-red-600' :
                          health.risk_score >= 50 ? 'text-orange-600' : 'text-gray-600'
                        }`}>
                          {health.risk_score}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            health.risk_score >= 70 ? 'bg-red-500' :
                            health.risk_score >= 50 ? 'bg-orange-500' : 'bg-gray-400'
                          }`}
                          style={{ width: `${health.risk_score}%` }}
                        ></div>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-600">機会スコア</span>
                        <span className={`text-sm font-semibold ${
                          health.opportunity_score >= 70 ? 'text-green-600' :
                          health.opportunity_score >= 50 ? 'text-blue-600' : 'text-gray-600'
                        }`}>
                          {health.opportunity_score}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            health.opportunity_score >= 70 ? 'bg-green-500' :
                            health.opportunity_score >= 50 ? 'bg-blue-500' : 'bg-gray-400'
                          }`}
                          style={{ width: `${health.opportunity_score}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 重要なInsight */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold" style={{ color: primaryColor }}>
              重要なAI分析・提案（Insight）
            </h2>
            <button
              onClick={() => navigate('/insights')}
              className="text-sm px-4 py-2 text-white rounded-lg hover:opacity-90 transition-colors"
              style={{ backgroundColor: primaryColor }}
            >
              すべて見る
            </button>
          </div>
          {insights.length === 0 ? (
            <div className="text-center py-4 text-gray-500">Insightがありません</div>
          ) : (
            <div className="space-y-3">
              {insights.map((insight) => (
                <div
                  key={insight.id}
                  className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold" style={{ color: primaryColor }}>{insight.title}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          insight.type === 'risk' ? 'bg-red-100 text-red-800' :
                          insight.type === 'opportunity' ? 'bg-green-100 text-green-800' :
                          'bg-blue-100 text-blue-800'
                        }`}>
                          {insight.type === 'risk' ? 'リスク' :
                           insight.type === 'opportunity' ? '機会' : '改善提案'}
                        </span>
                        <span className="text-xs text-gray-500">重要度: {insight.score}</span>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">{insight.content}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 最近のIssue */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold" style={{ color: primaryColor }}>
              最近の課題・困りごと（Issue）
            </h2>
            <button
              onClick={() => navigate('/issues')}
              className="text-sm px-4 py-2 text-white rounded-lg hover:opacity-90 transition-colors"
              style={{ backgroundColor: primaryColor }}
            >
              すべて見る
            </button>
          </div>
          {recentIssues.length === 0 ? (
            <div className="text-center py-4 text-gray-500">Issueがありません</div>
          ) : (
            <div className="space-y-3">
              {recentIssues.map((issue) => (
                <div
                  key={issue.id}
                  className="border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold" style={{ color: primaryColor }}>{issue.title}</h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          issue.status === 'open' ? 'bg-blue-100 text-blue-800' :
                          issue.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {issue.status === 'open' ? '未対応' :
                           issue.status === 'in_progress' ? '対応中' : '解決済み'}
                        </span>
                      </div>
                      {issue.business_unit_name && (
                        <p className="text-xs text-gray-500">{issue.business_unit_name}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 各事業部門のサマリー */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
            各事業部門のサマリー（直近14日間）
          </h2>
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">読み込み中...</div>
            </div>
          ) : summaries.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              データがありません
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {summaries.map((summary) => (
                <div
                  key={summary.business_unit_id}
                  className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
                >
                  <h3 className="font-bold text-lg mb-3" style={{ color: primaryColor }}>
                    {summary.business_unit_name}
                  </h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">合計売上</span>
                      <span className="font-semibold" style={{ color: primaryColor }}>
                        {formatCurrency(summary.total_sales)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">合計客数</span>
                      <span className="font-semibold">{summary.total_customers}人</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">取引数</span>
                      <span className="font-semibold">{summary.total_transactions}件</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">投稿数</span>
                      <span className="font-semibold">{summary.log_count}件</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* クイックアクション */}
        <div className="card">
          <h2 className="text-xl font-bold mb-4" style={{ color: primaryColor }}>
            クイックアクション
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <button
              onClick={() => navigate('/ai')}
              className="btn-primary"
            >
              AIに相談する
            </button>
            {user.role === 'admin' && (
              <button
                onClick={() => navigate('/admin/users')}
                className="btn-secondary"
              >
                ユーザー管理
              </button>
            )}
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default PortalHQ

