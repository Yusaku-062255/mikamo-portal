import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useTenantSettings } from '../stores/tenantStore'
import api from '../utils/api'
import Layout from '../components/Layout'

interface Conversation {
  id: number
  title: string | null
  business_unit_id: number | null
  business_unit_name: string | null
  created_at: string
  updated_at: string
  message_count: number
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

interface BusinessUnit {
  id: number
  name: string
  code: string
}

const AIChat = () => {
  const user = useAuthStore((state) => state.user)
  const navigate = useNavigate()
  const { primaryColor, displayName, businessUnitLabel, settings } = useTenantSettings()
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [businessUnits, setBusinessUnits] = useState<BusinessUnit[]>([])
  const [selectedBusinessUnitId, setSelectedBusinessUnitId] = useState<number | null>(null)
  const [isLoadingConversations, setIsLoadingConversations] = useState(true)
  const [isLoadingMessages, setIsLoadingMessages] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) {
      navigate('/login')
      return
    }
    fetchBusinessUnits()
    fetchConversations()
  }, [user])

  useEffect(() => {
    if (currentConversationId) {
      fetchMessages(currentConversationId)
    } else {
      setMessages([])
    }
  }, [currentConversationId])

  const fetchBusinessUnits = async () => {
    try {
      const response = await api.get('/api/portal/business-units')
      setBusinessUnits(response.data)
      // ユーザーの所属部門をデフォルトに設定
      if (user?.business_unit_id) {
        setSelectedBusinessUnitId(user.business_unit_id)
      } else if (response.data.length > 0) {
        setSelectedBusinessUnitId(response.data[0].id)
      }
    } catch (error) {
      console.error('事業部門取得エラー:', error)
    }
  }

  const fetchConversations = async () => {
    setIsLoadingConversations(true)
    try {
      const response = await api.get('/api/ai/conversations')
      setConversations(response.data)
    } catch (error) {
      console.error('会話一覧取得エラー:', error)
    } finally {
      setIsLoadingConversations(false)
    }
  }

  const fetchMessages = async (conversationId: number) => {
    setIsLoadingMessages(true)
    try {
      const response = await api.get(`/api/ai/conversations/${conversationId}/messages`)
      setMessages(response.data)
    } catch (error) {
      console.error('メッセージ取得エラー:', error)
    } finally {
      setIsLoadingMessages(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!message.trim()) return

    setError('')
    setIsLoading(true)

    try {
      // スタッフ・マネージャーの場合はスタッフQAモードを使用
      const mode = (user?.role === 'staff' || user?.role === 'manager') ? 'staff_qa' : undefined
      
      const response = await api.post('/api/ai/chat', {
        message: message.trim(),
        conversation_id: currentConversationId,
        business_unit_id: selectedBusinessUnitId,
        mode: mode  // スタッフQAモードを指定
      })

      // 会話IDを更新
      if (!currentConversationId) {
        setCurrentConversationId(response.data.conversation_id)
      }

      // メッセージを追加
      setMessages([
        ...messages,
        { id: 0, role: 'user', content: message.trim(), created_at: new Date().toISOString() },
        { id: response.data.message_id, role: 'assistant', content: response.data.reply, created_at: new Date().toISOString() }
      ])

      setMessage('')
      
      // 会話一覧を更新
      fetchConversations()
    } catch (error: any) {
      setError(error.response?.data?.detail || '送信に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewConversation = () => {
    setCurrentConversationId(null)
    setMessages([])
    setMessage('')
  }

  const handleSelectConversation = (conversationId: number) => {
    setCurrentConversationId(conversationId)
  }

  // AIプランバッジの設定
  const getAiPlanBadge = () => {
    const policy = settings?.ai_tier_policy || 'all'
    const badges: Record<string, { label: string; color: string; description: string }> = {
      all: {
        label: 'プレミアム',
        color: '#8B5CF6', // purple
        description: '全ティア利用可能'
      },
      standard_max: {
        label: 'スタンダード',
        color: '#3B82F6', // blue
        description: 'STANDARD以下'
      },
      basic_only: {
        label: 'ライト',
        color: '#22C55E', // green
        description: 'BASICのみ'
      }
    }
    return badges[policy] || badges.all
  }

  const aiPlanBadge = getAiPlanBadge()

  return (
    <Layout>
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* ページタイトル */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            <h2 className="text-2xl font-bold" style={{ color: primaryColor }}>
              AI相談
            </h2>
            {/* AIプランバッジ */}
            <span
              className="px-2 py-1 text-xs font-medium text-white rounded-full"
              style={{ backgroundColor: aiPlanBadge.color }}
              title={aiPlanBadge.description}
            >
              {aiPlanBadge.label}プラン
            </span>
          </div>
          <p className="text-sm text-gray-600">
            {displayName}専属AIアシスタント
          </p>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* サイドバー: 会話一覧 */}
          <div className="lg:col-span-1">
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold" style={{ color: primaryColor }}>会話履歴</h2>
                <button
                  onClick={handleNewConversation}
                  className="text-sm px-3 py-1 text-white rounded hover:opacity-90 transition-colors"
                  style={{ backgroundColor: primaryColor }}
                >
                  新規
                </button>
              </div>

              {/* 事業部門選択 */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {businessUnitLabel}
                </label>
                <select
                  value={selectedBusinessUnitId || ''}
                  onChange={(e) => setSelectedBusinessUnitId(e.target.value ? Number(e.target.value) : null)}
                  className="input-field"
                >
                  {businessUnits.map((bu) => (
                    <option key={bu.id} value={bu.id}>
                      {bu.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* 会話一覧 */}
              {isLoadingConversations ? (
                <div className="text-center py-4 text-gray-500">読み込み中...</div>
              ) : conversations.length === 0 ? (
                <div className="text-center py-4 text-gray-500 text-sm">
                  会話履歴がありません
                </div>
              ) : (
                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                  {conversations.map((conv) => (
                    <button
                      key={conv.id}
                      onClick={() => handleSelectConversation(conv.id)}
                      className="w-full text-left p-3 rounded-lg border transition-colors"
                      style={{
                        backgroundColor: currentConversationId === conv.id ? primaryColor : '#f9fafb',
                        color: currentConversationId === conv.id ? 'white' : 'inherit',
                        borderColor: currentConversationId === conv.id ? primaryColor : '#e5e7eb'
                      }}
                    >
                      <div className="font-semibold text-sm mb-1">
                        {conv.title || '（タイトルなし）'}
                      </div>
                      <div className={`text-xs ${currentConversationId === conv.id ? 'opacity-90' : 'text-gray-500'}`}>
                        {conv.business_unit_name || '全社共通'} · {conv.message_count}件
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* メイン: チャットエリア */}
          <div className="lg:col-span-2">
            <div className="card flex flex-col" style={{ minHeight: '500px' }}>
              {/* メッセージ表示エリア */}
              <div className="flex-1 overflow-y-auto mb-4 space-y-4" style={{ maxHeight: '400px' }}>
                {isLoadingMessages ? (
                  <div className="text-center py-8 text-gray-500">読み込み中...</div>
                ) : messages.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p className="text-lg mb-2">👋 こんにちは！</p>
                    <p className="text-sm">何でも聞いてください。ナレッジベースから関連情報を参照して回答します。</p>
                  </div>
                ) : (
                  messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className="max-w-[80%] rounded-lg p-4"
                        style={{
                          backgroundColor: msg.role === 'user' ? primaryColor : '#f3f4f6',
                          color: msg.role === 'user' ? 'white' : '#1f2937'
                        }}
                      >
                        <div className="whitespace-pre-wrap">{msg.content}</div>
                        <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-white/70' : 'text-gray-500'}`}>
                          {new Date(msg.created_at).toLocaleTimeString('ja-JP', {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </div>
                      </div>
                    </div>
                  ))
                )}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg p-4">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* エラーメッセージ */}
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                  {error}
                </div>
              )}

              {/* 入力フォーム */}
              <form onSubmit={handleSubmit} className="flex gap-2">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  className="input-field flex-1 min-h-[80px] resize-none"
                  placeholder="質問を入力してください..."
                  required
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                      handleSubmit(e as any)
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={isLoading || !message.trim()}
                  className="btn-primary px-6 self-end"
                >
                  {isLoading ? '送信中...' : '送信'}
                </button>
              </form>
              <p className="text-xs text-gray-500 mt-1">
                Enterで送信、Cmd/Ctrl+Enterで改行
              </p>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default AIChat
