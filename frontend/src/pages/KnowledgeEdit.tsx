import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import Layout from '../components/Layout'

interface BusinessUnit {
  id: number
  name: string
  code: string
}

const KnowledgeEdit = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { primaryColor, businessUnitLabel } = useTenantSettings()
  const { id } = useParams<{ id: string }>()
  const isNew = !id

  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const [formData, setFormData] = useState({
    title: '',
    content: '',
    business_unit_id: 0,
    category: '',
    source: '',
    tags: '' as string | string[]
  })

  // カテゴリ一覧
  const categories = [
    { value: '', label: '未設定' },
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
    if (!isNew) {
      fetchItem()
    }
  }, [user, id])

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
      
      if (units.length > 0 && formData.business_unit_id === 0) {
        // ユーザーの所属部門をデフォルトに設定
        const userUnit = units.find((bu: BusinessUnit) => bu.id === user?.business_unit_id)
        setFormData({
          ...formData,
          business_unit_id: userUnit?.id || (user?.role === 'staff' || user?.role === 'manager' ? 0 : units[0].id)  // スタッフの場合は全社共通（0）をデフォルトに
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
        category: item.category || '',
        source: item.source || '',
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
        category: formData.category || null,
        source: formData.source || null,
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
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* ページタイトル */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold" style={{ color: primaryColor }}>
            {isNew ? 'ナレッジを新規作成' : 'ナレッジを編集'}
          </h2>
          <button
            onClick={() => navigate('/knowledge')}
            className="text-sm px-4 py-2 rounded-lg border hover:bg-gray-50 transition-colors"
          >
            一覧に戻る
          </button>
        </div>
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
                placeholder="例: コーヒーの淹れ方マニュアル"
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
                {businessUnitLabel}
              </label>
              <select
                value={formData.business_unit_id}
                onChange={(e) => setFormData({ ...formData, business_unit_id: Number(e.target.value) })}
                className="input-field"
              >
                <option value="0">全社共通</option>
                {businessUnits
                  .filter((bu) => bu.code !== 'head' && bu.code !== 'hq')  // 本部は選択肢から除外（全社共通として扱う）
                  .map((bu) => (
                    <option key={bu.id} value={bu.id}>
                      {bu.name}
                    </option>
                  ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                {user?.role === 'staff' || user?.role === 'manager'
                  ? `自分の${businessUnitLabel}または全社共通を選択できます`
                  : `全社共通を選択すると、全ての${businessUnitLabel}から参照可能です`}
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  カテゴリ
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="input-field"
                >
                  {categories.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  情報の種類を選択
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  情報元
                </label>
                <input
                  type="text"
                  value={formData.source}
                  onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                  className="input-field"
                  placeholder="例: 社内資料、Claude調査"
                />
                <p className="text-xs text-gray-500 mt-1">
                  情報の出典を入力
                </p>
              </div>
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
    </Layout>
  )
}

export default KnowledgeEdit

