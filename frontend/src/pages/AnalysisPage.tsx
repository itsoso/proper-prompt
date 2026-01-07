import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { BarChart3, Send, Loader2, Sparkles, Copy, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../utils/api'
import { debugLog } from '../utils/debug'

export default function AnalysisPage() {
  const [formData, setFormData] = useState({
    group_type: 'investment',
    chat_content: '',
    time_period: '今天',
    analysis_focus: '',
    custom_prompt: '',
  })
  const [useCustomPrompt, setUseCustomPrompt] = useState(false)

  const [result, setResult] = useState<{
    analysis: string
    key_points: string[]
    execution_time_ms: number
    tokens_used: number
  } | null>(null)

  // Quick analysis mutation
  const analysisMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      debugLog.info('Starting quick analysis', data, 'AnalysisPage')
      const response = await api.analysis.quick(data)
      return response.data
    },
    onSuccess: (data) => {
      setResult(data)
      debugLog.info('Analysis completed', { execution_time_ms: data.execution_time_ms }, 'AnalysisPage')
      toast.success(`分析完成，耗时 ${data.execution_time_ms}ms`)
    },
    onError: (error: Error) => {
      debugLog.error('Analysis failed', error, 'AnalysisPage')
      toast.error(`分析失败: ${error.message}`)
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!formData.chat_content.trim()) {
      toast.error('请输入聊天内容')
      return
    }
    analysisMutation.mutate(formData)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('已复制到剪贴板')
  }

  const sampleContent = `[2024-01-15 09:00] 张三: 大家早，今天看好哪些板块？
[2024-01-15 09:02] 李四: AI相关的继续看好，特别是算力方向
[2024-01-15 09:05] 王五: 同意，英伟达昨晚又创新高了
[2024-01-15 09:10] 张三: 国内有什么标的推荐吗？
[2024-01-15 09:15] 李四: 可以关注一下寒武纪、海光信息
[2024-01-15 09:20] 赵六: 注意风险，AI概念已经涨很多了
[2024-01-15 09:25] 王五: 确实，建议分批建仓，不要追高
[2024-01-15 09:30] 张三: 明白了，谢谢大家的建议`

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">群聊分析</h2>
        <p className="text-dark-400 mt-1">输入群聊内容，获取智能分析结果</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input Section */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary-400" />
            分析设置
          </h3>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">群组类型</label>
                <select
                  value={formData.group_type}
                  onChange={(e) => setFormData({ ...formData, group_type: e.target.value })}
                  className="select"
                >
                  <option value="investment">投资群</option>
                  <option value="science">科普群</option>
                  <option value="learning">学习群</option>
                  <option value="technology">技术群</option>
                  <option value="health">健康群</option>
                  <option value="custom">自定义</option>
                </select>
              </div>
              <div>
                <label className="label">时间段</label>
                <select
                  value={formData.time_period}
                  onChange={(e) => setFormData({ ...formData, time_period: e.target.value })}
                  className="select"
                >
                  <option value="今天">今天</option>
                  <option value="本周">本周</option>
                  <option value="本月">本月</option>
                  <option value="本季度">本季度</option>
                </select>
              </div>
            </div>

            <div>
              <label className="label">分析重点（可选）</label>
              <input
                type="text"
                value={formData.analysis_focus}
                onChange={(e) => setFormData({ ...formData, analysis_focus: e.target.value })}
                className="input"
                placeholder="如：话题热度、成员活跃度、投资观点..."
              />
            </div>

            {/* Custom Prompt Toggle */}
            <div className="flex items-center justify-between p-3 bg-dark-700 rounded-lg">
              <div>
                <p className="text-white text-sm font-medium">使用自定义 Prompt</p>
                <p className="text-dark-400 text-xs">自定义分析提示词，获得更精准的结果</p>
              </div>
              <button
                type="button"
                onClick={() => setUseCustomPrompt(!useCustomPrompt)}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  useCustomPrompt ? 'bg-primary-500' : 'bg-dark-600'
                }`}
              >
                <span
                  className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                    useCustomPrompt ? 'left-7' : 'left-1'
                  }`}
                />
              </button>
            </div>

            {/* Custom Prompt Input */}
            {useCustomPrompt && (
              <div>
                <label className="label">自定义 Prompt</label>
                <textarea
                  value={formData.custom_prompt}
                  onChange={(e) => setFormData({ ...formData, custom_prompt: e.target.value })}
                  className="input min-h-[120px] font-mono text-sm"
                  placeholder={`请分析以下群聊内容：

1. 总结主要讨论话题
2. 提取关键观点和建议
3. 分析成员互动情况
4. 给出综合评价

聊天内容如下：
{chat_content}`}
                />
                <p className="text-dark-500 text-xs mt-1">
                  提示：使用 {'{chat_content}'} 代表聊天内容，{'{time_period}'} 代表时间段
                </p>
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="label mb-0">聊天内容</label>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, chat_content: sampleContent })}
                  className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1"
                >
                  <RefreshCw className="w-3 h-3" />
                  使用示例
                </button>
              </div>
              <textarea
                value={formData.chat_content}
                onChange={(e) => setFormData({ ...formData, chat_content: e.target.value })}
                className="input min-h-[300px] font-mono text-sm"
                placeholder="粘贴群聊内容，格式如：&#10;[时间] 发送者: 消息内容"
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary w-full flex items-center justify-center gap-2"
              disabled={analysisMutation.isPending}
            >
              {analysisMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  分析中...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  开始分析
                </>
              )}
            </button>
          </form>
        </motion.div>

        {/* Result Section */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="card"
        >
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-accent-400" />
            分析结果
          </h3>

          {result ? (
            <div className="space-y-4">
              {/* Stats */}
              <div className="flex gap-4 text-sm">
                <div className="px-3 py-1 rounded-lg bg-dark-700">
                  <span className="text-dark-400">耗时：</span>
                  <span className="text-white">{result.execution_time_ms}ms</span>
                </div>
                <div className="px-3 py-1 rounded-lg bg-dark-700">
                  <span className="text-dark-400">Token：</span>
                  <span className="text-white">{result.tokens_used}</span>
                </div>
              </div>

              {/* Key Points */}
              {result.key_points && result.key_points.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-dark-300 mb-2">关键要点</h4>
                  <ul className="space-y-2">
                    {result.key_points.map((point, index) => (
                      <li
                        key={index}
                        className="flex items-start gap-2 text-sm text-dark-200"
                      >
                        <span className="text-primary-400 mt-1">•</span>
                        {point}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Full Analysis */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-medium text-dark-300">详细分析</h4>
                  <button
                    onClick={() => copyToClipboard(result.analysis)}
                    className="text-xs text-primary-400 hover:text-primary-300 flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" />
                    复制
                  </button>
                </div>
                <div className="bg-dark-900 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                  <pre className="text-sm text-dark-200 whitespace-pre-wrap font-sans">
                    {result.analysis}
                  </pre>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-[400px] text-dark-500">
              <BarChart3 className="w-16 h-16 mb-4 opacity-50" />
              <p>分析结果将显示在这里</p>
              <p className="text-sm mt-1">输入聊天内容后点击"开始分析"</p>
            </div>
          )}
        </motion.div>
      </div>
    </div>
  )
}

