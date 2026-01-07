import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, Trash2, FileText, Copy, Eye, X, Sparkles, Edit2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../utils/api'
import { debugLog } from '../utils/debug'

interface PromptTemplate {
  id: number
  name: string
  description: string | null
  group_type: string
  time_granularity: string
  style: string
  system_prompt: string
  user_prompt_template: string
  is_active: boolean
  is_default: boolean
  version: number
  created_at: string
}

const granularityLabels: Record<string, string> = {
  daily: '天级别',
  weekly: '周级别',
  monthly: '月级别',
  quarterly: '季度级别',
  yearly: '年级别',
  custom: '自定义',
}

const styleLabels: Record<string, string> = {
  analytical: '分析型',
  summary: '总结型',
  insight: '洞察型',
  comparative: '对比型',
  trending: '趋势型',
  member_focused: '成员聚焦型',
}

export default function PromptsPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isViewModalOpen, setIsViewModalOpen] = useState(false)
  const [isGenerateModalOpen, setIsGenerateModalOpen] = useState(false)
  const [viewingTemplate, setViewingTemplate] = useState<PromptTemplate | null>(null)
  const [editingTemplate, setEditingTemplate] = useState<PromptTemplate | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    group_type: 'custom',
    time_granularity: 'daily',
    style: 'analytical',
    system_prompt: '你是一个专业的群聊分析助手。',
    user_prompt_template: '',
  })

  // Generate form state
  const [generateForm, setGenerateForm] = useState({
    group_type: 'investment',
    time_granularity: 'daily',
    styles: ['analytical', 'summary', 'insight'],
    custom_requirements: '',
  })

  // Fetch templates
  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates', { type: selectedType }],
    queryFn: async () => {
      debugLog.debug('Fetching templates', { type: selectedType }, 'PromptsPage')
      const response = await api.prompts.templates.list({
        group_type: selectedType || undefined,
      })
      return response.data
    },
  })

  // Fetch builtin templates
  const { data: builtinTemplates } = useQuery({
    queryKey: ['builtin-templates'],
    queryFn: async () => {
      const response = await api.prompts.builtin()
      return response.data
    },
  })

  // Create template mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.prompts.templates.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('模板创建成功')
      setIsModalOpen(false)
      resetForm()
    },
    onError: (error: Error) => {
      toast.error(`创建失败: ${error.message}`)
    },
  })

  // Generate prompts mutation
  const generateMutation = useMutation({
    mutationFn: (data: typeof generateForm) => api.prompts.generate(data),
    onSuccess: (response) => {
      toast.success(`生成了 ${response.data.prompts.length} 个Prompt变体`)
      setIsGenerateModalOpen(false)
    },
    onError: (error: Error) => {
      toast.error(`生成失败: ${error.message}`)
    },
  })

  // Update template mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof formData> }) => 
      api.prompts.templates.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('模板更新成功')
      setIsModalOpen(false)
      setEditingTemplate(null)
      resetForm()
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`)
    },
  })

  // Delete template mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.prompts.templates.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] })
      toast.success('模板删除成功')
    },
    onError: (error: Error) => {
      toast.error(`删除失败: ${error.message}`)
    },
  })

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      group_type: 'custom',
      time_granularity: 'daily',
      style: 'analytical',
      system_prompt: '你是一个专业的群聊分析助手。',
      user_prompt_template: '',
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingTemplate) {
      updateMutation.mutate({ id: editingTemplate.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  const openEditModal = (template: PromptTemplate) => {
    setEditingTemplate(template)
    setFormData({
      name: template.name,
      description: template.description || '',
      group_type: template.group_type,
      time_granularity: template.time_granularity,
      style: template.style,
      system_prompt: template.system_prompt,
      user_prompt_template: template.user_prompt_template,
    })
    setIsModalOpen(true)
  }

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault()
    generateMutation.mutate(generateForm)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('已复制到剪贴板')
  }

  const filteredTemplates = templates?.filter((t: PromptTemplate) =>
    t.name.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Prompt模板</h2>
          <p className="text-dark-400 mt-1">管理和创建群聊分析Prompt模板</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setIsGenerateModalOpen(true)}
            className="btn btn-accent flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            自动生成
          </button>
          <button
            onClick={() => {
              setEditingTemplate(null)
              resetForm()
              setIsModalOpen(true)
            }}
            className="btn btn-primary flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            创建模板
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
            <input
              type="text"
              placeholder="搜索模板名称..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="select md:w-48"
          >
            <option value="">全部群组类型</option>
            <option value="investment">投资群</option>
            <option value="science">科普群</option>
            <option value="learning">学习群</option>
            <option value="technology">技术群</option>
            <option value="health">健康群</option>
            <option value="custom">自定义</option>
          </select>
        </div>
      </div>

      {/* Custom Templates Section */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">自定义模板</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <AnimatePresence>
            {isLoading ? (
              [...Array(3)].map((_, i) => (
                <div key={i} className="card animate-pulse">
                  <div className="h-6 bg-dark-700 rounded w-3/4 mb-4" />
                  <div className="h-4 bg-dark-700 rounded w-1/2 mb-2" />
                  <div className="h-4 bg-dark-700 rounded w-full" />
                </div>
              ))
            ) : filteredTemplates?.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <FileText className="w-16 h-16 mx-auto text-dark-600 mb-4" />
                <p className="text-dark-400">暂无自定义模板，点击上方按钮创建</p>
              </div>
            ) : (
              filteredTemplates?.map((template: PromptTemplate) => (
                <motion.div
                  key={template.id}
                  layout
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="card hover:border-primary-500/50 transition-colors"
                >
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="font-semibold text-white">{template.name}</h4>
                    <span className="badge badge-primary">v{template.version}</span>
                  </div>
                  
                  <div className="flex flex-wrap gap-2 mb-3">
                    <span className="badge bg-dark-700 text-dark-300 border border-dark-600">
                      {granularityLabels[template.time_granularity]}
                    </span>
                    <span className="badge bg-dark-700 text-dark-300 border border-dark-600">
                      {styleLabels[template.style]}
                    </span>
                  </div>

                  {template.description && (
                    <p className="text-dark-400 text-sm mb-3 line-clamp-2">{template.description}</p>
                  )}
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setViewingTemplate(template)
                        setIsViewModalOpen(true)
                      }}
                      className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors"
                      title="查看"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => openEditModal(template)}
                      className="p-2 rounded-lg hover:bg-primary-500/20 text-dark-400 hover:text-primary-400 transition-colors"
                      title="编辑"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => copyToClipboard(template.user_prompt_template)}
                      className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors"
                      title="复制"
                    >
                      <Copy className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('确定要删除此模板吗？')) {
                          deleteMutation.mutate(template.id)
                        }
                      }}
                      className="p-2 rounded-lg hover:bg-red-500/20 text-dark-400 hover:text-red-400 transition-colors"
                      title="删除"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Built-in Templates Section */}
      {builtinTemplates && builtinTemplates.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-white mb-4">内置模板</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {builtinTemplates.slice(0, 6).map((template: { group_type: string; time_granularity: string; style: string; template: string }, index: number) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="card bg-gradient-to-br from-dark-800 to-dark-900 hover:border-accent-500/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="badge badge-accent">内置</span>
                    <span className="badge badge-primary">{granularityLabels[template.time_granularity]}</span>
                  </div>
                </div>
                <h4 className="font-medium text-white mb-2">
                  {template.group_type} - {styleLabels[template.style]}
                </h4>
                <p className="text-dark-400 text-sm line-clamp-2 mb-3">
                  {template.template.slice(0, 100)}...
                </p>
                <button
                  onClick={() => copyToClipboard(template.template)}
                  className="btn btn-secondary w-full flex items-center justify-center gap-2 text-sm"
                >
                  <Copy className="w-4 h-4" />
                  复制模板
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      )}

      {/* Create Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => {
              setIsModalOpen(false)
              setEditingTemplate(null)
              resetForm()
            }}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="card max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">
                  {editingTemplate ? '编辑Prompt模板' : '创建Prompt模板'}
                </h3>
                <button
                  onClick={() => {
                    setIsModalOpen(false)
                    setEditingTemplate(null)
                    resetForm()
                  }}
                  className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">模板名称</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="input"
                      placeholder="如：投资群日报分析"
                      required
                    />
                  </div>
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
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">时间粒度</label>
                    <select
                      value={formData.time_granularity}
                      onChange={(e) => setFormData({ ...formData, time_granularity: e.target.value })}
                      className="select"
                    >
                      {Object.entries(granularityLabels).map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="label">分析风格</label>
                    <select
                      value={formData.style}
                      onChange={(e) => setFormData({ ...formData, style: e.target.value })}
                      className="select"
                    >
                      {Object.entries(styleLabels).map(([value, label]) => (
                        <option key={value} value={value}>{label}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="label">描述</label>
                  <input
                    type="text"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input"
                    placeholder="模板描述（可选）"
                  />
                </div>

                <div>
                  <label className="label">系统提示词</label>
                  <textarea
                    value={formData.system_prompt}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    className="input min-h-[80px] font-mono text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="label">用户提示词模板</label>
                  <p className="text-xs text-dark-500 mb-2">
                    可用变量: {'{chat_content}'}, {'{start_date}'}, {'{end_date}'}, {'{member_filter_text}'}
                  </p>
                  <textarea
                    value={formData.user_prompt_template}
                    onChange={(e) => setFormData({ ...formData, user_prompt_template: e.target.value })}
                    className="input min-h-[200px] font-mono text-sm"
                    placeholder="请分析以下群聊记录...&#10;&#10;聊天记录：&#10;{chat_content}"
                    required
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setIsModalOpen(false)
                      setEditingTemplate(null)
                      resetForm()
                    }}
                    className="btn btn-secondary flex-1"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary flex-1"
                    disabled={createMutation.isPending || updateMutation.isPending}
                  >
                    {editingTemplate
                      ? (updateMutation.isPending ? '保存中...' : '保存修改')
                      : (createMutation.isPending ? '创建中...' : '创建')
                    }
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* View Modal */}
      <AnimatePresence>
        {isViewModalOpen && viewingTemplate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIsViewModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="card max-w-3xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">{viewingTemplate.name}</h3>
                <button
                  onClick={() => setIsViewModalOpen(false)}
                  className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="label">系统提示词</label>
                  <pre className="code-block whitespace-pre-wrap">{viewingTemplate.system_prompt}</pre>
                </div>

                <div>
                  <label className="label">用户提示词模板</label>
                  <pre className="code-block whitespace-pre-wrap">{viewingTemplate.user_prompt_template}</pre>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => copyToClipboard(viewingTemplate.user_prompt_template)}
                    className="btn btn-primary flex-1 flex items-center justify-center gap-2"
                  >
                    <Copy className="w-4 h-4" />
                    复制模板
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Generate Modal */}
      <AnimatePresence>
        {isGenerateModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIsGenerateModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="card max-w-lg w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-accent-400" />
                  自动生成Prompt
                </h3>
                <button
                  onClick={() => setIsGenerateModalOpen(false)}
                  className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="label">群组类型</label>
                  <select
                    value={generateForm.group_type}
                    onChange={(e) => setGenerateForm({ ...generateForm, group_type: e.target.value })}
                    className="select"
                  >
                    <option value="investment">投资群</option>
                    <option value="science">科普群</option>
                    <option value="learning">学习群</option>
                    <option value="technology">技术群</option>
                    <option value="health">健康群</option>
                  </select>
                </div>

                <div>
                  <label className="label">时间粒度</label>
                  <select
                    value={generateForm.time_granularity}
                    onChange={(e) => setGenerateForm({ ...generateForm, time_granularity: e.target.value })}
                    className="select"
                  >
                    {Object.entries(granularityLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">自定义需求（可选）</label>
                  <textarea
                    value={generateForm.custom_requirements}
                    onChange={(e) => setGenerateForm({ ...generateForm, custom_requirements: e.target.value })}
                    className="input min-h-[80px]"
                    placeholder="描述您的特定分析需求..."
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setIsGenerateModalOpen(false)}
                    className="btn btn-secondary flex-1"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    className="btn btn-accent flex-1 flex items-center justify-center gap-2"
                    disabled={generateMutation.isPending}
                  >
                    <Sparkles className="w-4 h-4" />
                    {generateMutation.isPending ? '生成中...' : '生成Prompt'}
                  </button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

