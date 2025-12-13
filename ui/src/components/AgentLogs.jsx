import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Terminal, Filter, X, Download, RefreshCw, Search, Clock, AlertCircle, Info, AlertTriangle, Bug, ExternalLink } from 'lucide-react'
import { getAgentLogs, getLogDetails } from '../services/api'
import { format, parseISO, formatDistanceToNow } from 'date-fns'

const AgentLogs = ({ agent = null, autoRefresh = true, filterByLogId = null, filterBySimulationId = null }) => {
  const [logs, setLogs] = useState([])
  const [filteredLogs, setFilteredLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedAgent, setSelectedAgent] = useState(agent || 'all')
  const [logLevel, setLogLevel] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')
  const [timeRange, setTimeRange] = useState('all')
  const logsEndRef = useRef(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [groupByTime, setGroupByTime] = useState(false)
  const [selectedLog, setSelectedLog] = useState(null)
  const [showLogDetail, setShowLogDetail] = useState(false)
  const [selectedLogId, setSelectedLogId] = useState(filterByLogId)
  const [selectedSimulationId, setSelectedSimulationId] = useState(filterBySimulationId)
  const [groupByLogId, setGroupByLogId] = useState(false)

  const agents = [
    { id: 'all', name: 'All Agents', color: 'gray' },
    { id: 'red_team', name: 'Red Team', color: 'red' },
    { id: 'detection', name: 'Detection', color: 'yellow' },
    { id: 'rag', name: 'RAG', color: 'blue' },
    { id: 'remediation', name: 'Remediation', color: 'green' },
    { id: 'rl_agent', name: 'RL Agent', color: 'purple' },
    { id: 'orchestrator', name: 'Orchestrator', color: 'gray' },
  ]

  useEffect(() => {
    loadLogs()
    if (autoRefresh) {
      const interval = setInterval(loadLogs, 2000)
      return () => clearInterval(interval)
    }
  }, [selectedAgent, autoRefresh, filterBySimulationId])

  useEffect(() => {
    if (filterByLogId) {
      setSelectedLogId(filterByLogId)
    }
  }, [filterByLogId])

  useEffect(() => {
    if (filterBySimulationId) {
      setSelectedSimulationId(filterBySimulationId)
      console.log('[AgentLogs] Filtering by simulation_id:', filterBySimulationId)
    } else {
      setSelectedSimulationId(null)
    }
  }, [filterBySimulationId])

  useEffect(() => {
    filterLogs()
  }, [logs, logLevel, searchTerm, timeRange, selectedLogId, selectedSimulationId])

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [filteredLogs, autoScroll])

  const loadLogs = async () => {
    try {
      const agentParam = selectedAgent === 'all' ? null : selectedAgent
      const data = await getAgentLogs(agentParam, 1000)
      const newLogs = data.logs || []
      console.log(`[AgentLogs] Loaded ${newLogs.length} logs from API (agent: ${agentParam || 'all'}, filterBySimulationId: ${filterBySimulationId || 'none'})`)
      
      // Log sample of simulation_ids for debugging
      if (newLogs.length > 0) {
        const sampleSimIds = [...new Set(newLogs.map(l => l.simulation_id).filter(Boolean))].slice(0, 3)
        console.log(`[AgentLogs] Sample simulation_ids in logs:`, sampleSimIds)
      }
      
      setLogs(newLogs)
      setLoading(false)
    } catch (error) {
      console.error('[AgentLogs] Failed to load logs:', error)
      setLoading(false)
    }
  }

  const filterLogs = () => {
    let filtered = [...logs]

    // Filter by level
    if (logLevel !== 'all') {
      filtered = filtered.filter(log => log.level.toLowerCase() === logLevel.toLowerCase())
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.agent.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (log.id && log.id.toLowerCase().includes(searchTerm.toLowerCase()))
      )
    }

    // Filter by selected log ID
    if (selectedLogId) {
      filtered = filtered.filter(log => log.id === selectedLogId)
    }

    // Filter by simulation ID (from LogStreams)
    if (selectedSimulationId) {
      const beforeCount = filtered.length
      
      // Normalize the selected simulation ID - remove microseconds if present for matching
      // Format: sim_20251213_173541_123456 -> sim_20251213_173541
      const normalizeSimId = (simId) => {
        if (!simId) return null
        // Remove microseconds part (last 6 digits after final underscore)
        return simId.replace(/_\d{6}$/, '')
      }
      
      const normalizedSelectedId = normalizeSimId(selectedSimulationId)
      
      filtered = filtered.filter(log => {
        const logSimId = log.simulation_id
        if (!logSimId) return false
        
        // Try exact match first
        if (logSimId === selectedSimulationId) {
          return true
        }
        
        // Try normalized match (without microseconds)
        const normalizedLogId = normalizeSimId(logSimId)
        if (normalizedLogId === normalizedSelectedId) {
          return true
        }
        
        // Try prefix match (in case one is a prefix of the other)
        if (logSimId.startsWith(selectedSimulationId) || selectedSimulationId.startsWith(logSimId)) {
          return true
        }
        
        // Try normalized prefix match
        if (normalizedLogId && normalizedSelectedId) {
          if (normalizedLogId.startsWith(normalizedSelectedId) || normalizedSelectedId.startsWith(normalizedLogId)) {
            return true
          }
        }
        
        return false
      })
      
      console.log(`[AgentLogs] Filtered from ${beforeCount} to ${filtered.length} logs for simulation_id: "${selectedSimulationId}" (normalized: "${normalizedSelectedId}")`)
      
      if (filtered.length === 0 && beforeCount > 0) {
        const availableSimIds = [...new Set(logs.map(l => l.simulation_id).filter(Boolean))]
        const normalizedAvailable = [...new Set(availableSimIds.map(normalizeSimId).filter(Boolean))]
        console.warn(`[AgentLogs] No logs matched simulation_id="${selectedSimulationId}". Available simulation_ids:`, availableSimIds.slice(0, 5))
        console.warn(`[AgentLogs] Normalized available IDs:`, normalizedAvailable.slice(0, 5))
      }
    }

    // Filter by time range
    if (timeRange !== 'all') {
      const now = new Date()
      const cutoff = new Date()
      switch (timeRange) {
        case '5m':
          cutoff.setMinutes(now.getMinutes() - 5)
          break
        case '15m':
          cutoff.setMinutes(now.getMinutes() - 15)
          break
        case '1h':
          cutoff.setHours(now.getHours() - 1)
          break
        case '6h':
          cutoff.setHours(now.getHours() - 6)
          break
        case '24h':
          cutoff.setHours(now.getHours() - 24)
          break
      }
      filtered = filtered.filter(log => {
        const logDate = typeof log.timestamp === 'string' ? parseISO(log.timestamp) : new Date(log.timestamp)
        return logDate >= cutoff
      })
    }

    setFilteredLogs(filtered)
  }

  const getLogLevelIcon = (level) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'INFO':
        return <Info className="w-4 h-4 text-blue-500" />
      case 'DEBUG':
        return <Bug className="w-4 h-4 text-gray-500" />
      default:
        return <Info className="w-4 h-4 text-gray-500" />
    }
  }

  const getLogLevelColor = (level) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'INFO':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'DEBUG':
        return 'text-gray-600 bg-gray-50 border-gray-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getAgentColor = (agentName) => {
    const agentMap = {
      'red_team': { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
      'detection': { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300' },
      'rag': { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
      'remediation': { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300' },
      'rl_agent': { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-300' },
      'orchestrator': { bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-300' },
    }
    return agentMap[agentName] || { bg: 'bg-gray-100', text: 'text-gray-800', border: 'border-gray-300' }
  }

  const groupLogsByTime = (logs) => {
    const groups = {}
    logs.forEach(log => {
      const logDate = typeof log.timestamp === 'string' ? parseISO(log.timestamp) : new Date(log.timestamp)
      const dateKey = format(logDate, 'yyyy-MM-dd HH:mm')
      if (!groups[dateKey]) {
        groups[dateKey] = []
      }
      groups[dateKey].push(log)
    })
    return groups
  }

  const exportLogs = () => {
    const logText = filteredLogs.map(log => {
      const timestamp = log.timestamp 
        ? format(
            typeof log.timestamp === 'string' ? parseISO(log.timestamp) : new Date(log.timestamp),
            'yyyy-MM-dd HH:mm:ss.SSS'
          )
        : 'N/A'
      return `[${timestamp}] [${log.level}] [${log.agent}] ${log.message}`
    }).join('\n')
    
    const blob = new Blob([logText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `agent-logs-${selectedAgent}-${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const groupLogsById = (logs) => {
    const grouped = {}
    logs.forEach(log => {
      const logId = log.id || 'unknown'
      if (!grouped[logId]) {
        grouped[logId] = []
      }
      grouped[logId].push(log)
    })
    return grouped
  }

  const displayLogs = groupByLogId 
    ? groupLogsById(filteredLogs)
    : groupByTime 
      ? groupLogsByTime(filteredLogs) 
      : { 'all': filteredLogs }

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200/60 overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200/60 p-6 bg-gradient-to-r from-gray-50 to-gray-100/50">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 p-3 rounded-xl shadow-lg">
              <Terminal className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Agent Logs</h2>
              <p className="text-sm text-gray-600 font-medium">Real-time log streaming</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={loadLogs}
              className="btn btn-secondary px-4 py-2.5 text-sm font-semibold"
              title="Refresh logs"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
            <button
              onClick={exportLogs}
              className="btn btn-secondary px-4 py-2.5 text-sm font-semibold"
              title="Export logs"
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Filter Banner */}
          {(selectedLogId || selectedSimulationId) && (
            <div className="md:col-span-4">
              <div className="flex items-center justify-between bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-center space-x-2">
                  {selectedSimulationId ? (
                    <>
                      <span className="text-sm font-medium text-blue-900">Filtered by Simulation:</span>
                      <code className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded font-mono">
                        {selectedSimulationId === 'system' 
                          ? 'System Logs' 
                          : selectedSimulationId.replace('sim_', 'Simulation ').replace(/_/g, ' ').replace(/\s+\d{6}$/, '')
                        }
                      </code>
                    </>
                  ) : (
                    <>
                      <span className="text-sm font-medium text-blue-900">Filtered by Log ID:</span>
                      <code className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded font-mono">
                        {selectedLogId.substring(0, 8)}...
                      </code>
                    </>
                  )}
                  <span className="text-xs text-blue-700">
                    ({filteredLogs.length} log{filteredLogs.length !== 1 ? 's' : ''})
                  </span>
                </div>
                <button
                  onClick={() => {
                    setSelectedLogId(null)
                    setSelectedSimulationId(null)
                  }}
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium px-3 py-1 hover:bg-blue-100 rounded transition-colors"
                >
                  Clear Filter
                </button>
              </div>
            </div>
          )}
          
          {/* Agent Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Agent</label>
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {agents.map((agent) => (
                <option key={agent.id} value={agent.id}>{agent.name}</option>
              ))}
            </select>
          </div>

          {/* Level Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Log Level</label>
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Levels</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
              <option value="info">Info</option>
              <option value="debug">Debug</option>
            </select>
          </div>

          {/* Time Range Filter */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Time Range</label>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">All Time</option>
              <option value="5m">Last 5 minutes</option>
              <option value="15m">Last 15 minutes</option>
              <option value="1h">Last hour</option>
              <option value="6h">Last 6 hours</option>
              <option value="24h">Last 24 hours</option>
            </select>
          </div>

          {/* Search */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search logs..."
                className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Options */}
        <div className="flex items-center space-x-4 mt-4">
          <label className="flex items-center space-x-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Auto-scroll</span>
          </label>
          <label className="flex items-center space-x-2 text-sm text-gray-700">
            <input
              type="checkbox"
              checked={groupByTime}
              onChange={(e) => {
                setGroupByTime(e.target.checked)
                if (e.target.checked) setGroupByLogId(false)
              }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Group by time</span>
          </label>
          <label className="flex items-center space-x-2 text-sm text-gray-700 cursor-pointer">
            <input
              type="checkbox"
              checked={groupByLogId}
              onChange={(e) => {
                setGroupByLogId(e.target.checked)
                if (e.target.checked) setGroupByTime(false)
              }}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span>Group by Log ID</span>
          </label>
          {autoRefresh && (
            <div className="flex items-center space-x-2 text-sm text-green-600">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span>Live streaming (2s refresh)</span>
            </div>
          )}
        </div>
      </div>

      {/* Logs Display - CloudWatch Style */}
      <div className="bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-gray-100 font-mono text-sm h-[600px] overflow-y-auto shadow-inner">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
              <p className="text-gray-400">Loading logs...</p>
            </div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 py-12">
            <Terminal className="w-12 h-12 mx-auto mb-4 text-gray-600" />
            <p className="text-lg font-medium">No logs found</p>
            <p className="text-sm mt-2 text-gray-400">
              {logs.length === 0 
                ? "Start a simulation to see agent logs"
                : selectedSimulationId
                  ? `No logs found for simulation: ${selectedSimulationId}. Total logs available: ${logs.length}`
                  : "Try adjusting your filters"
              }
            </p>
            {selectedSimulationId && logs.length > 0 && (
              <div className="mt-4 text-xs text-gray-500">
                <p>Available simulation_ids in logs:</p>
                <code className="block mt-2 p-2 bg-gray-100 rounded text-left max-w-md mx-auto">
                  {[...new Set(logs.map(l => l.simulation_id).filter(Boolean))].slice(0, 5).join(', ')}
                </code>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 space-y-1">
            {Object.entries(displayLogs).map(([groupKey, timeLogs]) => (
              <div key={groupKey}>
                {groupByTime && (
                  <div className="sticky top-0 bg-gray-800 text-gray-400 text-xs px-2 py-1 mb-2 border-b border-gray-700">
                    {groupKey}
                  </div>
                )}
                {groupByLogId && (
                  <div className="sticky top-0 bg-gray-800/90 backdrop-blur-sm text-gray-300 text-xs px-3 py-2 mb-2 border-b border-gray-700 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-blue-400">Log ID:</span>
                      <code className="font-mono text-white">{groupKey.substring(0, 8)}...</code>
                      <span className="text-gray-500">({timeLogs.length} log{timeLogs.length !== 1 ? 's' : ''})</span>
                    </div>
                    <button
                      onClick={() => {
                        setSelectedLogId(groupKey)
                        setGroupByLogId(false)
                      }}
                      className="text-blue-400 hover:text-blue-300 text-xs"
                    >
                      Filter by this ID
                    </button>
                  </div>
                )}
                {timeLogs.map((log, index) => {
                  const logDate = log.timestamp 
                    ? (typeof log.timestamp === 'string' ? parseISO(log.timestamp) : new Date(log.timestamp))
                    : new Date()
                  const agentColors = getAgentColor(log.agent)
                  const logId = log.id || `${log.timestamp}-${index}`
                  
                  return (
                    <div
                      key={`${logId}-${index}`}
                      onClick={() => {
                        setSelectedLog(log)
                        setShowLogDetail(true)
                      }}
                      className="flex items-start space-x-3 py-1.5 px-2 hover:bg-gray-800 rounded group cursor-pointer transition-colors"
                    >
                      {/* Log ID (CloudWatch style) - Always visible and clickable */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setSelectedLogId(logId)
                          setGroupByLogId(false)
                        }}
                        className="text-blue-400 hover:text-blue-300 text-xs flex-shrink-0 w-20 font-mono text-left hover:underline transition-colors"
                        title={`Click to filter by Log ID: ${logId}`}
                      >
                        {logId.substring(0, 8)}
                      </button>
                      
                      {/* Timestamp */}
                      <span className="text-gray-500 text-xs flex-shrink-0 w-32 font-mono">
                        {format(logDate, 'HH:mm:ss.SSS')}
                      </span>
                      
                      {/* Level Icon */}
                      <div className="flex-shrink-0 mt-0.5">
                        {getLogLevelIcon(log.level)}
                      </div>
                      
                      {/* Level Badge */}
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold flex-shrink-0 ${getLogLevelColor(log.level)}`}>
                        {log.level}
                      </span>
                      
                      {/* Agent Badge */}
                      <span className={`px-2 py-0.5 rounded text-xs font-medium flex-shrink-0 border ${agentColors.bg} ${agentColors.text} ${agentColors.border}`}>
                        {log.agent}
                      </span>
                      
                      {/* Message */}
                      <span className="text-gray-200 flex-1 break-words">
                        {log.message}
                      </span>
                      
                      {/* Relative Time */}
                      <span className="text-gray-600 text-xs flex-shrink-0 w-24 text-right">
                        {formatDistanceToNow(logDate, { addSuffix: true })}
                      </span>
                      
                      {/* Click indicator */}
                      <ExternalLink className="w-3 h-3 text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                    </div>
                  )
                })}
              </div>
            ))}
            <div ref={logsEndRef} />
          </div>
        )}
      </div>

      {/* Log Detail Modal */}
      {showLogDetail && selectedLog && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
          onClick={() => {
            setShowLogDetail(false)
            setSelectedLog(null)
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-gradient-to-br from-gray-900 via-gray-900 to-gray-800 text-gray-100 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col border border-gray-700/50"
          >
            {/* Modal Header */}
            <div className="border-b border-gray-700/50 p-6 bg-gray-800/50 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white mb-1">Log Details</h3>
                <p className="text-sm text-gray-400 font-mono bg-gray-800/50 px-3 py-1 rounded-lg inline-block">
                  {selectedLog.id}
                </p>
              </div>
              <button
                onClick={() => {
                  setShowLogDetail(false)
                  setSelectedLog(null)
                }}
                className="p-2 hover:bg-gray-700 rounded-lg transition-all duration-200 active:scale-95"
                aria-label="Close modal"
              >
                <X className="w-6 h-6 text-gray-400 hover:text-white" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6 font-mono text-sm">
              <div className="space-y-4">
                {/* Log ID */}
                <div>
                  <span className="text-gray-500">Log ID:</span>
                  <span className="ml-2 text-gray-300">{selectedLog.id}</span>
                </div>

                {/* Timestamp */}
                <div>
                  <span className="text-gray-500">Timestamp:</span>
                  <span className="ml-2 text-gray-300">
                    {selectedLog.timestamp 
                      ? format(
                          typeof selectedLog.timestamp === 'string' 
                            ? parseISO(selectedLog.timestamp) 
                            : new Date(selectedLog.timestamp),
                          'yyyy-MM-dd HH:mm:ss.SSS'
                        )
                      : 'N/A'
                    }
                  </span>
                </div>

                {/* Level */}
                <div>
                  <span className="text-gray-500">Level:</span>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${getLogLevelColor(selectedLog.level)}`}>
                    {selectedLog.level}
                  </span>
                </div>

                {/* Agent */}
                <div>
                  <span className="text-gray-500">Agent:</span>
                  <span className={`ml-2 px-2 py-1 rounded text-xs ${getAgentColor(selectedLog.agent).bg} ${getAgentColor(selectedLog.agent).text}`}>
                    {selectedLog.agent}
                  </span>
                </div>

                {/* Message */}
                <div>
                  <span className="text-gray-500 block mb-2">Message:</span>
                  <div className="bg-gray-800 p-4 rounded border border-gray-700">
                    <pre className="whitespace-pre-wrap text-gray-200">{selectedLog.message || selectedLog.raw_message || 'N/A'}</pre>
                  </div>
                </div>

                {/* Additional Details */}
                {(selectedLog.module || selectedLog.funcName || selectedLog.lineno) && (
                  <div>
                    <span className="text-gray-500 block mb-2">Source:</span>
                    <div className="bg-gray-800 p-4 rounded border border-gray-700">
                      {selectedLog.module && (
                        <div>
                          <span className="text-gray-500">Module:</span>
                          <span className="ml-2 text-gray-300">{selectedLog.module}</span>
                        </div>
                      )}
                      {selectedLog.funcName && (
                        <div>
                          <span className="text-gray-500">Function:</span>
                          <span className="ml-2 text-gray-300">{selectedLog.funcName}</span>
                        </div>
                      )}
                      {selectedLog.lineno && (
                        <div>
                          <span className="text-gray-500">Line:</span>
                          <span className="ml-2 text-gray-300">{selectedLog.lineno}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Raw JSON */}
                <div>
                  <span className="text-gray-500 block mb-2">Raw Log Entry:</span>
                  <div className="bg-gray-800 p-4 rounded border border-gray-700 overflow-x-auto">
                    <pre className="text-gray-300 text-xs">
                      {JSON.stringify(selectedLog, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="border-t border-gray-700 p-4 flex items-center justify-end space-x-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(selectedLog.id)
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
              >
                Copy Log ID
              </button>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(JSON.stringify(selectedLog, null, 2))
                }}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors"
              >
                Copy JSON
              </button>
              <button
                onClick={() => {
                  setShowLogDetail(false)
                  setSelectedLog(null)
                }}
                className="px-4 py-2 bg-primary-600 hover:bg-primary-700 rounded text-sm transition-colors"
              >
                Close
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}

      {/* Footer Stats */}
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50 flex items-center justify-between text-xs text-gray-600">
        <div className="flex items-center space-x-4">
          <span>Showing {filteredLogs.length} of {logs.length} logs</span>
          {filteredLogs.length !== logs.length && (
            <span className="text-blue-600">({logs.length - filteredLogs.length} filtered out)</span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          <Clock className="w-4 h-4" />
          <span>Last updated: {new Date().toLocaleTimeString()}</span>
        </div>
      </div>
    </div>
  )
}

export default AgentLogs
