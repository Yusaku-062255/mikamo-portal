import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'
import { ErrorBoundary } from './components/ErrorBoundary'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DailyLog from './pages/DailyLog'
import AIChat from './pages/AIChat'
import PrivateRoute from './components/PrivateRoute'

function App() {
  const fetchUser = useAuthStore((state) => state.fetchUser)

  useEffect(() => {
    // アプリ起動時にユーザー情報を取得
    fetchUser()
  }, [fetchUser])

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
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  )
}

export default App

