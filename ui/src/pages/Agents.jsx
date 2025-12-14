import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { User, Search, Brain, Shield, Activity, CheckCircle, AlertCircle, Terminal, X } from 'lucide-react'
import { getAgentStatus } from '../services/api'
import AgentLogs from '../components/AgentLogs'

const Agents = () => {
  const [selectedAgentForLogs, setSelectedAgentForLogs] = useState(null)
  const [agents, setAgents] = useState([
    {
      id: 'red-team',
      name: 'Red Team Agent',
      role: 'Attack Generation',
      icon: User,
      color: 'danger',
      description: 'Generates realistic multi-stage cyberattack scenarios using MITRE ATT&CK framework',
      status: 'active',
      lastActivity: new Date(),
      metrics: {
        tasksCompleted: 1247,
        avgResponseTime: '2.3s',
        successRate: 0.98,
      },
    },
    {
      id: 'detection',
      name: 'Detection Agent',
      role: 'Incident Detection',
      icon: Search,
      color: 'warning',
      description: 'LLM-powered incident detection and analysis from synthetic telemetry',
      status: 'active',
      lastActivity: new Date(),
      metrics: {
        tasksCompleted: 1892,
        avgResponseTime: '1.8s',
        successRate: 0.95,
      },
    },
    {
      id: 'rag',
      name: 'RAG Agent',
      role: 'Context Retrieval',
      icon: Brain,
      color: 'primary',
      description: 'Retrieves relevant security runbooks, threat intelligence, and past incidents',
      status: 'active',
      lastActivity: new Date(),
      metrics: {
        tasksCompleted: 1563,
        avgResponseTime: '0.5s',
        successRate: 0.99,
      },
    },
    {
      id: 'remediation',
      name: 'Remediation Agent',
      role: 'Action Planning',
      icon: Shield,
      color: 'success',
      description: 'AI-driven action recommendations grounded in security best practices',
      status: 'active',
      lastActivity: new Date(),
      metrics: {
        tasksCompleted: 1345,
        avgResponseTime: '2.1s',
        successRate: 0.97,
      },
    },
  ])

  useEffect(() => {
    loadAgentStatus()
    const interval = setInterval(loadAgentStatus, 15000) // Refresh every 15 seconds
    return () => clearInterval(interval)
  }, [])

  const loadAgentStatus = async () => {
    try {
      const status = await getAgentStatus()
      // Update agents with real status
      setAgents(prev => prev.map(agent => {
        const agentKey = agent.id === 'red-team' ? 'redTeam' : 
                        agent.id === 'detection' ? 'detection' :
                        agent.id === 'rag' ? 'rag' : 'remediation'
        const agentStatus = status[agentKey]
        return {
          ...agent,
          status: agentStatus?.status || 'idle',
          lastActivity: agentStatus?.lastActivity ? new Date(agentStatus.lastActivity) : new Date(),
          metrics: {
            tasksCompleted: agentStatus?.tasksCompleted || 0,
            avgResponseTime: agent.metrics.avgResponseTime, // Keep existing
            successRate: agent.metrics.successRate, // Keep existing
          }
        }
      }))
    } catch (error) {
      console.error('Failed to load agent status:', error)
    }
  }

  const getStatusIcon = (status) => {
    return status === 'active' ? (
      <CheckCircle className="w-5 h-5 text-success-600" />
    ) : (
      <AlertCircle className="w-5 h-5 text-gray-400" />
    )
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">Agents</h1>
        <p className="text-gray-600 text-lg">Monitor and manage your CrewAI agents</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {agents.map((agent, index) => {
          const Icon = agent.icon
          const colorClasses = {
            danger: 'bg-danger-50 text-danger-600 border-danger-200',
            warning: 'bg-yellow-50 text-yellow-600 border-yellow-200',
            primary: 'bg-primary-50 text-primary-600 border-primary-200',
            success: 'bg-success-50 text-success-600 border-success-200',
          }

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              whileHover={{ y: -4 }}
              className="card hover:shadow-xl transition-all duration-300 group cursor-pointer border-l-4 border-l-transparent hover:border-l-primary-500"
            >
              <div className="flex items-start justify-between mb-5">
                <div className="flex items-center space-x-4">
                  <div className={`
                    p-4 rounded-xl border-2 transition-all duration-200
                    ${colorClasses[agent.color]}
                    group-hover:scale-110 group-hover:shadow-lg
                  `}>
                    <Icon className="w-7 h-7" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-1">{agent.name}</h3>
                    <p className="text-sm text-gray-600 font-medium">{agent.role}</p>
                  </div>
                </div>
                {getStatusIcon(agent.status)}
              </div>

              <p className="text-sm text-gray-600 mb-5 leading-relaxed">{agent.description}</p>

              <div className="space-y-3 pt-5 border-t border-gray-100">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Tasks Completed</span>
                  <span className="font-semibold text-gray-900">
                    {agent.metrics.tasksCompleted.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Avg Response Time</span>
                  <span className="font-semibold text-gray-900">
                    {agent.metrics.avgResponseTime}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Success Rate</span>
                  <span className="font-semibold text-success-600">
                    {(agent.metrics.successRate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center justify-between text-xs text-gray-500 w-full">
                    <span>Last Activity</span>
                    <span>
                      {agent.lastActivity 
                        ? (typeof agent.lastActivity === 'string' 
                            ? new Date(agent.lastActivity) 
                            : agent.lastActivity
                          ).toLocaleTimeString()
                        : 'Never'
                      }
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedAgentForLogs(agent.id === 'red-team' ? 'red_team' : agent.id)}
                  className="mt-3 btn btn-secondary w-full px-4 py-2.5 text-sm font-semibold hover:bg-gray-100"
                >
                  <Terminal className="w-4 h-4 mr-2" />
                  View Logs
                </button>
              </div>
            </motion.div>
          )
        })}
      </div>

      {/* Agent Logs Section */}
      <div className="mt-6">
        {selectedAgentForLogs ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-gray-900">
                Logs: {agents.find(a => (a.id === 'red-team' ? 'red_team' : a.id) === selectedAgentForLogs)?.name || selectedAgentForLogs}
              </h2>
              <button
                onClick={() => setSelectedAgentForLogs(null)}
                className="btn btn-secondary px-3 py-2"
              >
                <X className="w-4 h-4 mr-2" />
                Close Logs
              </button>
            </div>
            <AgentLogs agent={selectedAgentForLogs} autoRefresh={true} />
          </div>
        ) : (
          <AgentLogs agent={null} autoRefresh={true} />
        )}
      </div>
    </div>
  )
}

export default Agents

