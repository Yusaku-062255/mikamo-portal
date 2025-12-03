import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'

interface KnowledgeItem {
  id: number
  title: string
  content: string
  business_unit_id: number | null
  business_unit_name: string | null
  tags: string[] | null
  created_by: number
  created_by_name: string | null
  created_at: string
  updated_at: string
}

interface BusinessUnit {
  id: number
  name: string
  code: string
}

const KnowledgeList = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const [items, setItems] = useState<KnowledgeItem[]>([])
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterBusinessUnitId, setFilterBusinessUnitId] = useState<number | ''>('')
  const [filterTag, setFilterTag] = useState('')

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    fetchBusinessUnits()
    fetchItems()
  }, [user, searchQuery, filterBusinessUnitId, filterTag])

  const fetchBusinessUnits = async () => {
    try {
      const response = await api.get('/api/portal/business-units')
      setBusinessUnits(response.data)
    } catch (error) {
      console.error('事業部門取得エラー:', error)
    }
  }

  const fetchItems = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (searchQuery) {
        params.append('q', searchQuery)
      }
      if (filterBusinessUnitId) {
        params.append('business_unit_id', filterBusinessUnitId.toString())
      }
      if (filterTag) {
        params.append('tag', filterTag)
      }

      const url = `/api/knowledge${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      setItems(response.data)
    } catch (error: any) {
      console.error('ナレッジ取得エラー:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('このナレッジを削除してもよろしいですか？')) {
      return
    }

    try {
      await api.delete(`/api/knowledge/${id}`)
      fetchItems()
    } catch (error: any) {
      alert(error.response?.data?.detail || '削除に失敗しました')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* ヘッダー */}
      <header className="bg-mikamo-blue text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">ナレッジベース</h1>
            <p className="text-sm opacity-90 mt-1">社内情報の管理</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => navigate('/knowledge/new')}
              className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
            >
              新規作成
            </button>
            <button
              onClick={() => navigate('/dashboard')}
              className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
            >
              ダッシュボードに戻る
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* 検索・フィルター */}
        <div className="card">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                検索
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-field"
                placeholder="タイトル・本文から検索"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                事業部門で絞り込み
              </label>
              <select
                value={filterBusinessUnitId}
                onChange={(e) => setFilterBusinessUnitId(e.target.value ? Number(e.target.value) : '')}
                className="input-field"
              >
                <option value="">すべて</option>
                {businessUnits.map((bu) => (
                  <option key={bu.id} value={bu.id}>
                    {bu.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                タグで絞り込み
              </label>
              <input
                type="text"
                value={filterTag}
                onChange={(e) => setFilterTag(e.target.value)}
                className="input-field"
                placeholder="タグ名を入力"
              />
            </div>
          </div>
        </div>

        {/* ナレッジ一覧 */}
        <div className="card">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">読み込み中...</div>
            </div>
          ) : items.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              ナレッジが見つかりません
            </div>
          ) : (
            <div className="space-y-4">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-mikamo-blue mb-2">
                        {item.title}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {item.content}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>
                          {item.business_unit_name || '全社共通'}
                        </span>
                        {item.tags && item.tags.length > 0 && (
                          <span>
                            タグ: {item.tags.join(', ')}
                          </span>
                        )}
                        <span>
                          作成: {new Date(item.created_at).toLocaleDateString('ja-JP')}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2 ml-4">
                      <button
                        onClick={() => navigate(`/knowledge/${item.id}`)}
                        className="px-3 py-1 text-sm bg-mikamo-blue text-white rounded hover:bg-blue-700 transition-colors"
                      >
                        編集
                      </button>
                      {(user?.role === 'admin' || user?.role === 'head') && (
                        <button
                          onClick={() => handleDelete(item.id)}
                          className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                        >
                          削除
                        </button>
                      )}
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

export default KnowledgeList

