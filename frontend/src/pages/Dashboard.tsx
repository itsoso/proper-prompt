import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Users,
  FileText,
  BarChart3,
  Zap,
  TrendingUp,
  Clock,
  Activity,
} from 'lucide-react'
import { api } from '../utils/api'
import { debugLog } from '../utils/debug'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  trend?: string
  color: 'primary' | 'accent' | 'success' | 'warning'
}

function StatCard({ title, value, icon: Icon, trend, color }: StatCardProps) {
  const colorClasses = {
    primary: 'from-primary-500/20 to-primary-600/20 border-primary-500/30',
    accent: 'from-accent-500/20 to-accent-600/20 border-accent-500/30',
    success: 'from-green-500/20 to-green-600/20 border-green-500/30',
    warning: 'from-yellow-500/20 to-yellow-600/20 border-yellow-500/30',
  }

  const iconColorClasses = {
    primary: 'text-primary-400',
    accent: 'text-accent-400',
    success: 'text-green-400',
    warning: 'text-yellow-400',
  }

  return (
    <motion.div
      className={`card bg-gradient-to-br ${colorClasses[color]} border`}
      whileHover={{ scale: 1.02 }}
      transition={{ type: 'spring', stiffness: 300 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-dark-400 text-sm">{title}</p>
          <p className="text-3xl font-bold text-white mt-2">{value}</p>
          {trend && (
            <div className="flex items-center gap-1 mt-2 text-green-400 text-sm">
              <TrendingUp className="w-4 h-4" />
              <span>{trend}</span>
            </div>
          )}
        </div>
        <div className={`p-3 rounded-xl bg-dark-800/50 ${iconColorClasses[color]}`}>
          <Icon className="w-6 h-6" />
        </div>
      </div>
    </motion.div>
  )
}

export default function Dashboard() {
  // Fetch stats
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      debugLog.debug('Fetching health status', undefined, 'Dashboard')
      const response = await api.health()
      return response.data
    },
    refetchInterval: 30000,
  })

  const { data: groupsData } = useQuery({
    queryKey: ['groups', { size: 1 }],
    queryFn: async () => {
      const response = await api.groups.list({ size: 1 })
      return response.data
    },
  })

  const { data: templatesData } = useQuery({
    queryKey: ['templates'],
    queryFn: async () => {
      const response = await api.prompts.templates.list()
      return response.data
    },
  })

  const { data: executionsData } = useQuery({
    queryKey: ['executions', { limit: 100 }],
    queryFn: async () => {
      const response = await api.prompts.executions.list()
      return response.data
    },
  })

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Welcome section */}
      <motion.div variants={itemVariants} className="card glow-primary">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold gradient-text">欢迎使用 Proper Prompts</h2>
            <p className="text-dark-400 mt-2">
              智能群聊分析与Prompt管理系统，帮助您高效分析群聊内容
            </p>
          </div>
          <div className="hidden md:flex items-center gap-4">
            <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-green-500/20 border border-green-500/30">
              <Activity className="w-5 h-5 text-green-400" />
              <span className="text-green-300">
                {healthData?.status === 'healthy' ? '系统运行正常' : '检查中...'}
              </span>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Stats grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="管理群组"
          value={groupsData?.total || 0}
          icon={Users}
          color="primary"
        />
        <StatCard
          title="Prompt模板"
          value={templatesData?.length || 0}
          icon={FileText}
          color="accent"
        />
        <StatCard
          title="执行次数"
          value={executionsData?.length || 0}
          icon={BarChart3}
          trend="+12% 本周"
          color="success"
        />
        <StatCard
          title="API调用"
          value="1,234"
          icon={Zap}
          trend="+8% 今日"
          color="warning"
        />
      </motion.div>

      {/* Quick actions and recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <motion.div variants={itemVariants} className="card">
          <h3 className="text-lg font-semibold text-white mb-4">快速操作</h3>
          <div className="grid grid-cols-2 gap-3">
            <button className="btn btn-primary flex items-center justify-center gap-2">
              <BarChart3 className="w-4 h-4" />
              快速分析
            </button>
            <button className="btn btn-secondary flex items-center justify-center gap-2">
              <FileText className="w-4 h-4" />
              新建模板
            </button>
            <button className="btn btn-secondary flex items-center justify-center gap-2">
              <Users className="w-4 h-4" />
              添加群组
            </button>
            <button className="btn btn-accent flex items-center justify-center gap-2">
              <Zap className="w-4 h-4" />
              Prompt评测
            </button>
          </div>
        </motion.div>

        {/* Recent Activity */}
        <motion.div variants={itemVariants} className="card">
          <h3 className="text-lg font-semibold text-white mb-4">最近活动</h3>
          <div className="space-y-3">
            {[
              { action: '分析完成', target: '投资讨论群', time: '5分钟前', status: 'success' },
              { action: '创建模板', target: '学习群日报模板', time: '1小时前', status: 'info' },
              { action: 'API调用', target: 'chatlog集成', time: '2小时前', status: 'warning' },
              { action: '评测完成', target: '3个Prompt对比', time: '3小时前', status: 'success' },
            ].map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between py-2 border-b border-dark-700 last:border-0"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full ${
                      activity.status === 'success'
                        ? 'bg-green-500'
                        : activity.status === 'warning'
                        ? 'bg-yellow-500'
                        : 'bg-primary-500'
                    }`}
                  />
                  <div>
                    <p className="text-white text-sm">{activity.action}</p>
                    <p className="text-dark-400 text-xs">{activity.target}</p>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-dark-500 text-xs">
                  <Clock className="w-3 h-3" />
                  {activity.time}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Feature highlights */}
      <motion.div variants={itemVariants}>
        <h3 className="text-lg font-semibold text-white mb-4">核心功能</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              title: '智能群聊分析',
              description: '支持投资群、科普群、学习群等多种类型，自动生成专属分析Prompt',
              color: 'primary',
            },
            {
              title: 'Prompt评测系统',
              description: '对同一需求生成多个Prompt，通过A/B测试评估效果',
              color: 'accent',
            },
            {
              title: '开放API集成',
              description: '与Browser-LLM-Orchestrator、chatlog、health-llm-driven无缝集成',
              color: 'success',
            },
          ].map((feature, index) => (
            <div
              key={index}
              className={`p-6 rounded-xl bg-gradient-to-br border
                ${feature.color === 'primary' 
                  ? 'from-primary-500/10 to-transparent border-primary-500/20' 
                  : feature.color === 'accent'
                  ? 'from-accent-500/10 to-transparent border-accent-500/20'
                  : 'from-green-500/10 to-transparent border-green-500/20'
                }
              `}
            >
              <h4 className="font-semibold text-white">{feature.title}</h4>
              <p className="text-dark-400 text-sm mt-2">{feature.description}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </motion.div>
  )
}

