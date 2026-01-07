import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import { Scale, Trophy, BarChart2, Clock } from 'lucide-react'
import { api } from '../utils/api'
import { debugLog } from '../utils/debug'

interface Evaluation {
  id: number
  name: string
  description: string | null
  execution_ids: number[]
  criteria: Record<string, number>
  scores: Record<string, Record<string, number>>
  winner_execution_id: number | null
  evaluator_notes: string | null
  auto_evaluated: boolean
  created_at: string
}

export default function EvaluationsPage() {
  // Fetch evaluations
  const { data: evaluations, isLoading } = useQuery({
    queryKey: ['evaluations'],
    queryFn: async () => {
      debugLog.debug('Fetching evaluations', undefined, 'EvaluationsPage')
      const response = await api.evaluations.list()
      return response.data
    },
  })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Prompt评测</h2>
          <p className="text-dark-400 mt-1">对比不同Prompt的效果，选出最佳方案</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-gradient-to-br from-primary-500/20 to-primary-600/20 border-primary-500/30">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-primary-500/20">
              <Scale className="w-6 h-6 text-primary-400" />
            </div>
            <div>
              <p className="text-dark-400 text-sm">总评测次数</p>
              <p className="text-2xl font-bold text-white">{evaluations?.length || 0}</p>
            </div>
          </div>
        </div>
        <div className="card bg-gradient-to-br from-accent-500/20 to-accent-600/20 border-accent-500/30">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-accent-500/20">
              <Trophy className="w-6 h-6 text-accent-400" />
            </div>
            <div>
              <p className="text-dark-400 text-sm">自动评测</p>
              <p className="text-2xl font-bold text-white">
                {evaluations?.filter((e: Evaluation) => e.auto_evaluated).length || 0}
              </p>
            </div>
          </div>
        </div>
        <div className="card bg-gradient-to-br from-green-500/20 to-green-600/20 border-green-500/30">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-green-500/20">
              <BarChart2 className="w-6 h-6 text-green-400" />
            </div>
            <div>
              <p className="text-dark-400 text-sm">平均对比数</p>
              <p className="text-2xl font-bold text-white">
                {evaluations?.length
                  ? (evaluations.reduce((acc: number, e: Evaluation) => acc + e.execution_ids.length, 0) / evaluations.length).toFixed(1)
                  : 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Evaluations List */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">评测历史</h3>
        
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse p-4 bg-dark-700 rounded-lg">
                <div className="h-5 bg-dark-600 rounded w-1/3 mb-2" />
                <div className="h-4 bg-dark-600 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : evaluations?.length === 0 ? (
          <div className="text-center py-12">
            <Scale className="w-16 h-16 mx-auto text-dark-600 mb-4" />
            <p className="text-dark-400">暂无评测记录</p>
            <p className="text-dark-500 text-sm mt-1">执行Prompt后可以进行效果评测</p>
          </div>
        ) : (
          <div className="space-y-4">
            {evaluations?.map((evaluation: Evaluation) => (
              <motion.div
                key={evaluation.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-dark-700/50 rounded-lg border border-dark-600 hover:border-primary-500/50 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-white">{evaluation.name}</h4>
                    {evaluation.description && (
                      <p className="text-dark-400 text-sm mt-1">{evaluation.description}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {evaluation.auto_evaluated && (
                      <span className="badge badge-accent">自动评测</span>
                    )}
                    {evaluation.winner_execution_id && (
                      <span className="badge badge-success flex items-center gap-1">
                        <Trophy className="w-3 h-3" />
                        胜出: #{evaluation.winner_execution_id}
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 flex items-center gap-4 text-sm text-dark-400">
                  <div className="flex items-center gap-1">
                    <BarChart2 className="w-4 h-4" />
                    <span>{evaluation.execution_ids.length} 个Prompt对比</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{formatDate(evaluation.created_at)}</span>
                  </div>
                </div>

                {/* Scores */}
                {evaluation.scores && Object.keys(evaluation.scores).length > 0 && (
                  <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(evaluation.criteria).map(([criterion, weight]) => (
                      <div key={criterion} className="text-center">
                        <p className="text-xs text-dark-500 mb-1">
                          {criterion} ({(weight * 100).toFixed(0)}%)
                        </p>
                        <div className="flex justify-center gap-2">
                          {Object.entries(evaluation.scores).map(([execId, scores]) => (
                            <span
                              key={execId}
                              className={`text-sm font-medium ${
                                evaluation.winner_execution_id?.toString() === execId
                                  ? 'text-green-400'
                                  : 'text-dark-300'
                              }`}
                            >
                              {(scores as Record<string, number>)[criterion]?.toFixed(1) || '-'}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {evaluation.evaluator_notes && (
                  <div className="mt-4 p-3 bg-dark-800 rounded-lg text-sm text-dark-300">
                    {evaluation.evaluator_notes}
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

