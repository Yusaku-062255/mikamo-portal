import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import Layout from '../components/Layout'

interface Insight {
  id: number
  title: string
  content: string
  type: string
  score: number
  business_unit_id: number | null
  business_unit_name: string | null
  created_by_name: string | null
  created_at: string
  updated_at: string
}

const InsightsList = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { primaryColor } = useTenantSettings()
  const [insights, setInsights] = useState<Insight[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterType, setFilterType] = useState<string>('')
  const [minScore, setMinScore] = useState<number>(60)

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    if (user.role === 'head' || user.role === 'admin') {
      fetchInsights()
    } else {
      navigate('/dashboard')
    }
  }, [user, filterType, minScore])

  const fetchInsights = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterType) {
        params.append('type', filterType)
      }
      if (minScore) {
        params.append('min_score', minScore.toString())
      }

      const url = `/api/insights${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      setInsights(response.data)
    } catch (error) {
      console.error('Insight取得エラー:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'risk':
        return 'bg-red-100 text-red-800'
      case 'opportunity':
        return 'bg-green-100 text-green-800'
      case 'improvement':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'risk':
        return 'リスク'
      case 'opportunity':
        return '機会'
      case 'improvement':
        return '改善提案'
      default:
        return type
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-600 font-bold'
    if (score >= 60) return 'text-orange-600 font-semibold'
    return 'text-gray-600'
  }

  if (!user || (user.role !== 'head' && user.role !== 'admin')) {
    return null
  }

  return (
    <Layout>
      {/* カスタムヘッダー */}
      <div
        className="text-white p-4 shadow-md -mx-4 -mt-4 mb-6"
        style={{ backgroundColor: primaryColor }}
      >
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div>
            <h1 className="text-xl font-bold">AI分析・提案（Insight）</h1>
            <p className="text-sm opacity-90 mt-1">現場の声から抽出された重要な気付き</p>
          </div>
          <button
            onClick={() => navigate('/portal/hq')}
            className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
          >
            本部ビューに戻る
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto space-y-6">
        {/* フィルター */}
        <div className="card">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                タイプ
              </label>
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="input-field"
              >
                <option value="">すべて</option>
                <option value="risk">リスク</option>
                <option value="opportunity">機会</option>
                <option value="improvement">改善提案</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                最小スコア
              </label>
              <input
                type="number"
                value={minScore}
                onChange={(e) => setMinScore(Number(e.target.value))}
                className="input-field"
                min="0"
                max="100"
              />
            </div>
          </div>
        </div>

        {/* Insight一覧 */}
        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">読み込み中...</div>
            </div>
          ) : insights.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              Insightが見つかりません
            </div>
          ) : (
            <div className="space-y-4">
              {insights.map((insight) => (
                <div
                  key={insight.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-bold" style={{ color: primaryColor }}>
                          {insight.title}
                        </h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${getTypeColor(insight.type)}`}>
                          {getTypeLabel(insight.type)}
                        </span>
                        <span className={`text-sm ${getScoreColor(insight.score)}`}>
                          重要度: {insight.score}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2 whitespace-pre-wrap">
                        {insight.content}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        {insight.business_unit_name ? (
                          <span>{insight.business_unit_name}</span>
                        ) : (
                          <span>全社共通</span>
                        )}
                        {insight.created_by_name && (
                          <span>作成: {insight.created_by_name}</span>
                        )}
                        <span>
                          {new Date(insight.created_at).toLocaleDateString('ja-JP')}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}

export default InsightsList

