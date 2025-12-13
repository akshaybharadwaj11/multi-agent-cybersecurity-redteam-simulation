import React, { useState } from 'react'
import { Terminal, List } from 'lucide-react'
import AgentLogs from '../components/AgentLogs'
import LogStreams from '../components/LogStreams'

const Logs = () => {
  const [view, setView] = useState('streams') // 'streams' or 'logs'
  const [selectedStreamId, setSelectedStreamId] = useState(null)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">Logs</h1>
          <p className="text-gray-600 text-lg">View and monitor agent logs</p>
        </div>
        <div className="flex items-center space-x-2 bg-white rounded-lg border border-gray-200 p-1">
          <button
            onClick={() => {
              setView('streams')
              setSelectedStreamId(null)
            }}
            className={`px-4 py-2 rounded-md text-sm font-semibold transition-all duration-200 flex items-center space-x-2 ${
              view === 'streams'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <List className="w-4 h-4" />
            <span>Log Streams</span>
          </button>
          <button
            onClick={() => {
              setView('logs')
              setSelectedStreamId(null)
            }}
            className={`px-4 py-2 rounded-md text-sm font-semibold transition-all duration-200 flex items-center space-x-2 ${
              view === 'logs'
                ? 'bg-blue-600 text-white shadow-md'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Log Events</span>
          </button>
        </div>
      </div>

      {view === 'streams' ? (
        <LogStreams 
          onStreamSelect={(streamId) => {
            console.log('[Logs] Stream selected:', streamId)
            setSelectedStreamId(streamId)
            setView('logs')
          }}
        />
      ) : (
        <div className="space-y-4">
          {selectedStreamId && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="text-sm font-medium text-blue-900">
                  Filtering logs for simulation:
                </span>
                <code className="text-sm font-mono bg-blue-100 px-3 py-1 rounded text-blue-800">
                  {selectedStreamId === 'system' ? 'System Logs' : selectedStreamId.replace('sim_', 'Simulation ').replace(/_/g, ' ')}
                </code>
              </div>
              <button
                onClick={() => {
                  setSelectedStreamId(null)
                  setView('streams')
                }}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Clear Filter
              </button>
            </div>
          )}
          <AgentLogs 
            agent={null} 
            autoRefresh={true}
            filterBySimulationId={selectedStreamId}
            key={selectedStreamId || 'all'} // Force re-render when filter changes
          />
        </div>
      )}
    </div>
  )
}

export default Logs
