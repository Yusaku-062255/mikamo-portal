import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../utils/api'

const AIChat = () => {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [suggestionTips, setSuggestionTips] = useState<string[]>([])
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(true)

  useEffect(() => {
    // 部署に応じたサジェストを取得
    const fetchSuggestions = async () => {
      try {
        const response = await api.get('/api/ai/suggestions')
        setSuggestionTips(response.data)
      } catch (error) {
        console.error('サジェスト取得エラー:', error)
        // フォールバック
        setSuggestionTips([
          '今日の接客のコツは？',
          '売上を上げるための工夫は？',
        ])
      } finally {
        setIsLoadingSuggestions(false)
      }
    }
    fetchSuggestions()
  }, [])

  const handleSuggestionClick = (tip: string) => {
    setQuestion(tip)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return

    setIsLoading(true)
    try {
      const response = await api.post('/api/ai', { question })
      // 回答が含まれている場合は表示（v0.1ではダミー回答）
      if (response.data.answer) {
        alert(`回答: ${response.data.answer}`)
      } else {
        alert('質問を送信しました。')
      }
      setQuestion('')
    } catch (error: any) {
      alert(error.response?.data?.detail || '送信に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-24">
      {/* ヘッダー */}
      <header className="bg-mikamo-blue text-white p-4 shadow-md">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/dashboard')}
            className="text-lg"
          >
            ← 戻る
          </button>
          <h1 className="text-xl font-bold">AI相談</h1>
          <div className="w-8"></div>
        </div>
      </header>

      <div className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* 説明 */}
        <div className="card">
          <h2 className="text-xl font-bold mb-2 text-mikamo-blue">
            AIに相談してみましょう 🤖
          </h2>
          <p className="text-gray-600">
            何を聞けばいいかわからない時は、下のサジェストから選んでください。
          </p>
        </div>

        {/* サジェストチップ */}
        <div className="card">
          <h3 className="text-lg font-semibold mb-4 text-gray-700">
            よくある質問
          </h3>
          {isLoadingSuggestions ? (
            <div className="text-center py-4 text-gray-500">読み込み中...</div>
          ) : (
            <div className="space-y-2">
              {suggestionTips.map((tip, index) => (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleSuggestionClick(tip)}
                  className="w-full text-left p-4 bg-gray-50 hover:bg-gray-100 rounded-lg border border-gray-200 transition-colors active:bg-gray-200"
                >
                  <span className="text-mikamo-blue mr-2">💡</span>
                  {tip}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 質問フォーム */}
        <form onSubmit={handleSubmit} className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            質問を入力してください
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="input-field min-h-[150px]"
            placeholder="音声入力でも大丈夫です。気になることを何でも聞いてみましょう。"
            required
          />
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            className="btn-primary w-full mt-4"
          >
            {isLoading ? '送信中...' : '質問を送信'}
          </button>
        </form>

        {/* 注意書き */}
        <div className="card bg-blue-50 border border-blue-200">
          <p className="text-sm text-blue-800">
            <strong>注意:</strong> AI回答機能はv0.1では基本的な回答を返します。
            v0.2以降でより高度なAI機能を実装予定です。
          </p>
        </div>
      </div>
    </div>
  )
}

export default AIChat

