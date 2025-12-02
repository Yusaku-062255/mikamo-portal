import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import api from '../utils/api'
import { format } from 'date-fns'

type WeatherType = 'sunny' | 'cloudy' | 'rainy' | 'snow' | null

interface DailyLogData {
  date: string
  weather: WeatherType
  sales_amount: number
  customers_count: number
  transaction_count: number
  highlight: string
  problem: string
  memo: string
}

const DailyLog = () => {
  const navigate = useNavigate()
  const [formData, setFormData] = useState<DailyLogData>({
    date: format(new Date(), 'yyyy-MM-dd'),
    weather: null,
    sales_amount: 0,
    customers_count: 0,
    transaction_count: 0,
    highlight: '',
    problem: '',
    memo: '',
  })
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)

  const weatherOptions = [
    { value: 'sunny', label: '晴れ', emoji: '☀️' },
    { value: 'cloudy', label: '曇り', emoji: '☁️' },
    { value: 'rainy', label: '雨', emoji: '🌧️' },
    { value: 'snow', label: '雪', emoji: '❄️' },
  ]

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      await api.post('/api/daily-logs', {
        ...formData,
        date: formData.date,
      })
      setShowSuccess(true)
      setTimeout(() => {
        setShowSuccess(false)
        navigate('/dashboard')
      }, 3000)
    } catch (error: any) {
      alert(error.response?.data?.detail || '保存に失敗しました')
    } finally {
      setIsLoading(false)
    }
  }

  const updateNumber = (field: 'sales_amount' | 'customers_count' | 'transaction_count', delta: number) => {
    setFormData((prev) => ({
      ...prev,
      [field]: Math.max(0, prev[field] + delta),
    }))
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
          <h1 className="text-xl font-bold">今日の振り返り</h1>
          <div className="w-8"></div>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="max-w-2xl mx-auto px-4 py-6 space-y-6">
        {/* 日付 */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            日付
          </label>
          <input
            type="date"
            value={formData.date}
            onChange={(e) => setFormData({ ...formData, date: e.target.value })}
            className="input-field"
            required
          />
        </div>

        {/* 天気選択 */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-4">
            今日の天気
          </label>
          <div className="grid grid-cols-4 gap-3">
            {weatherOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setFormData({ ...formData, weather: option.value as WeatherType })}
                className={`p-4 rounded-lg border-2 transition-all ${
                  formData.weather === option.value
                    ? 'border-mikamo-blue bg-blue-50'
                    : 'border-gray-200 bg-white'
                }`}
              >
                <div className="text-3xl mb-2">{option.emoji}</div>
                <div className="text-sm font-medium">{option.label}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 数値入力: 売上 */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            売上金額
          </label>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => updateNumber('sales_amount', -1000)}
              className="w-12 h-12 bg-gray-200 rounded-lg text-xl font-bold active:bg-gray-300"
            >
              −
            </button>
            <input
              type="number"
              inputMode="numeric"
              value={formData.sales_amount}
              onChange={(e) => setFormData({ ...formData, sales_amount: parseInt(e.target.value) || 0 })}
              className="input-field flex-1 text-center text-xl font-bold"
              min="0"
            />
            <button
              type="button"
              onClick={() => updateNumber('sales_amount', 1000)}
              className="w-12 h-12 bg-gray-200 rounded-lg text-xl font-bold active:bg-gray-300"
            >
              ＋
            </button>
          </div>
        </div>

        {/* 数値入力: お客様数 */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            お客様数
          </label>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => updateNumber('customers_count', -1)}
              className="w-12 h-12 bg-gray-200 rounded-lg text-xl font-bold active:bg-gray-300"
            >
              −
            </button>
            <input
              type="number"
              inputMode="numeric"
              value={formData.customers_count}
              onChange={(e) => setFormData({ ...formData, customers_count: parseInt(e.target.value) || 0 })}
              className="input-field flex-1 text-center text-xl font-bold"
              min="0"
            />
            <button
              type="button"
              onClick={() => updateNumber('customers_count', 1)}
              className="w-12 h-12 bg-gray-200 rounded-lg text-xl font-bold active:bg-gray-300"
            >
              ＋
            </button>
          </div>
        </div>

        {/* 数値入力: 取引数 */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            取引数
          </label>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => updateNumber('transaction_count', -1)}
              className="w-12 h-12 bg-gray-200 rounded-lg text-xl font-bold active:bg-gray-300"
            >
              −
            </button>
            <input
              type="number"
              inputMode="numeric"
              value={formData.transaction_count}
              onChange={(e) => setFormData({ ...formData, transaction_count: parseInt(e.target.value) || 0 })}
              className="input-field flex-1 text-center text-xl font-bold"
              min="0"
            />
            <button
              type="button"
              onClick={() => updateNumber('transaction_count', 1)}
              className="w-12 h-12 bg-gray-200 rounded-lg text-xl font-bold active:bg-gray-300"
            >
              ＋
            </button>
          </div>
        </div>

        {/* 定性データ: 良かったこと */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            今日の良かったこと ✨
          </label>
          <textarea
            value={formData.highlight}
            onChange={(e) => setFormData({ ...formData, highlight: e.target.value })}
            className="input-field min-h-[100px]"
            placeholder="音声入力でも大丈夫です。今日の良かったことを記録しましょう。"
          />
        </div>

        {/* 定性データ: 課題・チャレンジ */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            課題・チャレンジ 💪
          </label>
          <textarea
            value={formData.problem}
            onChange={(e) => setFormData({ ...formData, problem: e.target.value })}
            className="input-field min-h-[100px]"
            placeholder="音声入力でも大丈夫です。今日の課題やチャレンジを記録しましょう。"
          />
        </div>

        {/* メモ */}
        <div className="card">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            メモ
          </label>
          <textarea
            value={formData.memo}
            onChange={(e) => setFormData({ ...formData, memo: e.target.value })}
            className="input-field min-h-[100px]"
            placeholder="その他、気づいたことやメモがあれば記録してください。"
          />
        </div>

        {/* 保存ボタン（画面下部固定） */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 p-4 shadow-lg">
          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full"
          >
            {isLoading ? '保存中...' : '保存する'}
          </button>
        </div>
      </form>

      {/* 成功アニメーション */}
      <AnimatePresence>
        {showSuccess && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ y: 50 }}
              animate={{ y: 0 }}
              className="bg-white rounded-2xl p-8 max-w-sm mx-4 text-center"
            >
              <motion.div
                animate={{
                  scale: [1, 1.2, 1],
                  rotate: [0, 10, -10, 0],
                }}
                transition={{ duration: 0.5 }}
                className="text-6xl mb-4"
              >
                🎉
              </motion.div>
              <h2 className="text-2xl font-bold text-mikamo-blue mb-2">
                お疲れ様でした！
              </h2>
              <p className="text-gray-600 mb-4">
                本日の記録を保存しました
              </p>
              <motion.div
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  repeat: Infinity,
                  duration: 1.5,
                }}
                className="text-4xl"
              >
                ✨
              </motion.div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default DailyLog

