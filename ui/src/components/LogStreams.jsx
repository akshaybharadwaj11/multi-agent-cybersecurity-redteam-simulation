import React, { useState, useEffect } from 'react'
import { Search, RefreshCw, ChevronDown, ChevronUp, ExternalLink, Clock, Hash } from 'lucide-react'
import { getAgentLogs } from '../services/api'
import { format, parseISO } from 'date-fns'

const LogStreams = ({ onStreamSelect = null }) => {
  const [logs, setLogs] = useState([])
  const [streams, setStreams] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [sortBy, setSortBy] = useState('lastEvent') // 'lastEvent' or 'count'
  const [sortOrder, setSortOrder] = useState('desc') // 'asc' or 'desc'
  const [selectedStreams, setSelectedStreams] = useState(new Set())

  useEffect(() => {
    loadLogs()
    const interval = setInterval(loadLogs, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    processStreams()
  }, [logs])

  const loadLogs = async () => {
    try {
      const data = await getAgentLogs(null, 1000) // Get all logs
      const newLogs = data.logs || []
      console.log(`[LogStreams] Loaded ${newLogs.length} logs from API`)
      setLogs(newLogs)
      setLoading(false)
    } catch (error) {
      console.error('[LogStreams] Failed to load logs:', error)
      setLoading(false)
    }
  }

  const processStreams = () => {
    // Group logs by simulation_id (one stream per simulation)
    const streamMap = new Map()
    
    console.log(`[LogStreams] Processing ${logs.length} logs into streams`)
    
    logs.forEach(log => {
      // Use simulation_id if available, otherwise use 'system' for non-simulation logs
      const streamId = log.simulation_id || 'system'
      
      if (!streamMap.has(streamId)) {
        streamMap.set(streamId, {
          id: streamId,
          logs: [],
          agents: new Set(),
          levels: new Set(),
          firstEvent: null,
          lastEvent: null,
        })
      }
      
      const stream = streamMap.get(streamId)
      stream.logs.push(log)
      stream.agents.add(log.agent)
      
      if (log.level) {
        stream.levels.add(log.level)
      }
      
      const logDate = log.timestamp 
        ? (typeof log.timestamp === 'string' ? parseISO(log.timestamp) : new Date(log.timestamp))
        : new Date()
      
      if (!stream.firstEvent || logDate < stream.firstEvent) {
        stream.firstEvent = logDate
      }
      if (!stream.lastEvent || logDate > stream.lastEvent) {
        stream.lastEvent = logDate
      }
    })
    
    // Convert to array and format
    const streamArray = Array.from(streamMap.values()).map(stream => ({
      id: stream.id,
      logCount: stream.logs.length,
      agents: Array.from(stream.agents),
      levels: Array.from(stream.levels),
      firstEvent: stream.firstEvent,
      lastEvent: stream.lastEvent,
      logs: stream.logs,
    }))
    
    console.log(`[LogStreams] Created ${streamArray.length} streams from ${logs.length} logs`)
    setStreams(streamArray)
  }

  const filteredStreams = streams.filter(stream => {
    if (!searchTerm) return true
    const search = searchTerm.toLowerCase()
    return (
      stream.id.toLowerCase().includes(search) ||
      stream.agents.some(a => a.toLowerCase().includes(search)) ||
      stream.levels.some(l => l.toLowerCase().includes(search))
    )
  })

  const sortedStreams = [...filteredStreams].sort((a, b) => {
    let comparison = 0
    if (sortBy === 'lastEvent') {
      comparison = a.lastEvent - b.lastEvent
    } else if (sortBy === 'count') {
      comparison = a.logCount - b.logCount
    } else if (sortBy === 'id') {
      comparison = a.id.localeCompare(b.id)
    }
    return sortOrder === 'asc' ? comparison : -comparison
  })

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
  }

  const handleStreamClick = (streamId) => {
    if (onStreamSelect) {
      onStreamSelect(streamId)
    }
  }

  const toggleStreamSelection = (streamId) => {
    const newSelected = new Set(selectedStreams)
    if (newSelected.has(streamId)) {
      newSelected.delete(streamId)
    } else {
      newSelected.add(streamId)
    }
    setSelectedStreams(newSelected)
  }

  const SortIcon = ({ column }) => {
    if (sortBy !== column) return null
    return sortOrder === 'asc' ? (
      <ChevronUp className="w-4 h-4 inline ml-1" />
    ) : (
      <ChevronDown className="w-4 h-4 inline ml-1" />
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading log streams...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200/60 overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200/60 p-6 bg-gradient-to-r from-gray-50 to-gray-100/50">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Log Streams</h2>
            <p className="text-sm text-gray-600 mt-1">
              {streams.length} log stream{streams.length !== 1 ? 's' : ''} 
              {filteredStreams.length !== streams.length && ` (${filteredStreams.length} filtered)`}
              <span className="ml-2 text-xs text-gray-500">(Each simulation grouped into one stream)</span>
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={loadLogs}
              className="btn btn-secondary px-4 py-2.5 text-sm font-semibold"
              title="Refresh streams"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex items-center space-x-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Filter log streams or try prefix search"
              className="w-full pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Streams Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider w-12">
                <input
                  type="checkbox"
                  checked={selectedStreams.size === sortedStreams.length && sortedStreams.length > 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedStreams(new Set(sortedStreams.map(s => s.id)))
                    } else {
                      setSelectedStreams(new Set())
                    }
                  }}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th 
                className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('id')}
              >
                <div className="flex items-center">
                  Log Stream
                  <SortIcon column="id" />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Agents
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Log Count
              </th>
              <th 
                className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('lastEvent')}
              >
                <div className="flex items-center">
                  Last Event Time
                  <SortIcon column="lastEvent" />
                </div>
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedStreams.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-4 py-12 text-center text-gray-500">
                  <p className="text-lg font-medium">No log streams found</p>
                  <p className="text-sm mt-2">
                    {searchTerm ? "Try adjusting your search" : "Start a simulation to see log streams"}
                  </p>
                </td>
              </tr>
            ) : (
              sortedStreams.map((stream) => (
                <tr
                  key={stream.id}
                  className="hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => handleStreamClick(stream.id)}
                >
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <input
                      type="checkbox"
                      checked={selectedStreams.has(stream.id)}
                      onChange={() => toggleStreamSelection(stream.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-sm font-mono text-blue-600 hover:text-blue-800 hover:underline">
                      {stream.id === 'system' 
                        ? 'System Logs' 
                        : stream.id.replace('sim_', 'Simulation ').replace(/_/g, ' ').replace(/\s+\d{6}$/, '') // Remove microseconds for readability
                      }
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {stream.agents.map(agent => (
                        <span
                          key={agent}
                          className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700 border border-gray-300"
                        >
                          {agent}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {stream.logCount}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {stream.lastEvent 
                      ? format(stream.lastEvent, 'yyyy-MM-dd HH:mm:ss')
                      : 'N/A'
                    }
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => handleStreamClick(stream.id)}
                      className="text-blue-600 hover:text-blue-800 text-sm font-medium flex items-center space-x-1"
                    >
                      <ExternalLink className="w-4 h-4" />
                      <span>View</span>
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200/60 px-6 py-4 bg-gray-50 flex items-center justify-between text-sm text-gray-600">
        <span>
          Showing {sortedStreams.length} of {streams.length} log stream{streams.length !== 1 ? 's' : ''}
        </span>
        {selectedStreams.size > 0 && (
          <span className="text-blue-600">
            {selectedStreams.size} stream{selectedStreams.size !== 1 ? 's' : ''} selected
          </span>
        )}
      </div>
    </div>
  )
}

export default LogStreams

