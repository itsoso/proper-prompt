import { useState } from 'react'
import { motion } from 'framer-motion'
import { Save, RefreshCw, Database, Server, Globe } from 'lucide-react'
import toast from 'react-hot-toast'
import { debugLog } from '../utils/debug'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    openai_api_key: '',
    openai_base_url: 'https://api.openai.com/v1',
    default_model: 'gpt-4o-mini',
    max_tokens: 4096,
  })

  const [debugEnabled, setDebugEnabled] = useState(
    localStorage.getItem('debug') === 'true'
  )

  const handleSave = () => {
    localStorage.setItem('llm_settings', JSON.stringify(settings))
    toast.success('设置已保存')
    debugLog.info('Settings saved', settings, 'SettingsPage')
  }

  const toggleDebug = () => {
    const newValue = !debugEnabled
    setDebugEnabled(newValue)
    debugLog.setEnabled(newValue)
  }

  const clearLogs = () => {
    debugLog.clear()
    toast.success('日志已清空')
  }

  const exportLogs = () => {
    const logs = debugLog.export()
    const blob = new Blob([logs], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `proper-prompts-logs-${new Date().toISOString()}.json`
    a.click()
    URL.revokeObjectURL(url)
    toast.success('日志已导出')
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">系统设置</h2>
        <p className="text-dark-400 mt-1">配置LLM连接和系统选项</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LLM Settings */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-primary-400" />
            LLM配置
          </h3>
          <div className="space-y-4">
            <div>
              <label className="label">OpenAI API Key</label>
              <input
                type="password"
                value={settings.openai_api_key}
                onChange={(e) => setSettings({ ...settings, openai_api_key: e.target.value })}
                className="input"
                placeholder="sk-..."
              />
            </div>
            <div>
              <label className="label">Base URL</label>
              <input
                type="text"
                value={settings.openai_base_url}
                onChange={(e) => setSettings({ ...settings, openai_base_url: e.target.value })}
                className="input"
              />
            </div>
            <div>
              <label className="label">默认模型</label>
              <select
                value={settings.default_model}
                onChange={(e) => setSettings({ ...settings, default_model: e.target.value })}
                className="select"
              >
                <option value="gpt-4o-mini">GPT-4o Mini</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="gpt-4-turbo">GPT-4 Turbo</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              </select>
            </div>
            <div>
              <label className="label">最大Token数</label>
              <input
                type="number"
                value={settings.max_tokens}
                onChange={(e) => setSettings({ ...settings, max_tokens: parseInt(e.target.value) })}
                className="input"
                min="100"
                max="128000"
              />
            </div>
            <button onClick={handleSave} className="btn btn-primary w-full flex items-center justify-center gap-2">
              <Save className="w-4 h-4" />
              保存设置
            </button>
          </div>
        </motion.div>

        {/* Debug Settings */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="card">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-accent-400" />
            调试与日志
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-dark-700 rounded-lg">
              <div>
                <p className="text-white font-medium">调试模式</p>
                <p className="text-dark-400 text-sm">启用详细的前端日志记录</p>
              </div>
              <button
                onClick={toggleDebug}
                className={`w-12 h-6 rounded-full transition-colors relative ${
                  debugEnabled ? 'bg-primary-500' : 'bg-dark-600'
                }`}
              >
                <span
                  className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-transform ${
                    debugEnabled ? 'left-7' : 'left-1'
                  }`}
                />
              </button>
            </div>
            <div className="flex gap-3">
              <button onClick={exportLogs} className="btn btn-secondary flex-1 flex items-center justify-center gap-2">
                <RefreshCw className="w-4 h-4" />
                导出日志
              </button>
              <button onClick={clearLogs} className="btn btn-secondary flex-1 flex items-center justify-center gap-2">
                清空日志
              </button>
            </div>
            <div className="p-4 bg-dark-900 rounded-lg">
              <p className="text-dark-400 text-sm">
                日志存储在浏览器本地，包含API请求、错误信息和性能数据。
                在控制台输入 <code className="text-primary-400">debugLog</code> 可直接访问日志对象。
              </p>
            </div>
          </div>
        </motion.div>

        {/* Integration Info */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="card lg:col-span-2">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-green-400" />
            外部集成
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { name: 'Browser-LLM-Orchestrator', endpoint: '/api/v1/integrations/browser-llm/analyze', desc: '浏览器内容分析' },
              { name: 'Chatlog', endpoint: '/api/v1/integrations/chatlog/analyze', desc: '聊天记录分析' },
              { name: 'Health-LLM-Driven', endpoint: '/api/v1/integrations/health-llm/analyze', desc: '健康数据分析' },
            ].map((integration) => (
              <div key={integration.name} className="p-4 bg-dark-700/50 rounded-lg border border-dark-600">
                <h4 className="font-medium text-white">{integration.name}</h4>
                <p className="text-dark-400 text-sm mt-1">{integration.desc}</p>
                <code className="text-xs text-primary-400 mt-2 block">{integration.endpoint}</code>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}

