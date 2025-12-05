/**
 * テナント設定ストア
 *
 * テナントごとのブランド設定、AIポリシー、機能フラグを管理。
 * SaaS展開時に各テナントが独自の設定を持てるようにする。
 */
import { create } from 'zustand'
import api from '../utils/api'

// ========================================
// 型定義
// ========================================

/** AIティアポリシー */
export type AiTierPolicy = 'all' | 'standard_max' | 'basic_only'

/** 公開用テナント設定（未認証でも取得可能） */
export interface TenantSettingsPublic {
  tenant_name: string
  display_name: string
  logo_url: string | null
  primary_color: string
  secondary_color: string
  business_unit_label: string
  welcome_message: string | null
  footer_text: string | null
}

/** 完全なテナント設定（認証済みユーザー向け） */
export interface TenantSettingsFull extends TenantSettingsPublic {
  // AI設定
  ai_tier_policy: AiTierPolicy
  ai_company_context: string
  ai_max_tokens_override: number | null

  // 機能フラグ
  feature_ai_enabled: boolean
  feature_knowledge_enabled: boolean
  feature_insights_enabled: boolean
  feature_daily_log_enabled: boolean
}

// ========================================
// ストア
// ========================================

interface TenantState {
  /** 公開設定（ログイン画面用） */
  publicSettings: TenantSettingsPublic | null
  /** 完全設定（認証後） */
  settings: TenantSettingsFull | null
  /** ローディング状態 */
  isLoading: boolean
  /** エラー状態 */
  error: string | null

  /** 公開設定を取得（未認証可） */
  fetchPublicSettings: (tenantName?: string) => Promise<void>
  /** 完全設定を取得（認証必須） */
  fetchSettings: () => Promise<void>
  /** 設定をクリア（ログアウト時） */
  clearSettings: () => void
}

export const useTenantStore = create<TenantState>((set) => ({
  publicSettings: null,
  settings: null,
  isLoading: false,
  error: null,

  fetchPublicSettings: async (tenantName = 'mikamo') => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.get<TenantSettingsPublic>(
        `/api/tenant/settings/public?tenant_name=${tenantName}`
      )
      set({
        publicSettings: response.data,
        isLoading: false,
      })
    } catch (error) {
      console.error('Failed to fetch public tenant settings:', error)
      set({
        isLoading: false,
        error: 'テナント設定の取得に失敗しました',
        // フォールバック: デフォルト値を設定
        publicSettings: {
          tenant_name: tenantName,
          display_name: 'DXポータル',
          logo_url: null,
          primary_color: '#3B82F6',
          secondary_color: '#1E40AF',
          business_unit_label: '事業部門',
          welcome_message: null,
          footer_text: null,
        },
      })
    }
  },

  fetchSettings: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.get<TenantSettingsFull>('/api/tenant/settings')
      set({
        settings: response.data,
        publicSettings: response.data, // 公開設定も更新
        isLoading: false,
      })
    } catch (error) {
      console.error('Failed to fetch tenant settings:', error)
      set({
        isLoading: false,
        error: 'テナント設定の取得に失敗しました',
      })
    }
  },

  clearSettings: () => {
    set({
      settings: null,
      // publicSettingsは残す（ログイン画面で使う）
      error: null,
    })
  },
}))

// ========================================
// ユーティリティフック
// ========================================

/**
 * テナント設定を取得するカスタムフック
 *
 * 使用例:
 * ```tsx
 * const { settings, isLoading } = useTenantSettings()
 * if (settings?.feature_ai_enabled) {
 *   // AI機能を表示
 * }
 * ```
 */
export const useTenantSettings = () => {
  const settings = useTenantStore((state) => state.settings)
  const publicSettings = useTenantStore((state) => state.publicSettings)
  const isLoading = useTenantStore((state) => state.isLoading)
  const error = useTenantStore((state) => state.error)

  return {
    settings,
    publicSettings,
    isLoading,
    error,
    // よく使うプロパティへのショートカット
    displayName: settings?.display_name ?? publicSettings?.display_name ?? 'DXポータル',
    primaryColor: settings?.primary_color ?? publicSettings?.primary_color ?? '#3B82F6',
    businessUnitLabel: settings?.business_unit_label ?? publicSettings?.business_unit_label ?? '事業部門',
    // 機能フラグ（デフォルトは有効）
    isAiEnabled: settings?.feature_ai_enabled ?? true,
    isKnowledgeEnabled: settings?.feature_knowledge_enabled ?? true,
    isInsightsEnabled: settings?.feature_insights_enabled ?? true,
    isDailyLogEnabled: settings?.feature_daily_log_enabled ?? true,
  }
}
