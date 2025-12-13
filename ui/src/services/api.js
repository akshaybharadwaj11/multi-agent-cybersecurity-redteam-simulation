import axios from 'axios'

// Use relative URL to go through Vite proxy, or absolute if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false, // Don't send credentials for CORS
})

// Add request interceptor for debugging and data cleaning
api.interceptors.request.use(
  (config) => {
    // Clean the request data to remove any circular references
    if (config.data && typeof config.data === 'object') {
      // First, try to detect if it's a simulation config by checking for known keys
      const hasSimKeys = 'num_episodes' in config.data || 'attack_types' in config.data || 'quick_test' in config.data
      
      if (hasSimKeys) {
        // It's a simulation config - extract only the values we need
        try {
          const numEp = config.data.num_episodes
          const attackTypes = config.data.attack_types
          const quickTest = config.data.quick_test
          
          // Create completely new object with only primitives
          config.data = {
            num_episodes: typeof numEp === 'number' ? numEp : (typeof numEp === 'string' ? parseInt(numEp, 10) : 10),
            attack_types: Array.isArray(attackTypes) ? attackTypes.filter(t => typeof t === 'string') : ['phishing'],
            quick_test: typeof quickTest === 'boolean' ? quickTest : false
          }
          
          // Verify it can be stringified
          JSON.stringify(config.data)
        } catch (e) {
          // If extraction or stringify fails, use defaults
          console.error('[API] Failed to clean simulation config, using defaults:', e)
          config.data = {
            num_episodes: 10,
            attack_types: ['phishing'],
            quick_test: false
          }
        }
      } else {
        // For other data types, try JSON parse/stringify first
        try {
          const cleanData = JSON.parse(JSON.stringify(config.data))
          config.data = cleanData
        } catch (e) {
          // If that fails, extract only primitives
          console.warn('[API] Detected circular reference in request data, cleaning manually')
          const cleaned = {}
          for (const key in config.data) {
            if (config.data.hasOwnProperty(key) && typeof key === 'string') {
              const value = config.data[key]
              if (value === null || value === undefined) {
                cleaned[key] = value
              } else if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                cleaned[key] = value
              } else if (Array.isArray(value)) {
                cleaned[key] = value.filter(item => 
                  item === null || 
                  typeof item === 'string' || 
                  typeof item === 'number' || 
                  typeof item === 'boolean'
                )
              }
            }
          }
          config.data = cleaned
        }
      }
    }
    
    // Only log in development, not in production
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    }
    return config
  },
  (error) => {
    // Only log real errors, not network failures (API might be down)
    if (error.code !== 'ERR_NETWORK' && error.code !== 'ECONNREFUSED') {
      console.error('[API] Request error:', error)
    }
    return Promise.reject(error)
  }
)

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Suppress network errors - API server might not be running, which is OK
    if (error.code === 'ERR_NETWORK' || error.message === 'Network Error' || error.code === 'ECONNREFUSED') {
      // Don't log these - they're expected if API server is down
      return Promise.reject(error)
    } else if (error.response) {
      // Log HTTP errors (actual API responses) - safely extract data
      const errorData = error.response.data
      if (errorData && typeof errorData === 'object' && !errorData.constructor || errorData.constructor === Object) {
        console.error(`[API] ${error.response.status} ${error.response.statusText}:`, errorData)
      } else {
        console.error(`[API] ${error.response.status} ${error.response.statusText}`)
      }
    } else {
      // Log other errors - safely extract message
      const errorMsg = error?.message || String(error) || 'Unknown error'
      console.error('[API] Error:', errorMsg)
    }
    // Create a clean error object to avoid circular references
    const cleanError = {
      message: error?.message || String(error) || 'Unknown error',
      code: error?.code,
      response: error?.response ? {
        status: error.response.status,
        statusText: error.response.statusText,
        data: error.response.data
      } : undefined
    }
    return Promise.reject(cleanError)
  }
)

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
  // Ensure config is a clean plain object without any React references
  // Handle case where config might be undefined or have circular references
  let numEpisodes = 10
  let attackTypes = ['phishing']
  let quickTest = false
  
  if (config && typeof config === 'object') {
    try {
      // Safely extract values without accessing potentially circular properties
      if (typeof config.num_episodes === 'number') {
        numEpisodes = config.num_episodes
      } else if (typeof config.num_episodes === 'string') {
        numEpisodes = parseInt(config.num_episodes, 10) || 10
      }
      
      if (Array.isArray(config.attack_types)) {
        attackTypes = config.attack_types.filter(t => typeof t === 'string')
      }
      
      if (typeof config.quick_test === 'boolean') {
        quickTest = config.quick_test
      }
    } catch (e) {
      // If extraction fails, use defaults
      console.warn('[API] Failed to extract config, using defaults:', e.message)
    }
  }
  
  // Create a completely new object with only primitives
  // Build it from scratch to avoid any object references
  const cleanConfig = {
    num_episodes: Number(numEpisodes) || 10,
    attack_types: Array.isArray(attackTypes) ? attackTypes.map(t => String(t)) : ['phishing'],
    quick_test: Boolean(quickTest),
  }
  
  // Verify it can be stringified before making the request
  let serialized
  try {
    serialized = JSON.stringify(cleanConfig)
  } catch (e) {
    console.error('[API] Cannot serialize config:', e)
    // Create a minimal safe config
    const safeConfig = {
      num_episodes: 10,
      attack_types: ['phishing'],
      quick_test: false,
    }
    serialized = JSON.stringify(safeConfig)
    console.warn('[API] Using safe default config instead')
  }
  
  // Parse it back to ensure it's completely clean
  const finalConfig = JSON.parse(serialized)
  
  const response = await api.post('/simulations/start', finalConfig)
  return response.data
}

export const getSimulationStatus = async (simulationId) => {
  const response = await api.get(`/simulations/${simulationId}/status`)
  return response.data
}

export const pauseSimulation = async (simulationId) => {
  const response = await api.post(`/simulations/${simulationId}/pause`)
  return response.data
}

export const resumeSimulation = async (simulationId) => {
  const response = await api.post(`/simulations/${simulationId}/resume`)
  return response.data
}

export const stopSimulation = async (simulationId) => {
  const response = await api.post(`/simulations/${simulationId}/stop`)
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
export const getRLMetrics = async (simulationId = null) => {
  const params = simulationId ? { simulation_id: simulationId } : {}
  const response = await api.get('/rl/metrics', { params })
  return response.data
}

// Log detail endpoint
export const getLogDetails = async (logId) => {
  const response = await api.get(`/agents/logs/${logId}`)
  return response.data
}

export default api
