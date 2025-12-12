import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Dashboard endpoints
export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats')
  return response.data
}

export const getRecentSimulations = async (limit = 5) => {
  const response = await api.get(`/simulations/recent?limit=${limit}`)
  return response.data
}

// Simulation endpoints
export const getAllSimulations = async () => {
  const response = await api.get('/simulations')
  return response.data
}

export const startSimulation = async (config) => {
  const response = await api.post('/simulations/start', config)
  return response.data
}

export const getSimulationStatus = async (simulationId) => {
  const response = await api.get(`/simulations/${simulationId}/status`)
  return response.data
}

export const getSimulationEpisodes = async (simulationId) => {
  const response = await api.get(`/simulations/${simulationId}/episodes`)
  return response.data
}

export const getEpisodeDetails = async (episodeNumber) => {
  const response = await api.get(`/episodes/${episodeNumber}`)
  return response.data
}

// Agent endpoints
export const getAgentStatus = async () => {
  const response = await api.get('/agents/status')
  return response.data
}

// Analytics endpoints
export const getAnalytics = async (timeRange = '24h') => {
  const response = await api.get(`/analytics?range=${timeRange}`)
  return response.data
}

// Agent logs endpoints
export const getAgentLogs = async (agent = null, limit = 100) => {
  const params = { limit }
  if (agent) params.agent = agent
  const response = await api.get('/agents/logs', { params })
  return response.data
}

// RL metrics endpoints
export const getRLMetrics = async () => {
  const response = await api.get('/rl/metrics')
  return response.data
}

// Log detail endpoint
export const getLogDetails = async (logId) => {
  const response = await api.get(`/agents/logs/${logId}`)
  return response.data
}

export default api
