import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Key, Copy, Trash2, Eye, EyeOff, X, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../utils/api'

interface APIKey {
  id: number
  name: string
  prefix: string
  scopes: string[]
  rate_limit: number
  integration_type: string | null
  is_active: boolean
  total_requests: number
  last_used_at: string | null
  created_at: string
}

export default function APIKeysPage() {
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [newKey, setNewKey] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    name: '',
    scopes: ['read'],
    rate_limit: 1000,
    integration_type: '',
  })

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const response = await api.apiKeys.list()
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.apiKeys.create(data),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      setNewKey(response.data.key)
      toast.success('API密钥创建成功')
    },
    onError: (error: Error) => {
      toast.error(`创建失败: ${error.message}`)
    },
  })

  const revokeMutation = useMutation({
    mutationFn: (id: number) => api.apiKeys.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('API密钥已撤销')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('已复制到剪贴板')
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">API密钥管理</h2>
          <p className="text-dark-400 mt-1">管理外部系统集成的API密钥</p>
        </div>
        <button onClick={() => setIsModalOpen(true)} className="btn btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          创建密钥
        </button>
      </div>

      <div className="card">
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-16 bg-dark-700 rounded" />
            ))}
          </div>
        ) : apiKeys?.length === 0 ? (
          <div className="text-center py-12">
            <Key className="w-16 h-16 mx-auto text-dark-600 mb-4" />
            <p className="text-dark-400">暂无API密钥</p>
          </div>
        ) : (
          <div className="space-y-4">
            {apiKeys?.map((key: APIKey) => (
              <div key={key.id} className="p-4 bg-dark-700/50 rounded-lg border border-dark-600 flex justify-between items-center">
                <div>
                  <h4 className="font-medium text-white">{key.name}</h4>
                  <p className="text-dark-400 text-sm font-mono">{key.prefix}...****</p>
                  <div className="flex gap-2 mt-2">
                    {key.scopes.map((scope) => (
                      <span key={scope} className="badge badge-primary">{scope}</span>
                    ))}
                    {key.integration_type && (
                      <span className="badge badge-accent">{key.integration_type}</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${key.is_active ? 'bg-green-500' : 'bg-red-500'}`} />
                  <button
                    onClick={() => {
                      if (confirm('确定要撤销此密钥吗？')) {
                        revokeMutation.mutate(key.id)
                      }
                    }}
                    className="p-2 rounded-lg hover:bg-red-500/20 text-dark-400 hover:text-red-400"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => { setIsModalOpen(false); setNewKey(null) }}
          >
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.9 }}
              className="card max-w-md w-full"
              onClick={(e) => e.stopPropagation()}
            >
              {newKey ? (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 text-green-400">
                    <Key className="w-5 h-5" />
                    <h3 className="text-lg font-semibold">密钥创建成功</h3>
                  </div>
                  <div className="p-3 bg-dark-900 rounded-lg flex items-center gap-2">
                    <code className="text-sm text-primary-300 flex-1 break-all">{newKey}</code>
                    <button onClick={() => copyToClipboard(newKey)} className="p-2 hover:bg-dark-700 rounded">
                      <Copy className="w-4 h-4 text-dark-400" />
                    </button>
                  </div>
                  <div className="flex items-start gap-2 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                    <p className="text-yellow-300 text-sm">请立即保存此密钥，它只会显示一次！</p>
                  </div>
                  <button onClick={() => { setIsModalOpen(false); setNewKey(null) }} className="btn btn-primary w-full">
                    完成
                  </button>
                </div>
              ) : (
                <>
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-semibold text-white">创建API密钥</h3>
                    <button onClick={() => setIsModalOpen(false)} className="p-2 rounded-lg hover:bg-dark-700 text-dark-400">
                      <X className="w-5 h-5" />
                    </button>
                  </div>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <label className="label">名称</label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        className="input"
                        required
                      />
                    </div>
                    <div>
                      <label className="label">集成类型</label>
                      <select
                        value={formData.integration_type}
                        onChange={(e) => setFormData({ ...formData, integration_type: e.target.value })}
                        className="select"
                      >
                        <option value="">通用</option>
                        <option value="browser-llm-orchestrator">Browser-LLM-Orchestrator</option>
                        <option value="chatlog">Chatlog</option>
                        <option value="health-llm-driven">Health-LLM-Driven</option>
                      </select>
                    </div>
                    <div>
                      <label className="label">每小时请求限制</label>
                      <input
                        type="number"
                        value={formData.rate_limit}
                        onChange={(e) => setFormData({ ...formData, rate_limit: parseInt(e.target.value) })}
                        className="input"
                        min="1"
                      />
                    </div>
                    <div className="flex gap-3 pt-4">
                      <button type="button" onClick={() => setIsModalOpen(false)} className="btn btn-secondary flex-1">
                        取消
                      </button>
                      <button type="submit" className="btn btn-primary flex-1" disabled={createMutation.isPending}>
                        {createMutation.isPending ? '创建中...' : '创建'}
                      </button>
                    </div>
                  </form>
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

