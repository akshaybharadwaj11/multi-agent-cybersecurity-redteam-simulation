import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import AgentOrchestrationGraph from '../components/AgentOrchestrationGraph'
import { getAllSimulations, getSimulationEpisodes } from '../services/api'

const Orchestration = () => {
  const { episodeNumber } = useParams()
  const [simulations, setSimulations] = useState([])
  const [selectedSimulation, setSelectedSimulation] = useState(null)

  useEffect(() => {
    loadSimulations()
  }, [])

  const loadSimulations = async () => {
    try {
      const data = await getAllSimulations()
      setSimulations(data)
      // Auto-select most recent active simulation
      const active = data.find(s => s.status === 'running')
      if (active) {
        setSelectedSimulation(active.id)
      } else if (data.length > 0) {
        setSelectedSimulation(data[0].id)
      }
    } catch (error) {
      console.error('Error loading simulations:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">
            Agent Orchestration
          </h1>
          <p className="text-gray-600 text-lg">
            Visualize real-time agent interactions and workflow
          </p>
        </div>
        {simulations.length > 0 && (
          <div className="flex items-center space-x-3">
            <label className="text-sm font-medium text-gray-700">Simulation:</label>
            <select
              value={selectedSimulation || ''}
              onChange={(e) => setSelectedSimulation(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {simulations.map((sim) => (
                <option key={sim.id} value={sim.id}>
                  {sim.name} ({sim.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      <AgentOrchestrationGraph 
        simulationId={selectedSimulation}
        episodeNumber={episodeNumber ? parseInt(episodeNumber) : null}
      />

      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Orchestration Flow</h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
                <span className="text-red-600 font-bold">1</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Red Team</h3>
                <p className="text-sm text-gray-600">
                  Generates realistic cyberattack scenarios using MITRE ATT&CK framework
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                <span className="text-blue-600 font-bold">2</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Telemetry</h3>
                <p className="text-sm text-gray-600">
                  Creates synthetic system logs based on attack scenario
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center">
                <span className="text-yellow-600 font-bold">3</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Detection</h3>
                <p className="text-sm text-gray-600">
                  Analyzes telemetry using LLM to detect security incidents
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                <span className="text-purple-600 font-bold">4</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">RAG Agent</h3>
                <p className="text-sm text-gray-600">
                  Retrieves threat intelligence and runbooks from knowledge base
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                <span className="text-green-600 font-bold">5</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Remediation</h3>
                <p className="text-sm text-gray-600">
                  Generates remediation action recommendations based on incident and context
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-pink-100 flex items-center justify-center">
                <span className="text-pink-600 font-bold">6</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">RL Agent</h3>
                <p className="text-sm text-gray-600">
                  Selects optimal action using reinforcement learning (Q-learning)
                </p>
              </div>
            </div>
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                <span className="text-indigo-600 font-bold">7</span>
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Outcome & Reward</h3>
                <p className="text-sm text-gray-600">
                  Simulates action outcome and calculates reward for RL learning
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Orchestration

