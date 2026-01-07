import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { Plus, Search, Edit2, Trash2, Users, X } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../utils/api'
import { debugLog } from '../utils/debug'

interface Group {
  id: number
  external_id: string
  name: string
  type: string
  description: string | null
  member_count: number
  is_active: boolean
  created_at: string
}

const groupTypeLabels: Record<string, string> = {
  investment: '投资群',
  science: '科普群',
  learning: '学习群',
  technology: '技术群',
  lifestyle: '生活群',
  news: '新闻群',
  entertainment: '娱乐群',
  health: '健康群',
  business: '商务群',
  custom: '自定义',
}

const groupTypeColors: Record<string, string> = {
  investment: 'badge-primary',
  science: 'badge-accent',
  learning: 'badge-success',
  technology: 'bg-blue-500/20 text-blue-300 border border-blue-500/30',
  health: 'bg-pink-500/20 text-pink-300 border border-pink-500/30',
  custom: 'bg-gray-500/20 text-gray-300 border border-gray-500/30',
}

export default function GroupsPage() {
  const queryClient = useQueryClient()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedType, setSelectedType] = useState<string>('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingGroup, setEditingGroup] = useState<Group | null>(null)

  // Form state
  const [formData, setFormData] = useState({
    external_id: '',
    name: '',
    type: 'custom',
    description: '',
    member_count: 0,
  })

  // Fetch groups
  const { data: groupsData, isLoading } = useQuery({
    queryKey: ['groups', { search: searchTerm, type: selectedType }],
    queryFn: async () => {
      debugLog.debug('Fetching groups', { search: searchTerm, type: selectedType }, 'GroupsPage')
      const response = await api.groups.list({
        search: searchTerm || undefined,
        type: selectedType || undefined,
        size: 50,
      })
      return response.data
    },
  })

  // Create group mutation
  const createMutation = useMutation({
    mutationFn: (data: typeof formData) => api.groups.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      toast.success('群组创建成功')
      setIsModalOpen(false)
      resetForm()
    },
    onError: (error: Error) => {
      toast.error(`创建失败: ${error.message}`)
    },
  })

  // Update group mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<typeof formData> }) =>
      api.groups.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      toast.success('群组更新成功')
      setIsModalOpen(false)
      setEditingGroup(null)
      resetForm()
    },
    onError: (error: Error) => {
      toast.error(`更新失败: ${error.message}`)
    },
  })

  // Delete group mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.groups.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] })
      toast.success('群组删除成功')
    },
    onError: (error: Error) => {
      toast.error(`删除失败: ${error.message}`)
    },
  })

  const resetForm = () => {
    setFormData({
      external_id: '',
      name: '',
      type: 'custom',
      description: '',
      member_count: 0,
    })
  }

  const openEditModal = (group: Group) => {
    setEditingGroup(group)
    setFormData({
      external_id: group.external_id,
      name: group.name,
      type: group.type,
      description: group.description || '',
      member_count: group.member_count,
    })
    setIsModalOpen(true)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingGroup) {
      updateMutation.mutate({ id: editingGroup.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">群组管理</h2>
          <p className="text-dark-400 mt-1">管理您的群聊群组，设置群组类型以获得专属Prompt</p>
        </div>
        <button
          onClick={() => {
            setEditingGroup(null)
            resetForm()
            setIsModalOpen(true)
          }}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          添加群组
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-dark-400" />
            <input
              type="text"
              placeholder="搜索群组名称..."
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
            <option value="">全部类型</option>
            {Object.entries(groupTypeLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Groups List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <AnimatePresence>
          {isLoading ? (
            // Loading skeleton
            [...Array(6)].map((_, i) => (
              <div key={i} className="card animate-pulse">
                <div className="h-6 bg-dark-700 rounded w-3/4 mb-4" />
                <div className="h-4 bg-dark-700 rounded w-1/2 mb-2" />
                <div className="h-4 bg-dark-700 rounded w-full" />
              </div>
            ))
          ) : groupsData?.items?.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <Users className="w-16 h-16 mx-auto text-dark-600 mb-4" />
              <p className="text-dark-400">暂无群组，点击上方按钮添加</p>
            </div>
          ) : (
            groupsData?.items?.map((group: Group) => (
              <motion.div
                key={group.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="card hover:border-primary-500/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-white">{group.name}</h3>
                    <p className="text-xs text-dark-500 font-mono">{group.external_id}</p>
                  </div>
                  <span className={clsx('badge', groupTypeColors[group.type] || groupTypeColors.custom)}>
                    {groupTypeLabels[group.type] || group.type}
                  </span>
                </div>
                
                {group.description && (
                  <p className="text-dark-400 text-sm mb-3 line-clamp-2">{group.description}</p>
                )}
                
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-1 text-dark-400">
                    <Users className="w-4 h-4" />
                    <span>{group.member_count} 成员</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openEditModal(group)}
                      className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => {
                        if (confirm('确定要删除此群组吗？')) {
                          deleteMutation.mutate(group.id)
                        }
                      }}
                      className="p-2 rounded-lg hover:bg-red-500/20 text-dark-400 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Modal */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
            onClick={() => setIsModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="card max-w-lg w-full"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-semibold text-white">
                  {editingGroup ? '编辑群组' : '添加群组'}
                </h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="p-2 rounded-lg hover:bg-dark-700 text-dark-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="label">外部ID</label>
                  <input
                    type="text"
                    value={formData.external_id}
                    onChange={(e) => setFormData({ ...formData, external_id: e.target.value })}
                    className="input"
                    placeholder="如: wechat_group_123"
                    required
                    disabled={!!editingGroup}
                  />
                </div>

                <div>
                  <label className="label">群组名称</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="input"
                    placeholder="输入群组名称"
                    required
                  />
                </div>

                <div>
                  <label className="label">群组类型</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    className="select"
                  >
                    {Object.entries(groupTypeLabels).map(([value, label]) => (
                      <option key={value} value={value}>{label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="label">成员数量</label>
                  <input
                    type="number"
                    value={formData.member_count}
                    onChange={(e) => setFormData({ ...formData, member_count: parseInt(e.target.value) || 0 })}
                    className="input"
                    min="0"
                  />
                </div>

                <div>
                  <label className="label">描述</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    className="input min-h-[80px]"
                    placeholder="群组描述（可选）"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="btn btn-secondary flex-1"
                  >
                    取消
                  </button>
                  <button
                    type="submit"
                    className="btn btn-primary flex-1"
                    disabled={createMutation.isPending || updateMutation.isPending}
                  >
                    {createMutation.isPending || updateMutation.isPending ? '保存中...' : '保存'}
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

