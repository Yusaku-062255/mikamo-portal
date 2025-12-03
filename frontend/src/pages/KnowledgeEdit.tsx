import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'

interface BusinessUnit {
  id: number
  name: string
  code: string
}

const KnowledgeEdit = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { id } = useParams<{ id: string }>()
  const isNew = !id

  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const [formData, setFormData] = useState({
    title: '',
    content: '',
    business_unit_id: 0,
    tags: '' as string | string[]
  })

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    fetchBusinessUnits()
    if (!isNew) {
      fetchItem()
    }
  }, [user, id])

  const fetchBusinessUnits = async () => {
    try {
      const response = await api.get('/api/portal/business-units')
      setBusinessUnits(response.data)
      if (response.data.length > 0 && formData.business_unit_id === 0) {
        // ユーザーの所属部門をデフォルトに設定
        const userUnit = response.data.find((bu: BusinessUnit) => bu.id === user?.business_unit_id)
        setFormData({
          ...formData,
          business_unit_id: userUnit?.id || response.data[0].id
        })
      }
    } catch (error) {
      console.error('事業部門取得エラー:', error)
    }
  }

  const fetchItem = async () => {
    if (!id) return

    setIsLoading(true)
    try {
      const response = await api.get(`/api/knowledge/${id}`)
      const item = response.data
      setFormData({
        title: item.title,
        content: item.content,
        business_unit_id: item.business_unit_id || 0,
        tags: item.tags ? item.tags.join(', ') : ''
      })
    } catch (error: any) {
      setError(error.response?.data?.detail || 'ナレッジの取得に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const tagsArray = formData.tags
        ? (typeof formData.tags === 'string' ? formData.tags.split(',').map(t => t.trim()).filter(t => t) : formData.tags)
        : []

      const payload = {
        title: formData.title,
        content: formData.content,
        business_unit_id: formData.business_unit_id || null,
        tags: tagsArray
      }

      if (isNew) {
        await api.post('/api/knowledge', payload)
      } else {
        await api.put(`/api/knowledge/${id}`, payload)
      }

      navigate('/knowledge')
    } catch (error: any) {
      setError(error.response?.data?.detail || '保存に失敗しました')
    } finally {
      setIsLoading(false)
    }
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
            <h1 className="text-xl font-bold">
              {isNew ? 'ナレッジを新規作成' : 'ナレッジを編集'}
            </h1>
          </div>
          <button
            onClick={() => navigate('/knowledge')}
            className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
          >
            一覧に戻る
          </button>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="card">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                タイトル <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="input-field"
                placeholder="例: ミカモ喫茶のレシピ - コーヒーの淹れ方"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                内容 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                className="input-field min-h-[300px]"
                placeholder="Markdown形式で記述できます&#10;&#10;例:&#10;# コーヒーの淹れ方&#10;&#10;1. お湯の温度は90度に設定&#10;2. 豆は20g使用&#10;..."
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Markdown形式で記述できます
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                事業部門
              </label>
              <select
                value={formData.business_unit_id}
                onChange={(e) => setFormData({ ...formData, business_unit_id: Number(e.target.value) })}
                className="input-field"
              >
                <option value="0">全社共通</option>
                {businessUnits.map((bu) => (
                  <option key={bu.id} value={bu.id}>
                    {bu.name}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                特定の事業部門の情報の場合は選択してください。全社共通の場合は「全社共通」を選択
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                タグ（カンマ区切り）
              </label>
              <input
                type="text"
                value={typeof formData.tags === 'string' ? formData.tags : formData.tags.join(', ')}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                className="input-field"
                placeholder="例: レシピ, オペレーション, マニュアル"
              />
              <p className="text-xs text-gray-500 mt-1">
                カンマ区切りで複数のタグを設定できます
              </p>
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => navigate('/knowledge')}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                disabled={isLoading}
              >
                キャンセル
              </button>
              <button
                type="submit"
                className="flex-1 btn-primary"
                disabled={isLoading}
              >
                {isLoading ? '保存中...' : isNew ? '作成' : '更新'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}

export default KnowledgeEdit

