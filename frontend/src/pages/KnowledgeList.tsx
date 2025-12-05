import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import Layout from '../components/Layout'

interface KnowledgeItem {
  id: number
  title: string
  content: string
  business_unit_id: number | null
  business_unit_name: string | null
  category: string | null
  source: string | null
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
  const { primaryColor, businessUnitLabel } = useTenantSettings()
  const [items, setItems] = useState<KnowledgeItem[]>([])
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterBusinessUnitId, setFilterBusinessUnitId] = useState<number | ''>('')
  const [filterCategory, setFilterCategory] = useState('')
  const [filterTag, setFilterTag] = useState('')

  // カテゴリ一覧（固定リスト）
  const categories = [
    { value: '', label: 'すべて' },
    { value: 'DXレポート', label: 'DXレポート' },
    { value: 'レシピ', label: 'レシピ' },
    { value: 'menu', label: 'メニュー' },
    { value: 'マニュアル', label: 'マニュアル' },
    { value: 'お知らせ', label: 'お知らせ' },
    { value: 'FAQ', label: 'FAQ' },
  ]

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    fetchBusinessUnits()
    fetchItems()
  }, [user, searchQuery, filterBusinessUnitId, filterCategory, filterTag])

  const fetchBusinessUnits = async () => {
    try {
      const response = await api.get('/api/portal/business-units')
      const units = response.data
      // スタッフ/マネージャーの場合は、自分の事業部門 + 全社共通のみ表示
      if (user?.role === 'staff' || user?.role === 'manager') {
        const filteredUnits = units.filter(
          (bu: BusinessUnit) =>
            bu.id === user.business_unit_id || bu.code === 'head' || bu.code === 'hq'
        )
        setBusinessUnits(filteredUnits)
      } else {
        // head/admin は全部門を表示
        setBusinessUnits(units)
      }
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
      // カテゴリでフィルタ（フロントエンド側でフィルタ）
      let filteredItems = response.data
      if (filterCategory) {
        filteredItems = filteredItems.filter((item: KnowledgeItem) => item.category === filterCategory)
      }
      setItems(filteredItems)
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
    <Layout showFab onFabClick={() => navigate('/knowledge/new')} fabLabel="+">
      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
        {/* ページタイトル */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold" style={{ color: primaryColor }}>
              ナレッジベース
            </h2>
            <p className="text-sm text-gray-600 mt-1">社内情報の管理</p>
          </div>
          <div className="flex items-center gap-2">
            {user?.role && (
              <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: primaryColor, color: 'white' }}>
                {user.role === 'admin' || user.role === 'head' ? '全社閲覧可' : '自部門+共通'}
              </span>
            )}
            <button
              onClick={() => navigate('/knowledge/new')}
              className="text-sm px-4 py-2 rounded-lg text-white hover:opacity-90 transition-colors"
              style={{ backgroundColor: primaryColor }}
            >
              新規作成
            </button>
          </div>
        </div>
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
            {/* スタッフ/マネージャーの場合は事業部門フィルターを非表示（自分の部門のみ表示されるため） */}
            {(user?.role === 'head' || user?.role === 'admin') && (
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {businessUnitLabel}で絞り込み
                </label>
                <select
                  value={filterBusinessUnitId}
                  onChange={(e) => setFilterBusinessUnitId(e.target.value ? Number(e.target.value) : '')}
                  className="input-field"
                >
                  <option value="">すべて</option>
                  <option value="0">全社共通</option>
                  {businessUnits
                    .filter((bu) => bu.code !== 'head' && bu.code !== 'hq')  // 本部は除外
                    .map((bu) => (
                      <option key={bu.id} value={bu.id}>
                        {bu.name}
                      </option>
                    ))}
                </select>
              </div>
            )}
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                カテゴリで絞り込み
              </label>
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="input-field"
              >
                {categories.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
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
                      <h3 className="text-lg font-bold mb-2" style={{ color: primaryColor }}>
                        {item.title}
                      </h3>
                      <p className="text-sm text-gray-600 mb-2 line-clamp-2">
                        {item.content}
                      </p>
                      <div className="flex items-center gap-2 flex-wrap text-xs text-gray-500">
                        {item.category && (
                          <span className={`px-2 py-1 rounded-full font-medium ${
                            item.category === 'DXレポート' ? 'bg-purple-100 text-purple-800' :
                            item.category === 'レシピ' ? 'bg-orange-100 text-orange-800' :
                            item.category === 'menu' ? 'bg-amber-100 text-amber-800' :
                            item.category === 'マニュアル' ? 'bg-blue-100 text-blue-800' :
                            item.category === 'FAQ' ? 'bg-green-100 text-green-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {item.category === 'menu' ? 'メニュー' : item.category}
                          </span>
                        )}
                        {item.business_unit_name ? (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full">
                            {item.business_unit_name}
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                            全社共通
                          </span>
                        )}
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
                        className="px-3 py-1 text-sm text-white rounded hover:opacity-90 transition-colors"
                        style={{ backgroundColor: primaryColor }}
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
    </Layout>
  )
}

export default KnowledgeList

