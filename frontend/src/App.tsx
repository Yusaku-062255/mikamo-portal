import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { useTenantStore, useTenantSettings } from './stores/tenantStore'
import { ErrorBoundary } from './components/ErrorBoundary'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DailyLog from './pages/DailyLog'
import AIChat from './pages/AIChat'
import AdminUsers from './pages/AdminUsers'
import AdminTenantSettings from './pages/AdminTenantSettings'
import AdminAiUsage from './pages/AdminAiUsage'
import PortalHQ from './pages/PortalHQ'
import PortalGasStation from './pages/PortalGasStation'
import PortalCarCoating from './pages/PortalCarCoating'
import PortalUsedCar from './pages/PortalUsedCar'
import PortalCafe from './pages/PortalCafe'
import KnowledgeList from './pages/KnowledgeList'
import KnowledgeEdit from './pages/KnowledgeEdit'
import IssuesList from './pages/IssuesList'
import InsightsList from './pages/InsightsList'
import PrivateRoute from './components/PrivateRoute'

function App() {
  const fetchUser = useAuthStore((state) => state.fetchUser)
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const fetchPublicSettings = useTenantStore((state) => state.fetchPublicSettings)
  const fetchSettings = useTenantStore((state) => state.fetchSettings)
  const { primaryColor } = useTenantSettings()

  useEffect(() => {
    // アプリ起動時に公開テナント設定を取得（ログイン画面用）
    fetchPublicSettings()
    // ユーザー情報を取得
    fetchUser()
  }, [fetchUser, fetchPublicSettings])

  useEffect(() => {
    // 認証成功後に完全なテナント設定を取得
    if (isAuthenticated) {
      fetchSettings()
    }
  }, [isAuthenticated, fetchSettings])

  // CSS変数を設定（Tailwind CSS用）
  useEffect(() => {
    document.documentElement.style.setProperty('--color-primary', primaryColor)
  }, [primaryColor])

  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Dashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/daily-log"
            element={
              <PrivateRoute>
                <DailyLog />
              </PrivateRoute>
            }
          />
          <Route
            path="/ai"
            element={
              <PrivateRoute>
                <AIChat />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <PrivateRoute>
                <AdminUsers />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/settings"
            element={
              <PrivateRoute>
                <AdminTenantSettings />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/ai-usage"
            element={
              <PrivateRoute>
                <AdminAiUsage />
              </PrivateRoute>
            }
          />
          <Route
            path="/portal/hq"
            element={
              <PrivateRoute>
                <PortalHQ />
              </PrivateRoute>
            }
          />
          <Route
            path="/portal/gas-station"
            element={
              <PrivateRoute>
                <PortalGasStation />
              </PrivateRoute>
            }
          />
          <Route
            path="/portal/car-coating"
            element={
              <PrivateRoute>
                <PortalCarCoating />
              </PrivateRoute>
            }
          />
          <Route
            path="/portal/used-car"
            element={
              <PrivateRoute>
                <PortalUsedCar />
              </PrivateRoute>
            }
          />
          <Route
            path="/portal/cafe"
            element={
              <PrivateRoute>
                <PortalCafe />
              </PrivateRoute>
            }
          />
          <Route
            path="/knowledge"
            element={
              <PrivateRoute>
                <KnowledgeList />
              </PrivateRoute>
            }
          />
          <Route
            path="/knowledge/new"
            element={
              <PrivateRoute>
                <KnowledgeEdit />
              </PrivateRoute>
            }
          />
          <Route
            path="/knowledge/:id"
            element={
              <PrivateRoute>
                <KnowledgeEdit />
              </PrivateRoute>
            }
          />
          <Route
            path="/issues"
            element={
              <PrivateRoute>
                <IssuesList />
              </PrivateRoute>
            }
          />
          <Route
            path="/portal/:businessUnitCode/issues"
            element={
              <PrivateRoute>
                <IssuesList />
              </PrivateRoute>
            }
          />
          <Route
            path="/insights"
            element={
              <PrivateRoute>
                <InsightsList />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App

