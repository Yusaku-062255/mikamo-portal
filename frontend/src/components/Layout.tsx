/**
 * 共通レイアウトコンポーネント
 *
 * SaaS対応: テナント設定に基づいてブランディングを動的に変更
 * - ヘッダー（テナントロゴ、ユーザー情報、ナビゲーション）
 * - サイドバー（将来的に追加可能）
 * - フッター（テナント設定のfooter_text）
 */
import { ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'

interface LayoutProps {
  children: ReactNode
  /** ヘッダーを表示するか（デフォルト: true） */
  showHeader?: boolean
  /** フッターを表示するか（デフォルト: false） */
  showFooter?: boolean
  /** フローティングアクションボタンを表示するか */
  showFab?: boolean
  /** FABクリック時のアクション */
  onFabClick?: () => void
  /** FABのラベル */
  fabLabel?: string
}

const Layout = ({
  children,
  showHeader = true,
  showFooter = false,
  showFab = false,
  onFabClick,
  fabLabel = '+'
}: LayoutProps) => {
  const navigate = useNavigate()
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const { displayName, primaryColor, settings, publicSettings } = useTenantSettings()

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'おはようございます'
    if (hour < 18) return 'こんにちは'
    return 'こんばんは'
  }

  const getRoleLabel = (role: string) => {
    const roleMap: Record<string, string> = {
      staff: 'スタッフ',
      manager: 'マネージャー',
      head: '本部',
      admin: '管理者'
    }
    return roleMap[role] || role
  }

  // 現在のパスに基づいてアクティブなナビアイテムを判定
  const isActive = (path: string) => location.pathname === path

  // ナビゲーションアイテム
  const navItems = [
    { path: '/dashboard', label: 'ホーム', icon: '🏠' },
    { path: '/daily-log', label: '振り返り', icon: '📝' },
    { path: '/ai', label: 'AI相談', icon: '🤖' },
    { path: '/knowledge', label: 'ナレッジ', icon: '📚' }
  ]

  // 管理者のみのナビアイテム
  if (user?.role === 'admin') {
    navItems.push({ path: '/admin/users', label: 'ユーザー管理', icon: '👥' })
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* ヘッダー */}
      {showHeader && (
        <header
          className="text-white p-4 shadow-md"
          style={{ backgroundColor: primaryColor }}
        >
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-xl font-bold">
                  {getGreeting()}、{user?.full_name}さん
                </h1>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-sm opacity-90">
                    {format(new Date(), 'yyyy年M月d日(E)', { locale: ja })}
                  </p>
                  {user?.department_name && (
                    <>
                      <span className="text-sm opacity-70">|</span>
                      <p className="text-sm opacity-90">{user.department_name}</p>
                    </>
                  )}
                  {user?.role && (
                    <>
                      <span className="text-sm opacity-70">|</span>
                      <p className="text-sm opacity-90">{getRoleLabel(user.role)}</p>
                    </>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={logout}
                  className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
                >
                  ログアウト
                </button>
              </div>
            </div>
          </div>
        </header>
      )}

      {/* ボトムナビゲーション（モバイル向け） */}
      {showHeader && (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 md:hidden">
          <div className="flex justify-around py-2">
            {navItems.slice(0, 4).map((item) => (
              <button
                key={item.path}
                onClick={() => navigate(item.path)}
                className={`flex flex-col items-center px-3 py-1 ${
                  isActive(item.path)
                    ? 'text-blue-600'
                    : 'text-gray-600 hover:text-blue-500'
                }`}
              >
                <span className="text-xl">{item.icon}</span>
                <span className="text-xs mt-1">{item.label}</span>
              </button>
            ))}
          </div>
        </nav>
      )}

      {/* メインコンテンツ */}
      <main className={`flex-1 ${showHeader ? 'pb-20 md:pb-6' : ''}`}>{children}</main>

      {/* フッター */}
      {showFooter && (
        <footer className="bg-gray-100 border-t border-gray-200 py-4 text-center text-sm text-gray-600">
          {settings?.footer_text || publicSettings?.footer_text || `© ${displayName}`}
        </footer>
      )}

      {/* フローティングアクションボタン */}
      {showFab && onFabClick && (
        <div className="fixed bottom-20 right-6 md:bottom-6">
          <button
            onClick={onFabClick}
            className="w-14 h-14 rounded-full shadow-lg flex items-center justify-center text-2xl text-white hover:opacity-90 transition-opacity"
            style={{ backgroundColor: primaryColor }}
            aria-label={fabLabel}
          >
            {fabLabel}
          </button>
        </div>
      )}
    </div>
  )
}

export default Layout
