import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import api from '../utils/api'

interface User {
  id: number
  email: string
  full_name: string
  department_id: number
  department_name?: string
  department_code?: string
  role: string
  is_active: boolean
  created_at: string
}

interface Department {
  id: number
  name: string
  code: string
}

interface UserFormData {
  email: string
  password: string
  full_name: string
  department_id: number
  role: string
}

const AdminUsers = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const [users, setUsers] = useState<User[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  
  // フィルター
  const [filterDepartmentId, setFilterDepartmentId] = useState<number | ''>('')
  const [filterRole, setFilterRole] = useState<string>('')
  
  // フォームデータ
  const [formData, setFormData] = useState<UserFormData>({
    email: '',
    password: '',
    full_name: '',
    department_id: 0,
    role: 'staff'
  })

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

  // データ取得
  useEffect(() => {
    if (user?.role === 'admin') {
      fetchDepartments()
      fetchUsers()
    }
  }, [user, filterDepartmentId, filterRole])

  const fetchDepartments = async () => {
    try {
      const response = await api.get('/api/admin/departments')
      setDepartments(response.data)
      if (response.data.length > 0 && formData.department_id === 0) {
        setFormData({ ...formData, department_id: response.data[0].id })
      }
    } catch (error) {
      console.error('部門取得エラー:', error)
    }
  }

  const fetchUsers = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      if (filterDepartmentId) {
        params.append('department_id', filterDepartmentId.toString())
      }
      if (filterRole) {
        params.append('role', filterRole)
      }
      
      const url = `/api/admin/users${params.toString() ? '?' + params.toString() : ''}`
      const response = await api.get(url)
      setUsers(response.data)
    } catch (error: any) {
      console.error('ユーザー取得エラー:', error)
      setError(error.response?.data?.detail || 'ユーザー一覧の取得に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccessMessage('')
    setIsSubmitting(true)

    try {
      await api.post('/api/admin/users', formData)
      setSuccessMessage('ユーザーを作成しました。初期パスワードは別途安全な方法で共有してください。')
      setIsModalOpen(false)
      setFormData({
        email: '',
        password: '',
        full_name: '',
        department_id: departments[0]?.id || 0,
        role: 'staff'
      })
      fetchUsers()
    } catch (error: any) {
      setError(error.response?.data?.detail || 'ユーザーの作成に失敗しました')
    } finally {
      setIsSubmitting(false)
    }
  }

  const generatePassword = () => {
    // ランダムなパスワードを生成（12文字）
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*'
    let password = ''
    for (let i = 0; i < 12; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    setFormData({ ...formData, password })
  }

  const getRoleName = (role: string) => {
    const roleNames: Record<string, string> = {
      staff: 'スタッフ',
      manager: 'マネージャー',
      head: '経営本陣',
      admin: '管理者'
    }
    return roleNames[role] || role
  }

  if (!user || user.role !== 'admin') {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* ヘッダー */}
      <header className="bg-mikamo-blue text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">ユーザー管理</h1>
            <p className="text-sm opacity-90 mt-1">管理者専用画面</p>
          </div>
          <button
            onClick={() => navigate('/dashboard')}
            className="text-sm px-4 py-2 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
          >
            ダッシュボードに戻る
          </button>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
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

        {/* フィルターと新規作成ボタン */}
        <div className="card">
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex flex-col sm:flex-row gap-4 flex-1">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  部門で絞り込み
                </label>
                <select
                  value={filterDepartmentId}
                  onChange={(e) => setFilterDepartmentId(e.target.value ? Number(e.target.value) : '')}
                  className="input-field"
                >
                  <option value="">すべて</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ロールで絞り込み
                </label>
                <select
                  value={filterRole}
                  onChange={(e) => setFilterRole(e.target.value)}
                  className="input-field"
                >
                  <option value="">すべて</option>
                  <option value="staff">スタッフ</option>
                  <option value="manager">マネージャー</option>
                  <option value="head">経営本陣</option>
                  <option value="admin">管理者</option>
                </select>
              </div>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="btn-primary whitespace-nowrap"
            >
              新しいユーザーを追加
            </button>
          </div>
        </div>

        {/* ユーザー一覧テーブル */}
        <div className="card overflow-x-auto">
          {isLoading ? (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500">読み込み中...</div>
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              ユーザーが見つかりません
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-medium text-gray-700">氏名</th>
                  <th className="text-left p-3 font-medium text-gray-700">メールアドレス</th>
                  <th className="text-left p-3 font-medium text-gray-700">部門</th>
                  <th className="text-left p-3 font-medium text-gray-700">ロール</th>
                  <th className="text-left p-3 font-medium text-gray-700">ステータス</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-b hover:bg-gray-50">
                    <td className="p-3">{u.full_name}</td>
                    <td className="p-3 text-sm text-gray-600">{u.email}</td>
                    <td className="p-3">{u.department_name || '-'}</td>
                    <td className="p-3">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">
                        {getRoleName(u.role)}
                      </span>
                    </td>
                    <td className="p-3">
                      {u.is_active ? (
                        <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm">
                          有効
                        </span>
                      ) : (
                        <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded text-sm">
                          無効
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* 新規ユーザー作成モーダル */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4 text-mikamo-blue">新しいユーザーを追加</h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  氏名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  className="input-field"
                  placeholder="山田 太郎"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  メールアドレス <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  placeholder="example@mikamo.co.jp"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  部門 <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.department_id}
                  onChange={(e) => setFormData({ ...formData, department_id: Number(e.target.value) })}
                  className="input-field"
                  required
                >
                  <option value="0">選択してください</option>
                  {departments.map((dept) => (
                    <option key={dept.id} value={dept.id}>
                      {dept.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  ロール <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  className="input-field"
                  required
                >
                  <option value="staff">スタッフ</option>
                  <option value="manager">マネージャー</option>
                  <option value="head">経営本陣</option>
                  <option value="admin">管理者</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  初期パスワード <span className="text-red-500">*</span>
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="input-field flex-1"
                    placeholder="パスワードを入力または自動生成"
                    required
                  />
                  <button
                    type="button"
                    onClick={generatePassword}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  >
                    自動生成
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  初期パスワードは別途安全な方法で共有してください
                </p>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsModalOpen(false)
                    setError('')
                    setFormData({
                      email: '',
                      password: '',
                      full_name: '',
                      department_id: departments[0]?.id || 0,
                      role: 'staff'
                    })
                  }}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                  disabled={isSubmitting}
                >
                  キャンセル
                </button>
                <button
                  type="submit"
                  className="flex-1 btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? '作成中...' : '作成'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminUsers

