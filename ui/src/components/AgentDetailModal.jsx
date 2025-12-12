import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, User, Search, Brain, Shield, Activity, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { getAgentLogs } from '../services/api'

const AgentDetailModal = ({ agent, onClose, episodeData = null }) => {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)

  // Safety check - if no agent, don't render
  if (!agent) {
    return null
  }

  useEffect(() => {
    if (agent && agent.id) {
      loadLogs()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent])

  const loadLogs = async () => {
    try {
      // Map agent IDs from UI to API agent keys
      const agentKeyMap = {
        'red-team': 'red_team',
        'detection': 'detection',
        'rag': 'rag',
        'remediation': 'remediation',
        'rl': 'rl_agent',
        'telemetry': null, // Telemetry doesn't have logs in API
      }
      
      const agentKey = agentKeyMap[agent.id]
      
      // Skip if agent doesn't have logs (like telemetry)
      if (!agentKey) {
        setLogs([])
        setLoading(false)
        return
      }
      
      const data = await getAgentLogs(agentKey, 50)
      setLogs(data.logs || [])
      setLoading(false)
    } catch (error) {
      console.error('Failed to load agent logs:', error)
      setLogs([])
      setLoading(false)
    }
  }

  const getAgentIcon = (id) => {
    const icons = {
      'red-team': User,
      'detection': Search,
      'rag': Brain,
      'remediation': Shield,
      'rl': Brain,
    }
    return icons[id] || Activity
  }

  const getAgentData = () => {
    if (!episodeData) return null

    const data = {
      'red-team': {
        title: 'Attack Scenario',
        content: episodeData.attack_scenario,
      },
      'detection': {
        title: 'Incident Report',
        content: episodeData.incident_report,
      },
      'rag': {
        title: 'RAG Context',
        content: episodeData.rag_context,
      },
      'remediation': {
        title: 'Remediation Plan',
        content: episodeData.remediation,
      },
      'rl': {
        title: 'RL Decision',
        content: episodeData.rl_decision,
      },
    }
    return data[agent.id] || null
  }

  const agentData = getAgentData()
  const Icon = getAgentIcon(agent.id)

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-gray-200/50"
        >
        {/* Header */}
        <div className="border-b border-gray-200/60 p-6 bg-gradient-to-r from-gray-50 to-gray-100/50 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`p-4 rounded-xl shadow-lg ${
              agent.color === 'danger' ? 'bg-gradient-to-br from-red-100 to-red-200 text-red-600' :
              agent.color === 'warning' ? 'bg-gradient-to-br from-yellow-100 to-yellow-200 text-yellow-600' :
              agent.color === 'primary' ? 'bg-gradient-to-br from-blue-100 to-blue-200 text-blue-600' :
              'bg-gradient-to-br from-green-100 to-green-200 text-green-600'
            }`}>
              <Icon className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-1">{agent.name || 'Agent'}</h2>
              <p className="text-sm text-gray-600 font-medium">{agent.role || 'Agent Role'}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-all duration-200 active:scale-95"
            aria-label="Close modal"
          >
            <X className="w-6 h-6 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Agent Description */}
          {agent.description && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
              <p className="text-gray-700">{agent.description}</p>
            </div>
          )}

          {/* Status */}
          {agent.status && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Status</h3>
              <div className="flex items-center space-x-2">
                {agent.status === 'active' ? (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-gray-400" />
                )}
                <span className="text-gray-700 capitalize">{agent.status}</span>
              </div>
            </div>
          )}

          {/* Metrics */}
          {agent.metrics && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Metrics</h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Tasks Completed</p>
                  <p className="text-2xl font-bold text-gray-900">{agent.metrics.tasksCompleted || 0}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Avg Response Time</p>
                  <p className="text-2xl font-bold text-gray-900">{agent.metrics.avgResponseTime || 'N/A'}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold text-green-600">
                    {agent.metrics.successRate ? `${(agent.metrics.successRate * 100).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Agent-Specific Data */}
          {agentData && agentData.content && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{agentData.title}</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                {agent.id === 'remediation' && agentData.content && (
                  <>
                    {agentData.content.recommended_action && (
                      <div className="mb-4">
                        <p className="text-sm font-medium text-gray-700 mb-2">Recommended Action:</p>
                        <span className="inline-block px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-semibold">
                          {agentData.content.recommended_action.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    )}
                    {agentData.content.options && agentData.content.options.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Action Options:</p>
                        <div className="space-y-2">
                          {agentData.content.options.map((opt, i) => (
                            <div key={i} className="bg-white p-3 rounded border border-gray-200">
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-medium text-gray-900">
                                  {opt.action?.replace('_', ' ').toUpperCase() || 'N/A'}
                                </span>
                                {opt.confidence && (
                                  <span className="text-xs text-gray-600">
                                    Confidence: {(opt.confidence * 100).toFixed(0)}%
                                  </span>
                                )}
                              </div>
                              {opt.description && (
                                <p className="text-sm text-gray-600">{opt.description}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                {agent.id === 'detection' && agentData.content && (
                  <div className="space-y-2">
                    <div>
                      <span className="text-sm font-medium text-gray-700">Severity: </span>
                      <span className="text-sm text-gray-900 capitalize">{agentData.content.severity}</span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-gray-700">Confidence: </span>
                      <span className="text-sm text-gray-900">{(agentData.content.confidence * 100).toFixed(1)}%</span>
                    </div>
                    {agentData.content.summary && (
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-1">Summary:</p>
                        <p className="text-sm text-gray-600">{agentData.content.summary}</p>
                      </div>
                    )}
                  </div>
                )}
                {agent.id === 'rl' && agentData.content && (
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Selected Action</p>
                      <p className="font-semibold text-gray-900">
                        {agentData.content.selected_action?.replace('_', ' ').toUpperCase()}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Mode</p>
                      <p className="font-semibold text-gray-900">
                        {agentData.content.is_exploration ? 'Exploration' : 'Exploitation'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Epsilon</p>
                      <p className="font-semibold text-gray-900">{agentData.content.epsilon?.toFixed(4)}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recent Logs */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Recent Activity</h3>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              </div>
            ) : logs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No recent activity</p>
                <p className="text-xs mt-1 text-gray-400">
                  {agent.id === 'telemetry' 
                    ? 'Telemetry logs are not captured separately'
                    : 'Start a simulation to see agent activity'
                  }
                </p>
              </div>
            ) : (
              <div className="bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-gray-100 font-mono text-sm rounded-lg p-4 max-h-64 overflow-y-auto shadow-inner">
                {logs.slice(-10).reverse().map((log, index) => (
                  <div key={log.id || index} className="py-1.5 border-b border-gray-700/50 last:border-0 hover:bg-gray-800/50 transition-colors">
                    <span className="text-gray-500 text-xs">
                      {log.timestamp 
                        ? format(
                            typeof log.timestamp === 'string' ? parseISO(log.timestamp) : new Date(log.timestamp),
                            'HH:mm:ss'
                          )
                        : '--:--:--'
                      }
                    </span>
                    <span className={`ml-2 px-2 py-0.5 rounded text-xs font-semibold ${
                      log.level === 'ERROR' ? 'bg-red-500 text-white' :
                      log.level === 'WARNING' ? 'bg-yellow-500 text-white' :
                      log.level === 'INFO' ? 'bg-blue-500 text-white' :
                      'bg-gray-500 text-white'
                    }`}>
                      {log.level}
                    </span>
                    <span className="ml-2 text-gray-200 break-words">{log.message}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200/60 p-6 bg-gradient-to-r from-gray-50 to-gray-100/50 flex items-center justify-end">
          <button
            onClick={onClose}
            className="btn btn-primary px-6 py-2.5 text-sm font-semibold"
          >
            Close
          </button>
        </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default AgentDetailModal

