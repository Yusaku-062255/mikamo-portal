import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'

interface Issue {
  id: number
  title: string
  description: string
  status: string
  topic: string
  business_unit_id: number | null
  business_unit_name: string | null
  created_by_name: string | null
  conversation_id: number | null
  created_at: string
  updated_at: string
}

const IssuesList = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { businessUnitCode } = useParams<{ businessUnitCode?: string }>()
  const [issues, setIssues] = useState<Issue[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filterStatus, setFilterStatus] = useState<string>('')
  const [filterTopic, setFilterTopic] = useState<string>('')

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    fetchIssues()
  }, [user, filterStatus, filterTopic, businessUnitCode])

  const fetchIssues = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterStatus) {
        params.append('status', filterStatus)
      }
      if (filterTopic) {
        params.append('topic', filterTopic)
      }
      if (businessUnitCode) {
        // businessUnitCodeからbusiness_unit_idを取得する必要がある
        // 一旦、全件取得してフィルタリング
      }

      const url = `/api/issues${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      setIssues(response.data)
    } catch (error) {
      console.error('Issue取得エラー:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-blue-100 text-blue-800'
      case 'in_progress':
        return 'bg-yellow-100 text-yellow-800'
      case 'resolved':
        return 'bg-green-100 text-green-800'
      case 'archived':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'open':
        return '未対応'
      case 'in_progress':
        return '対応中'
      case 'resolved':
        return '解決済み'
      case 'archived':
        return 'アーカイブ'
      default:
        return status
    }
  }

  const getTopicLabel = (topic: string) => {
    const topicMap: Record<string, string> = {
      menu: 'メニュー・レシピ',
      operation: 'オペレーション',
      customer_complaint: 'クレーム',
      future_risk: '将来リスク',
      sales_opportunity: '売上機会',
      staffing: '人員・採用',
      other: 'その他'
    }
    return topicMap[topic] || topic
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* ヘッダー */}
      <header className="bg-mikamo-blue text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">課題・困りごと一覧</h1>
            <p className="text-sm opacity-90 mt-1">
              {businessUnitCode ? `${businessUnitCode}の課題` : '全課題'}
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
        {/* フィルター */}
        <div className="card">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ステータス
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="input-field"
              >
                <option value="">すべて</option>
                <option value="open">未対応</option>
                <option value="in_progress">対応中</option>
                <option value="resolved">解決済み</option>
                <option value="archived">アーカイブ</option>
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                トピック
              </label>
              <select
                value={filterTopic}
                onChange={(e) => setFilterTopic(e.target.value)}
                className="input-field"
              >
                <option value="">すべて</option>
                <option value="menu">メニュー・レシピ</option>
                <option value="operation">オペレーション</option>
                <option value="customer_complaint">クレーム</option>
                <option value="future_risk">将来リスク</option>
                <option value="sales_opportunity">売上機会</option>
                <option value="staffing">人員・採用</option>
                <option value="other">その他</option>
              </select>
            </div>
          </div>
        </div>

        {/* Issue一覧 */}
        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">読み込み中...</div>
            </div>
          ) : issues.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              課題が見つかりません
            </div>
          ) : (
            <div className="space-y-4">
              {issues.map((issue) => (
                <div
                  key={issue.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="text-lg font-bold text-mikamo-blue">
                          {issue.title}
                        </h3>
                        <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(issue.status)}`}>
                          {getStatusLabel(issue.status)}
                        </span>
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                          {getTopicLabel(issue.topic)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {issue.description}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        {issue.business_unit_name && (
                          <span>{issue.business_unit_name}</span>
                        )}
                        {issue.created_by_name && (
                          <span>作成: {issue.created_by_name}</span>
                        )}
                        <span>
                          {new Date(issue.created_at).toLocaleDateString('ja-JP')}
                        </span>
                        {issue.conversation_id && (
                          <button
                            onClick={() => navigate(`/ai?conversation=${issue.conversation_id}`)}
                            className="text-mikamo-blue hover:underline"
                          >
                            関連会話を見る
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default IssuesList

