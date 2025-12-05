import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantStore, useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import Layout from '../components/Layout'

interface TenantSettingsForm {
  logo_url: string
  primary_color: string
  secondary_color: string
  business_unit_label: string
  welcome_message: string
  footer_text: string
  ai_company_context: string
  ai_tier_policy: string
  ai_max_tokens_override: number | null
  feature_ai_enabled: boolean
  feature_knowledge_enabled: boolean
  feature_insights_enabled: boolean
  feature_daily_log_enabled: boolean
}

const AdminTenantSettings = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { primaryColor, settings } = useTenantSettings()
  const fetchSettings = useTenantStore((state) => state.fetchSettings)

  const [formData, setFormData] = useState<TenantSettingsForm>({
    logo_url: '',
    primary_color: '#3B82F6',
    secondary_color: '#1E40AF',
    business_unit_label: '事業部門',
    welcome_message: '',
    footer_text: '',
    ai_company_context: '',
    ai_tier_policy: 'all',
    ai_max_tokens_override: null,
    feature_ai_enabled: true,
    feature_knowledge_enabled: true,
    feature_insights_enabled: true,
    feature_daily_log_enabled: true,
  })

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')
  const [error, setError] = useState('')
  const [previewColor, setPreviewColor] = useState('#3B82F6')

  // 管理者チェック
  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    if (user.role !== 'admin') {
      navigate('/dashboard')
      return
    }
  }, [user, navigate])

  // 設定を読み込む
  useEffect(() => {
    if (settings) {
      setFormData({
        logo_url: settings.logo_url || '',
        primary_color: settings.primary_color,
        secondary_color: settings.secondary_color,
        business_unit_label: settings.business_unit_label,
        welcome_message: settings.welcome_message || '',
        footer_text: settings.footer_text || '',
        ai_company_context: settings.ai_company_context,
        ai_tier_policy: settings.ai_tier_policy || 'all',
        ai_max_tokens_override: settings.ai_max_tokens_override || null,
        feature_ai_enabled: settings.feature_ai_enabled,
        feature_knowledge_enabled: settings.feature_knowledge_enabled,
        feature_insights_enabled: settings.feature_insights_enabled,
        feature_daily_log_enabled: settings.feature_daily_log_enabled,
      })
      setPreviewColor(settings.primary_color)
      setIsLoading(false)
    }
  }, [settings])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    setIsSaving(true)

    try {
      await api.patch('/api/tenant/settings', {
        logo_url: formData.logo_url || null,
        primary_color: formData.primary_color,
        secondary_color: formData.secondary_color,
        business_unit_label: formData.business_unit_label,
        welcome_message: formData.welcome_message || null,
        footer_text: formData.footer_text || null,
        ai_company_context: formData.ai_company_context,
        ai_tier_policy: formData.ai_tier_policy,
        ai_max_tokens_override: formData.ai_max_tokens_override || null,
        feature_ai_enabled: formData.feature_ai_enabled,
        feature_knowledge_enabled: formData.feature_knowledge_enabled,
        feature_insights_enabled: formData.feature_insights_enabled,
        feature_daily_log_enabled: formData.feature_daily_log_enabled,
      })

      // ストアを更新
      await fetchSettings()

      // CSS変数も更新
      document.documentElement.style.setProperty('--color-primary', formData.primary_color)

      setSuccessMessage('設定を保存しました')
      setTimeout(() => setSuccessMessage(''), 3000)
    } catch (err: any) {
      setError(err.response?.data?.detail || '設定の保存に失敗しました')
    } finally {
      setIsSaving(false)
    }
  }

  const handleColorChange = (color: string) => {
    setFormData({ ...formData, primary_color: color })
    setPreviewColor(color)
  }

  // プリセットカラー
  const presetColors = [
    { name: 'ブルー', value: '#3B82F6' },
    { name: 'インディゴ', value: '#6366F1' },
    { name: 'パープル', value: '#8B5CF6' },
    { name: 'ピンク', value: '#EC4899' },
    { name: 'レッド', value: '#EF4444' },
    { name: 'オレンジ', value: '#F97316' },
    { name: 'グリーン', value: '#22C55E' },
    { name: 'ティール', value: '#14B8A6' },
    { name: 'グレー', value: '#6B7280' },
  ]

  if (!user || user.role !== 'admin') {
    return null
  }

  return (
    <Layout>
      <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* ページタイトル */}
        <div>
          <h2 className="text-2xl font-bold" style={{ color: primaryColor }}>
            テナント設定
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            ポータルのブランド設定と機能フラグを管理
          </p>
        </div>

        {/* 成功メッセージ */}
        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg">
            {successMessage}
          </div>
        )}

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
        ) : (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* ブランド設定 */}
            <div className="card">
              <h3 className="text-lg font-bold mb-4" style={{ color: primaryColor }}>
                ブランド設定
              </h3>

              {/* プライマリカラー */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  プライマリカラー
                </label>
                <div className="flex items-center gap-4 mb-3">
                  <input
                    type="color"
                    value={formData.primary_color}
                    onChange={(e) => handleColorChange(e.target.value)}
                    className="w-16 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={formData.primary_color}
                    onChange={(e) => handleColorChange(e.target.value)}
                    className="input-field w-32"
                    placeholder="#3B82F6"
                  />
                  <div
                    className="px-4 py-2 rounded-lg text-white font-medium"
                    style={{ backgroundColor: previewColor }}
                  >
                    プレビュー
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {presetColors.map((color) => (
                    <button
                      key={color.value}
                      type="button"
                      onClick={() => handleColorChange(color.value)}
                      className="w-8 h-8 rounded-full border-2 transition-transform hover:scale-110"
                      style={{
                        backgroundColor: color.value,
                        borderColor: formData.primary_color === color.value ? '#000' : 'transparent'
                      }}
                      title={color.name}
                    />
                  ))}
                </div>
              </div>

              {/* ロゴURL */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ロゴURL（オプション）
                </label>
                <input
                  type="url"
                  value={formData.logo_url}
                  onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                  className="input-field"
                  placeholder="https://example.com/logo.png"
                />
              </div>

              {/* 事業部門ラベル */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  事業部門の表示名
                </label>
                <input
                  type="text"
                  value={formData.business_unit_label}
                  onChange={(e) => setFormData({ ...formData, business_unit_label: e.target.value })}
                  className="input-field"
                  placeholder="事業部門"
                />
                <p className="text-xs text-gray-500 mt-1">
                  「店舗」「部署」「チーム」など、組織に合わせて変更できます
                </p>
              </div>

              {/* ウェルカムメッセージ */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ウェルカムメッセージ
                </label>
                <input
                  type="text"
                  value={formData.welcome_message}
                  onChange={(e) => setFormData({ ...formData, welcome_message: e.target.value })}
                  className="input-field"
                  placeholder="ようこそ、○○ポータルへ"
                />
              </div>

              {/* フッターテキスト */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  フッターテキスト
                </label>
                <input
                  type="text"
                  value={formData.footer_text}
                  onChange={(e) => setFormData({ ...formData, footer_text: e.target.value })}
                  className="input-field"
                  placeholder="© 会社名"
                />
              </div>
            </div>

            {/* AI設定 */}
            <div className="card">
              <h3 className="text-lg font-bold mb-4" style={{ color: primaryColor }}>
                AI設定
              </h3>

              {/* AIティアポリシー */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AIモデルプラン
                </label>
                <select
                  value={formData.ai_tier_policy}
                  onChange={(e) => setFormData({ ...formData, ai_tier_policy: e.target.value })}
                  className="input-field"
                >
                  <option value="all">プレミアムプラン（全ティア利用可能）</option>
                  <option value="standard_max">スタンダードプラン（STANDARD以下）</option>
                  <option value="basic_only">ライトプラン（BASICのみ）</option>
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  利用可能なAIモデルの性能レベルを設定します。コスト最適化のために制限できます。
                </p>
                <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-3 rounded">
                  <p className="font-medium mb-1">ティア説明：</p>
                  <ul className="list-disc ml-4 space-y-1">
                    <li><strong>BASIC</strong>: 高速・低コスト（シフト管理、ログ要約など軽量タスク向け）</li>
                    <li><strong>STANDARD</strong>: バランス型（従業員Q&A、ナレッジ検索など）</li>
                    <li><strong>PREMIUM</strong>: 高性能・高精度（経営判断、DXレポート分析など）</li>
                  </ul>
                </div>
              </div>

              {/* 最大トークン数オーバーライド */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  最大トークン数（オプション）
                </label>
                <input
                  type="number"
                  value={formData.ai_max_tokens_override || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    ai_max_tokens_override: e.target.value ? parseInt(e.target.value) : null
                  })}
                  className="input-field"
                  placeholder="未設定（デフォルト値を使用）"
                  min="100"
                  max="4000"
                />
                <p className="text-xs text-gray-500 mt-1">
                  AIの応答長を制限します。空欄の場合はデフォルト値が使用されます。
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  AIコンテキスト（システムプロンプト）
                </label>
                <textarea
                  value={formData.ai_company_context}
                  onChange={(e) => setFormData({ ...formData, ai_company_context: e.target.value })}
                  className="input-field min-h-[200px]"
                  placeholder="AIアシスタントに対する指示や会社の背景情報を記載..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  AIが回答を生成する際の背景情報として使用されます
                </p>
              </div>
            </div>

            {/* 機能フラグ */}
            <div className="card">
              <h3 className="text-lg font-bold mb-4" style={{ color: primaryColor }}>
                機能フラグ
              </h3>

              <div className="space-y-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.feature_ai_enabled}
                    onChange={(e) => setFormData({ ...formData, feature_ai_enabled: e.target.checked })}
                    className="w-5 h-5 rounded"
                  />
                  <div>
                    <span className="font-medium">AI相談機能</span>
                    <p className="text-sm text-gray-500">AIアシスタントとのチャット機能</p>
                  </div>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.feature_knowledge_enabled}
                    onChange={(e) => setFormData({ ...formData, feature_knowledge_enabled: e.target.checked })}
                    className="w-5 h-5 rounded"
                  />
                  <div>
                    <span className="font-medium">ナレッジベース</span>
                    <p className="text-sm text-gray-500">社内ナレッジの管理・検索機能</p>
                  </div>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.feature_insights_enabled}
                    onChange={(e) => setFormData({ ...formData, feature_insights_enabled: e.target.checked })}
                    className="w-5 h-5 rounded"
                  />
                  <div>
                    <span className="font-medium">Insight機能</span>
                    <p className="text-sm text-gray-500">AI分析による気付き・提案</p>
                  </div>
                </label>

                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.feature_daily_log_enabled}
                    onChange={(e) => setFormData({ ...formData, feature_daily_log_enabled: e.target.checked })}
                    className="w-5 h-5 rounded"
                  />
                  <div>
                    <span className="font-medium">日次ログ機能</span>
                    <p className="text-sm text-gray-500">毎日の振り返り記録</p>
                  </div>
                </label>
              </div>
            </div>

            {/* 保存ボタン */}
            <div className="flex gap-4">
              <button
                type="button"
                onClick={() => navigate('/admin/users')}
                className="btn-secondary flex-1"
              >
                キャンセル
              </button>
              <button
                type="submit"
                disabled={isSaving}
                className="btn-primary flex-1"
              >
                {isSaving ? '保存中...' : '設定を保存'}
              </button>
            </div>
          </form>
        )}
      </div>
    </Layout>
  )
}

export default AdminTenantSettings
