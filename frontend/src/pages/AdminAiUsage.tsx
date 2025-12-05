import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import Layout from '../components/Layout'

interface TierUsage {
  tier: string
  call_count: number
  tokens_input_total: number
  tokens_output_total: number
}

interface DailyUsage {
  date: string
  tier: string
  call_count: number
  tokens_input_total: number
  tokens_output_total: number
}

interface AiUsageSummary {
  period_start: string
  period_end: string
  total_calls: number
  total_tokens_input: number
  total_tokens_output: number
  by_tier: TierUsage[]
  by_day: DailyUsage[]
}

const AdminAiUsage = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { primaryColor } = useTenantSettings()
  const [summary, setSummary] = useState<AiUsageSummary | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [days, setDays] = useState(7)

  // 管理者または本部チェック
  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    if (user.role !== 'admin' && user.role !== 'head') {
      navigate('/dashboard')
      return
    }
  }, [user, navigate])

  // データ取得
  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'head') {
      fetchUsageSummary()
    }
  }, [user, days])

  const fetchUsageSummary = async () => {
    setIsLoading(true)
    setError('')
    try {
      const response = await api.get<AiUsageSummary>(`/api/admin/ai-usage/summary?days=${days}`)
      setSummary(response.data)
    } catch (err: any) {
      console.error('AI利用状況取得エラー:', err)
      setError(err.response?.data?.detail || 'AI利用状況の取得に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const getTierLabel = (tier: string) => {
    const labels: Record<string, string> = {
      basic: 'BASIC（軽量）',
      standard: 'STANDARD（標準）',
      premium: 'PREMIUM（高性能）',
    }
    return labels[tier] || tier
  }

  const getTierColor = (tier: string) => {
    const colors: Record<string, string> = {
      basic: '#22C55E',     // green
      standard: '#3B82F6',  // blue
      premium: '#8B5CF6',   // purple
    }
    return colors[tier] || '#6B7280'
  }

  const formatNumber = (num: number) => {
    return num.toLocaleString()
  }

  const formatDate = (dateStr: string) => {
    if (!dateStr) return ''
    const date = new Date(dateStr)
    return `${date.getMonth() + 1}/${date.getDate()}`
  }

  if (!user || (user.role !== 'admin' && user.role !== 'head')) {
    return null
  }

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* ページタイトル */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold" style={{ color: primaryColor }}>
              AI利用状況
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              テナント全体のAI利用統計（ベータ版）
            </p>
          </div>
          <div className="flex gap-2">
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="input-field w-auto"
            >
              <option value={7}>直近7日間</option>
              <option value={14}>直近14日間</option>
              <option value={30}>直近30日間</option>
            </select>
            {user.role === 'admin' && (
              <button
                onClick={() => navigate('/admin/users')}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm"
              >
                ユーザー管理へ
              </button>
            )}
          </div>
        </div>

        {/* エラーメッセージ */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-gray-500">読み込み中...</div>
          </div>
        ) : summary ? (
          <>
            {/* サマリーカード */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="card">
                <p className="text-sm text-gray-600 mb-1">総呼び出し回数</p>
                <p className="text-3xl font-bold" style={{ color: primaryColor }}>
                  {formatNumber(summary.total_calls)}
                </p>
                <p className="text-xs text-gray-500 mt-1">回</p>
              </div>
              <div className="card">
                <p className="text-sm text-gray-600 mb-1">入力トークン合計</p>
                <p className="text-3xl font-bold" style={{ color: primaryColor }}>
                  {formatNumber(summary.total_tokens_input)}
                </p>
                <p className="text-xs text-gray-500 mt-1">tokens</p>
              </div>
              <div className="card">
                <p className="text-sm text-gray-600 mb-1">出力トークン合計</p>
                <p className="text-3xl font-bold" style={{ color: primaryColor }}>
                  {formatNumber(summary.total_tokens_output)}
                </p>
                <p className="text-xs text-gray-500 mt-1">tokens</p>
              </div>
            </div>

            {/* ティア別利用状況 */}
            <div className="card">
              <h3 className="text-lg font-bold mb-4" style={{ color: primaryColor }}>
                ティア別利用状況
              </h3>
              {summary.by_tier.length === 0 ? (
                <p className="text-gray-500 text-center py-4">データがありません</p>
              ) : (
                <div className="space-y-4">
                  {summary.by_tier.map((tierData) => (
                    <div key={tierData.tier} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: getTierColor(tierData.tier) }}
                          />
                          <span className="font-medium">{getTierLabel(tierData.tier)}</span>
                        </div>
                        <span className="text-lg font-bold">
                          {formatNumber(tierData.call_count)} 回
                        </span>
                      </div>
                      <div className="flex gap-4 text-sm text-gray-600">
                        <span>入力: {formatNumber(tierData.tokens_input_total)} tokens</span>
                        <span>出力: {formatNumber(tierData.tokens_output_total)} tokens</span>
                      </div>
                      {/* プログレスバー */}
                      <div className="mt-2 h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: `${Math.min((tierData.call_count / summary.total_calls) * 100, 100)}%`,
                            backgroundColor: getTierColor(tierData.tier),
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 日別利用状況テーブル */}
            <div className="card overflow-x-auto">
              <h3 className="text-lg font-bold mb-4" style={{ color: primaryColor }}>
                日別利用状況
              </h3>
              {summary.by_day.length === 0 ? (
                <p className="text-gray-500 text-center py-4">データがありません</p>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-3 font-medium text-gray-700">日付</th>
                      <th className="text-left p-3 font-medium text-gray-700">ティア</th>
                      <th className="text-right p-3 font-medium text-gray-700">呼び出し回数</th>
                      <th className="text-right p-3 font-medium text-gray-700">入力トークン</th>
                      <th className="text-right p-3 font-medium text-gray-700">出力トークン</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.by_day.map((day, index) => (
                      <tr key={`${day.date}-${day.tier}-${index}`} className="border-b hover:bg-gray-50">
                        <td className="p-3">{formatDate(day.date)}</td>
                        <td className="p-3">
                          <span
                            className="px-2 py-1 rounded text-sm text-white"
                            style={{ backgroundColor: getTierColor(day.tier) }}
                          >
                            {day.tier.toUpperCase()}
                          </span>
                        </td>
                        <td className="p-3 text-right">{formatNumber(day.call_count)}</td>
                        <td className="p-3 text-right">{formatNumber(day.tokens_input_total)}</td>
                        <td className="p-3 text-right">{formatNumber(day.tokens_output_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* 注意事項 */}
            <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg text-sm">
              <p className="font-medium mb-1">コスト目安について</p>
              <p>
                表示されているトークン数は実際のAPI利用量に基づいています。
                料金計算には各AIプロバイダーの価格表をご確認ください。
              </p>
            </div>
          </>
        ) : (
          <div className="card text-center py-8 text-gray-500">
            データを取得できませんでした
          </div>
        )}
      </div>
    </Layout>
  )
}

export default AdminAiUsage
