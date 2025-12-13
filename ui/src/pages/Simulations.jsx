import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Play, Pause, Square, Filter, Search, Eye } from 'lucide-react'
import { pauseSimulation, resumeSimulation, stopSimulation } from '../services/api'
import { startSimulation, getSimulationStatus, getSimulationEpisodes, getAllSimulations } from '../services/api'
import { useNavigate } from 'react-router-dom'

const Simulations = () => {
  const navigate = useNavigate()
  const [simulations, setSimulations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedSim, setExpandedSim] = useState(null)
  const [episodes, setEpisodes] = useState({})

  useEffect(() => {
    // Load all simulations on mount
    loadSimulations()
    
    // Poll for simulation updates
    const interval = setInterval(() => {
      loadSimulations()
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const loadSimulations = async () => {
    try {
      const allSims = await getAllSimulations()
      setSimulations(allSims)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load simulations:', error)
      setLoading(false)
    }
  }

  const updateSimulationStatuses = async () => {
    // Reload all simulations to get latest status
    await loadSimulations()
  }

  const handleStartSimulation = async () => {
    setLoading(true)
    setError(null)
    try {
      console.log('Starting simulation...')
      const result = await startSimulation({
        num_episodes: 10,
        attack_types: ['phishing'],
        quick_test: false,
      })
      console.log('Simulation started:', result)
      
      const newSim = {
        id: result.id,
        name: `Simulation ${result.id}`,
        attackType: 'Phishing',
        episodes: 10,
        status: 'running',
        progress: 0,
        startTime: new Date(),
        successRate: 0,
      }
      
      // Reload all simulations to get the new one
      await loadSimulations()
      
      // Show success message
      console.log(`Simulation ${result.id} started!`)
    } catch (error) {
      console.error('Failed to start simulation:', error)
      setError(`Failed to start simulation: ${error.message || 'API server may not be running on port 8000'}`)
    } finally {
      setLoading(false)
    }
  }

  const loadEpisodes = async (simId) => {
    try {
      const eps = await getSimulationEpisodes(simId)
      setEpisodes(prev => ({ ...prev, [simId]: eps }))
    } catch (error) {
      console.error('Failed to load episodes:', error)
    }
  }

  const handlePauseSimulation = async (simId) => {
    try {
      await pauseSimulation(simId)
      await loadSimulations() // Refresh to show updated status
    } catch (error) {
      console.error('Failed to pause simulation:', error)
      alert(`Failed to pause simulation: ${error.message || 'Unknown error'}`)
    }
  }

  const handleResumeSimulation = async (simId) => {
    try {
      await resumeSimulation(simId)
      await loadSimulations() // Refresh to show updated status
    } catch (error) {
      console.error('Failed to resume simulation:', error)
      alert(`Failed to resume simulation: ${error.message || 'Unknown error'}`)
    }
  }

  const handleStopSimulation = async (simId) => {
    if (!confirm('Are you sure you want to stop this simulation? It cannot be resumed.')) {
      return
    }
    try {
      await stopSimulation(simId)
      await loadSimulations() // Refresh to show updated status
    } catch (error) {
      console.error('Failed to stop simulation:', error)
      alert(`Failed to stop simulation: ${error.message || 'Unknown error'}`)
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'bg-primary-100 text-primary-700 border-primary-300'
      case 'completed':
        return 'bg-success-100 text-success-700 border-success-300'
      case 'paused':
        return 'bg-yellow-100 text-yellow-700 border-yellow-300'
      case 'stopped':
        return 'bg-gray-100 text-gray-700 border-gray-300'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">Simulations</h1>
          <p className="text-gray-600 text-lg">Manage and monitor your cyber defense simulations</p>
        </div>
        <button 
          onClick={handleStartSimulation}
          disabled={loading}
          className="btn btn-primary px-6 py-3 shadow-lg hover:shadow-xl transition-all duration-200"
        >
          <Play className="w-5 h-5 mr-2" />
          {loading ? 'Starting...' : 'New Simulation'}
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search simulations..."
              className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl 
                       focus:ring-2 focus:ring-primary-500 focus:border-primary-500 
                       transition-all duration-200 bg-white/50 backdrop-blur-sm"
            />
          </div>
          <button className="btn btn-secondary px-6 py-3 whitespace-nowrap">
            <Filter className="w-4 h-4 mr-2" />
            Filter
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="card bg-danger-50 border-danger-200">
          <p className="text-danger-700">{error}</p>
        </div>
      )}

      {/* Simulations List */}
      {simulations.length === 0 ? (
        <div className="card text-center py-12">
          <p className="text-gray-500 mb-4">No simulations yet.</p>
          <button 
            onClick={handleStartSimulation}
            disabled={loading}
            className="btn btn-primary px-6 py-3"
          >
            {loading ? 'Starting...' : 'Start Your First Simulation'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {simulations.map((sim, index) => (
          <motion.div
            key={sim.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="card hover:shadow-xl transition-all duration-300 border-l-4 border-l-primary-500"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-gray-900">{sim.name}</h3>
                  <span className={`badge ${getStatusColor(sim.status)}`}>
                    {sim.status}
                  </span>
                </div>
                <div className="grid grid-cols-4 gap-4 text-sm text-gray-600">
                  <div>
                    <span className="font-medium">Attack Type:</span> {sim.attackType}
                  </div>
                  <div>
                    <span className="font-medium">Episodes:</span> {sim.episodes}
                  </div>
                  <div>
                    <span className="font-medium">Success Rate:</span> {(sim.successRate * 100).toFixed(0)}%
                  </div>
                  <div>
                    <span className="font-medium">Progress:</span> {sim.progress}%
                  </div>
                </div>
                {sim.status === 'running' && (
                  <div className="mt-3">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all"
                        style={{ width: `${sim.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
              <div className="flex items-center space-x-2 ml-6">
                <button
                  onClick={() => {
                    if (expandedSim === sim.id) {
                      setExpandedSim(null)
                    } else {
                      setExpandedSim(sim.id)
                      loadEpisodes(sim.id)
                    }
                  }}
                  className="btn btn-secondary px-3 py-2"
                >
                  <Eye className="w-4 h-4" />
                </button>
                {sim.status === 'running' && (
                  <>
                    <button 
                      onClick={() => handlePauseSimulation(sim.id)}
                      className="btn btn-secondary px-3 py-2"
                      title="Pause simulation"
                    >
                      <Pause className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => handleStopSimulation(sim.id)}
                      className="btn btn-danger px-3 py-2"
                      title="Stop simulation"
                    >
                      <Square className="w-4 h-4" />
                    </button>
                  </>
                )}
                {sim.status === 'paused' && (
                  <>
                    <button 
                      onClick={() => handleResumeSimulation(sim.id)}
                      className="btn btn-primary px-3 py-2"
                      title="Resume simulation"
                    >
                      <Play className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => handleStopSimulation(sim.id)}
                      className="btn btn-danger px-3 py-2"
                      title="Stop simulation"
                    >
                      <Square className="w-4 h-4" />
                    </button>
                  </>
                )}
              </div>
            </div>
            {expandedSim === sim.id && episodes[sim.id] && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="font-semibold mb-3">Episodes:</h4>
                <div className="space-y-2">
                  {episodes[sim.id].map((ep) => (
                    <div
                      key={ep.episode_number}
                      className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                      onClick={() => navigate(`/episodes/${ep.episode_number}`)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <span className="font-medium">Episode {ep.episode_number}</span>
                          <span className="ml-2 text-sm text-gray-600">{ep.attack_type}</span>
                        </div>
                        <div className="flex items-center space-x-4 text-sm">
                          <span className={ep.success ? 'text-success-600' : 'text-danger-600'}>
                            {ep.success ? '✓ Success' : '✗ Failed'}
                          </span>
                          <span className="text-gray-600">Reward: {ep.reward.toFixed(3)}</span>
                          <button className="btn btn-secondary px-2 py-1 text-xs">
                            View Details
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ))}
        </div>
      )}
    </div>
  )
}

export default Simulations

