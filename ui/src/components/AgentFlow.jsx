import React, { useState, useEffect } from 'react'
import { 
  User, 
  Search, 
  FileText, 
  Shield, 
  Brain,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowRight
} from 'lucide-react'
import { motion } from 'framer-motion'
import { getSimulationEpisodes, getEpisodeDetails, startSimulation as startSimulationAPI } from '../services/api'
import AgentDetailModal from './AgentDetailModal'

const AgentFlow = ({ simulationId = null, onSimulationStart = null }) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [isRunning, setIsRunning] = useState(false)
  const [episodeData, setEpisodeData] = useState(null)
  const [selectedAgent, setSelectedAgent] = useState(null)
  const [fullEpisodeData, setFullEpisodeData] = useState(null)
  const [starting, setStarting] = useState(false)

  const agents = [
    {
      id: 'red-team',
      name: 'Red Team',
      role: 'Attack Generation',
      icon: User,
      color: 'danger',
      status: 'completed',
      description: 'Generates realistic cyberattack scenarios',
    },
    {
      id: 'telemetry',
      name: 'Telemetry',
      role: 'Log Generation',
      icon: FileText,
      color: 'primary',
      status: 'completed',
      description: 'Creates synthetic system logs',
    },
    {
      id: 'detection',
      name: 'Detection',
      role: 'Incident Analysis',
      icon: Search,
      color: 'warning',
      status: 'active',
      description: 'Analyzes telemetry for threats',
    },
    {
      id: 'rag',
      name: 'RAG',
      role: 'Context Retrieval',
      icon: Brain,
      color: 'primary',
      status: 'pending',
      description: 'Retrieves threat intelligence',
    },
    {
      id: 'remediation',
      name: 'Remediation',
      role: 'Action Planning',
      icon: Shield,
      color: 'success',
      status: 'pending',
      description: 'Generates remediation options',
    },
    {
      id: 'rl',
      name: 'RL Agent',
      role: 'Action Selection',
      icon: Brain,
      color: 'primary',
      status: 'pending',
      description: 'Selects optimal action',
    },
  ]

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-success-600" />
      case 'active':
        return <Clock className="w-5 h-5 text-primary-600 animate-spin" />
      case 'pending':
        return <AlertCircle className="w-5 h-5 text-gray-400" />
      default:
        return null
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'border-success-500 bg-success-50'
      case 'active':
        return 'border-primary-500 bg-primary-50'
      case 'pending':
        return 'border-gray-300 bg-gray-50'
      default:
        return 'border-gray-300 bg-gray-50'
    }
  }

  useEffect(() => {
    if (isRunning) {
      const interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev < agents.length - 1) {
            return prev + 1
          }
          setIsRunning(false)
          return prev
        })
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [isRunning, agents.length])

  useEffect(() => {
    if (simulationId) {
      // Poll for episode updates if simulation is running
      const interval = setInterval(async () => {
        try {
          const episodes = await getSimulationEpisodes(simulationId)
          if (episodes.length > 0) {
            const latest = episodes[episodes.length - 1]
            // Load full episode details
            try {
              const fullDetails = await getEpisodeDetails(latest.episode_number)
              setEpisodeData(fullDetails)
            } catch (e) {
              setEpisodeData(latest)
            }
            // Update step based on episode completion
            if (latest.success !== undefined) {
              setCurrentStep(agents.length - 1)
              setIsRunning(false)
            }
          }
        } catch (e) {
          console.error('Error fetching episode data:', e)
        }
      }, 2000)
      return () => clearInterval(interval)
    }
  }, [simulationId])

  const startSimulation = async () => {
    setStarting(true)
    setCurrentStep(0)
    setIsRunning(true)
    setEpisodeData(null)
    
    try {
      // Actually start the simulation via API
      const result = await startSimulationAPI({
        num_episodes: 10,
        attack_types: ['phishing'],
        quick_test: false,
      })
      
      console.log('Simulation started:', result)
      
      // Notify parent component if callback provided
      if (onSimulationStart) {
        onSimulationStart(result.id)
      }
      
      // The simulation will run in the background, and we'll poll for updates
      // via the simulationId prop when it's set
    } catch (error) {
      console.error('Failed to start simulation:', error)
      setIsRunning(false)
      alert(`Failed to start simulation: ${error.message || 'API server may not be running'}`)
    } finally {
      setStarting(false)
    }
  }

  return (
    <div className="card glow">
      <div className="card-header">
        <div>
          <h2 className="card-title">Agent Flow Visualization</h2>
          <p className="text-sm text-gray-500 mt-1">Interactive multi-agent simulation pipeline</p>
        </div>
        <button
          onClick={startSimulation}
          disabled={isRunning || starting}
          className="btn btn-primary px-6 py-2.5 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {starting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Starting...
            </>
          ) : isRunning ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Running...
            </>
          ) : (
            'Start Simulation'
          )}
        </button>
      </div>

      <div className="space-y-4">
        {agents.map((agent, index) => {
          const Icon = agent.icon
          const isActive = index === currentStep && isRunning
          const isCompleted = index < currentStep
          const status = isCompleted ? 'completed' : isActive ? 'active' : 'pending'

          return (
            <motion.div
              key={agent.id}
              onClick={async () => {
                setSelectedAgent(agent)
                // Load full episode data if available
                if (episodeData && episodeData.episode_number) {
                  try {
                    const fullData = await getEpisodeDetails(episodeData.episode_number)
                    setFullEpisodeData(fullData)
                  } catch (e) {
                    console.error('Error loading episode details:', e)
                    setFullEpisodeData(episodeData)
                  }
                } else {
                  setFullEpisodeData(episodeData)
                }
              }}
              initial={{ opacity: 0, x: -20 }}
              animate={{ 
                opacity: 1, 
                x: 0,
                scale: isActive ? 1.02 : 1
              }}
              transition={{ duration: 0.3 }}
              className={`
                flex items-center space-x-4 p-5 rounded-xl border-2 transition-all duration-300 
                cursor-pointer group
                ${getStatusColor(status)}
                ${isActive ? 'shadow-xl scale-[1.02] ring-2 ring-primary-200' : 'hover:scale-[1.01] hover:shadow-md'}
              `}
            >
              <div className={`
                p-3 rounded-lg
                ${status === 'completed' ? 'bg-success-100' : ''}
                ${status === 'active' ? 'bg-primary-100' : ''}
                ${status === 'pending' ? 'bg-gray-100' : ''}
              `}>
                <Icon className={`
                  w-6 h-6
                  ${status === 'completed' ? 'text-success-600' : ''}
                  ${status === 'active' ? 'text-primary-600' : ''}
                  ${status === 'pending' ? 'text-gray-400' : ''}
                `} />
              </div>

              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <h3 className="font-semibold text-gray-900">{agent.name}</h3>
                  {getStatusIcon(status)}
                </div>
                <p className="text-sm text-gray-600">{agent.role}</p>
                <p className="text-xs text-gray-500 mt-1">{agent.description}</p>
                {/* Show remediation info if available */}
                {agent.id === 'remediation' && episodeData?.remediation && (
                  <div className="mt-2 p-2 bg-green-50 rounded border border-green-200">
                    <p className="text-xs font-medium text-green-800 mb-1">Recommended Action:</p>
                    <p className="text-sm text-green-900 font-semibold">
                      {episodeData.remediation.recommended_action?.replace('_', ' ').toUpperCase() || 'N/A'}
                    </p>
                    {episodeData.remediation.options && episodeData.remediation.options.length > 0 && (
                      <p className="text-xs text-green-700 mt-1">
                        {episodeData.remediation.options.length} action options available
                      </p>
                    )}
                  </div>
                )}
              </div>

              {index < agents.length - 1 && (
                <ArrowRight className="w-5 h-5 text-gray-400" />
              )}
            </motion.div>
          )
        })}
      </div>

      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Current Step: {currentStep + 1} / {agents.length}</span>
          <span className="text-gray-600">
            Status: {isRunning ? 'Running' : 'Idle'}
          </span>
        </div>
      </div>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <AgentDetailModal
          agent={selectedAgent}
          episodeData={fullEpisodeData}
          onClose={() => {
            setSelectedAgent(null)
            setFullEpisodeData(null)
          }}
        />
      )}
    </div>
  )
}

export default AgentFlow

