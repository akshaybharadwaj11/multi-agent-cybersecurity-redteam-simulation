import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Brain, TrendingUp, TrendingDown, Activity, Target, Zap, BarChart3, Filter, Award, Clock, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { getRLMetrics, getAllSimulations } from '../services/api'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const RLMetrics = () => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [simulations, setSimulations] = useState([])
  const [selectedSimulation, setSelectedSimulation] = useState(null)
  const hasShownErrorRef = useRef(false)

  useEffect(() => {
    loadSimulations()
  }, [])

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 3000) // Refresh every 3 seconds
    return () => clearInterval(interval)
  }, [selectedSimulation])

  const loadSimulations = async () => {
    try {
      const data = await getAllSimulations()
      setSimulations(data)
      // Auto-select most recent simulation if available
      if (data.length > 0 && !selectedSimulation) {
        setSelectedSimulation(data[0].id)
      }
    } catch (err) {
      console.error('Failed to load simulations:', err)
    }
  }

  const loadMetrics = async () => {
    try {
      const data = await getRLMetrics(selectedSimulation)
      setMetrics(data)
      setLoading(false)
      setError(null)
      hasShownErrorRef.current = false
    } catch (err) {
      // Only log error if it's not a network error (API might not be running)
      if (err.code !== 'ERR_NETWORK' && err.code !== 'ECONNREFUSED') {
        console.error('Failed to load RL metrics:', err)
      }
      // Don't set error message repeatedly - API might just not be available
      if (!hasShownErrorRef.current) {
        setError('RL metrics API is not available. Make sure the API server is running on port 8000.')
        hasShownErrorRef.current = true
      }
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading RL metrics...</p>
        </div>
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="card">
        <p className="text-danger-600">{error || 'Failed to load RL metrics'}</p>
      </div>
    )
  }

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  // Prepare action distribution data for pie chart
  const actionData = Object.entries(metrics.action_distribution || {}).map(([name, value]) => ({
    name,
    value
  }))

  // Prepare Q-value trend data
  const qValueData = metrics.q_value_history?.map(item => ({
    episode: item.episode,
    qValue: item.q_value,
    reward: item.reward
  })) || []

  // Prepare epsilon decay data
  const epsilonData = metrics.epsilon_history?.map(item => ({
    episode: item.episode,
    epsilon: item.epsilon
  })) || []

  // Prepare success rate history data
  const successRateData = metrics.success_rate_history?.map(item => ({
    episode: item.episode,
    successRate: item.success_rate * 100, // Convert to percentage
    windowSize: item.window_size
  })) || []

  // Prepare reward trend data
  const rewardTrendData = qValueData.map(item => ({
    episode: item.episode,
    reward: item.reward
  }))

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">RL Agent Metrics</h1>
            <p className="text-gray-600 text-lg">Reinforcement Learning performance and parameters</p>
          </div>
        </div>
        
        {/* Simulation Filter - More Prominent */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="w-5 h-5 text-primary-600" />
              <label className="text-sm font-semibold text-gray-700">
                Filter by Simulation:
              </label>
            </div>
            <select
              value={selectedSimulation || ''}
              onChange={(e) => setSelectedSimulation(e.target.value || null)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent shadow-sm hover:shadow-md transition-shadow font-medium"
            >
              <option value="">All Simulations (Global Metrics)</option>
              {simulations.map((sim) => (
                <option key={sim.id} value={sim.id}>
                  {sim.name} - {sim.status} - {sim.episodes} episodes
                </option>
              ))}
            </select>
            {selectedSimulation && (
              <div className="text-sm text-gray-600">
                <span className="font-medium">Showing metrics for:</span>{' '}
                <span className="text-primary-600 font-semibold">
                  {simulations.find(s => s.id === selectedSimulation)?.name || selectedSimulation}
                </span>
              </div>
            )}
            {!selectedSimulation && (
              <div className="text-sm text-gray-500 italic">
                Showing aggregated metrics across all simulations
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Key Parameters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Learning Status Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className={`bg-gradient-to-br p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow ${
              metrics.statistics.is_learning 
                ? 'from-green-100 to-green-200' 
                : 'from-gray-100 to-gray-200'
            }`}>
              <Activity className={`w-7 h-7 ${
                metrics.statistics.is_learning ? 'text-green-600' : 'text-gray-600'
              }`} />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Learning Status</p>
              <p className={`text-2xl font-bold ${
                metrics.statistics.is_learning ? 'text-green-600' : 'text-gray-600'
              }`}>
                {metrics.statistics.is_learning ? '✓ Learning' : '○ Not Learning'}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">
            {metrics.statistics.is_learning 
              ? `Active learning with ${metrics.statistics.update_count} Q-value updates`
              : 'No learning updates yet - start simulations to begin learning'
            }
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-blue-100 to-blue-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <Brain className="w-7 h-7 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Learning Rate</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.parameters.learning_rate}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Alpha (α) - Controls Q-value update speed</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-yellow-100 to-yellow-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <Target className="w-7 h-7 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Current Epsilon</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.statistics.current_epsilon.toFixed(4)}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Exploration rate (ε) - {metrics.exploration_ratio.exploration}/{metrics.exploration_ratio.exploration + metrics.exploration_ratio.exploitation} recent explorations</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-purple-100 to-purple-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <TrendingDown className="w-7 h-7 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Epsilon Decay</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.parameters.epsilon_decay}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Decay factor per episode</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.4 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-green-100 to-green-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <Activity className="w-7 h-7 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Discount Factor</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.parameters.discount_factor}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Gamma (γ) - Future reward importance</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.5 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-red-100 to-red-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <Zap className="w-7 h-7 text-red-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Min Epsilon</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.parameters.min_epsilon}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Minimum exploration rate</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.6 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-indigo-100 to-indigo-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <BarChart3 className="w-7 h-7 text-indigo-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">States Learned</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.statistics.num_states}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Unique states in Q-table</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.7 }}
          whileHover={{ scale: 1.02, y: -4 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-center space-x-4 mb-4">
            <div className="bg-gradient-to-br from-emerald-100 to-emerald-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
              <TrendingUp className="w-7 h-7 text-emerald-600" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Max Q-Value</p>
              <p className="text-3xl font-bold text-gray-900">{metrics.statistics.max_q_value?.toFixed(3) || '0.000'}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500 leading-relaxed">Highest Q-value across all states (from improved RL core)</p>
        </motion.div>
      </div>

      {/* Performance Metrics Section */}
      {metrics.performance_metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.8 }}
            whileHover={{ scale: 1.02, y: -4 }}
            className="card group cursor-pointer"
          >
            <div className="flex items-center space-x-4 mb-4">
              <div className="bg-gradient-to-br from-green-100 to-green-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
                <CheckCircle2 className="w-7 h-7 text-green-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Success Rate</p>
                <p className="text-3xl font-bold text-gray-900">
                  {(metrics.performance_metrics.success_rate * 100).toFixed(1)}%
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {metrics.performance_metrics.success_trend > 0 ? (
                <TrendingUp className="w-4 h-4 text-green-600" />
              ) : metrics.performance_metrics.success_trend < 0 ? (
                <TrendingDown className="w-4 h-4 text-red-600" />
              ) : null}
              <p className="text-xs text-gray-500">
                {metrics.performance_metrics.success_trend > 0 ? '+' : ''}
                {(metrics.performance_metrics.success_trend * 100).toFixed(1)}% trend
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.9 }}
            whileHover={{ scale: 1.02, y: -4 }}
            className="card group cursor-pointer"
          >
            <div className="flex items-center space-x-4 mb-4">
              <div className="bg-gradient-to-br from-blue-100 to-blue-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
                <Award className="w-7 h-7 text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Avg Reward</p>
                <p className="text-3xl font-bold text-gray-900">
                  {metrics.performance_metrics.avg_reward.toFixed(3)}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              {metrics.performance_metrics.reward_trend > 0 ? (
                <TrendingUp className="w-4 h-4 text-green-600" />
              ) : metrics.performance_metrics.reward_trend < 0 ? (
                <TrendingDown className="w-4 h-4 text-red-600" />
              ) : null}
              <p className="text-xs text-gray-500">
                Range: {metrics.performance_metrics.min_reward.toFixed(2)} to {metrics.performance_metrics.max_reward.toFixed(2)}
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.0 }}
            whileHover={{ scale: 1.02, y: -4 }}
            className="card group cursor-pointer"
          >
            <div className="flex items-center space-x-4 mb-4">
              <div className="bg-gradient-to-br from-yellow-100 to-yellow-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
                <AlertTriangle className="w-7 h-7 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">False Positive Rate</p>
                <p className="text-3xl font-bold text-gray-900">
                  {(metrics.performance_metrics.false_positive_rate * 100).toFixed(1)}%
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500">Lower is better</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 1.1 }}
            whileHover={{ scale: 1.02, y: -4 }}
            className="card group cursor-pointer"
          >
            <div className="flex items-center space-x-4 mb-4">
              <div className="bg-gradient-to-br from-orange-100 to-orange-200 p-4 rounded-xl shadow-sm group-hover:shadow-md transition-shadow">
                <Clock className="w-7 h-7 text-orange-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Avg Response Time</p>
                <p className="text-3xl font-bold text-gray-900">
                  {metrics.performance_metrics.avg_response_time.toFixed(1)}s
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500">Time to remediate incidents</p>
          </motion.div>
        </div>
      )}

      {/* Statistics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Episodes', value: metrics.statistics.episode_count, color: 'blue' },
          { label: 'Q-Value Updates', value: metrics.statistics.update_count, color: 'purple' },
          { label: 'Avg Q-Value', value: metrics.statistics.avg_q_value.toFixed(3), color: 'green' },
          { label: 'Max Q-Value', value: (metrics.statistics.max_q_value || 0).toFixed(3), color: 'emerald' },
        ].map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.7 + index * 0.1 }}
            whileHover={{ scale: 1.05, y: -4 }}
            className="card group cursor-pointer"
          >
            <p className="text-sm font-semibold text-gray-600 mb-2 uppercase tracking-wide">{stat.label}</p>
            <p className="text-4xl font-bold text-gray-900">{stat.value}</p>
          </motion.div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Q-Value Trend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.1 }}
          className="card"
        >
          <h2 className="card-title mb-6">Q-Value Trend</h2>
          {qValueData.length > 0 ? (() => {
            // Calculate evenly spaced ticks to avoid clutter
            const episodes = qValueData.map(d => d.episode)
            const minEpisode = Math.min(...episodes)
            const maxEpisode = Math.max(...episodes)
            const range = maxEpisode - minEpisode
            
            // Determine interval based on range to show ~5-8 ticks
            let interval = 100
            if (range <= 100) interval = 20
            else if (range <= 200) interval = 50
            else if (range <= 500) interval = 100
            else if (range <= 1000) interval = 200
            else interval = 500
            
            const ticks = []
            for (let i = Math.ceil(minEpisode / interval) * interval; i <= maxEpisode; i += interval) {
              ticks.push(i)
            }
            
            return (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={qValueData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="episode" 
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    type="number"
                    scale="linear"
                    domain={[minEpisode, maxEpisode]}
                    tickCount={6}
                    allowDecimals={false}
                  />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  domain={['auto', 'auto']}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="qValue" 
                  stroke="#3b82f6" 
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#3b82f6' }}
                  activeDot={{ r: 5 }}
                  name="Q-Value" 
                />
              </LineChart>
            </ResponsiveContainer>
            )
          })() : (
            <div className="text-center py-12 text-gray-500">
              <p>No Q-value data yet</p>
              <p className="text-sm mt-2">Run simulations to see Q-value trends</p>
            </div>
          )}
        </motion.div>

        {/* Epsilon Decay */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.2 }}
          className="card"
        >
          <h2 className="card-title mb-6">Epsilon Decay Over Time</h2>
          {epsilonData.length > 0 ? (() => {
            // Calculate evenly spaced ticks to avoid clutter
            const episodes = epsilonData.map(d => d.episode)
            const minEpisode = Math.min(...episodes)
            const maxEpisode = Math.max(...episodes)
            const range = maxEpisode - minEpisode
            
            // Determine interval based on range to show ~5-8 ticks
            let interval = 100
            if (range <= 100) interval = 20
            else if (range <= 200) interval = 50
            else if (range <= 500) interval = 100
            else if (range <= 1000) interval = 200
            else interval = 500
            
            const ticks = []
            for (let i = Math.ceil(minEpisode / interval) * interval; i <= maxEpisode; i += interval) {
              ticks.push(i)
            }
            
            return (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={epsilonData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis 
                    dataKey="episode" 
                    stroke="#6b7280"
                    style={{ fontSize: '12px' }}
                    type="number"
                    scale="linear"
                    domain={[minEpisode, maxEpisode]}
                    tickCount={6}
                    allowDecimals={false}
                  />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  domain={[0, 1.1]}
                  tickFormatter={(value) => value.toFixed(2)}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value) => value.toFixed(4)}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="epsilon" 
                  stroke="#f59e0b" 
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#f59e0b' }}
                  activeDot={{ r: 5 }}
                  name="Epsilon" 
                />
              </LineChart>
            </ResponsiveContainer>
            )
          })() : (
            <div className="text-center py-12 text-gray-500">
              <p>No epsilon data yet</p>
              <p className="text-sm mt-2">Run simulations to see epsilon decay</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Action Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.3 }}
          className="card"
        >
          <h2 className="card-title mb-6">Action Distribution</h2>
          {actionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={actionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {actionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>No action data yet</p>
            </div>
          )}
        </motion.div>

        {/* Action Counts Bar Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4 }}
          className="card"
        >
          <h2 className="card-title mb-6">Action Selection Counts</h2>
          {actionData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={actionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>No action data yet</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* Performance Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Success Rate Over Time */}
        {successRateData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.4 }}
            className="card"
          >
            <h2 className="card-title mb-6">Success Rate Over Time</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={successRateData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="episode" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  type="number"
                  scale="linear"
                  allowDecimals={false}
                  label={{ value: 'Episode', position: 'insideBottom', offset: -5, style: { fill: '#6b7280' } }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                  label={{ value: 'Success Rate (%)', angle: -90, position: 'insideLeft', style: { fill: '#6b7280' } }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value) => [`${Number(value).toFixed(1)}%`, 'Success Rate']}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="successRate" 
                  stroke="#10b981" 
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#10b981' }}
                  activeDot={{ r: 5 }}
                  name="Success Rate (%)" 
                />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {/* Reward Trend Over Time */}
        {rewardTrendData.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.45 }}
            className="card"
          >
            <h2 className="card-title mb-6">Reward Trend Over Episodes</h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={rewardTrendData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis 
                  dataKey="episode" 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  type="number"
                  scale="linear"
                  allowDecimals={false}
                  label={{ value: 'Episode', position: 'insideBottom', offset: -5, style: { fill: '#6b7280' } }}
                />
                <YAxis 
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  domain={['auto', 'auto']}
                  label={{ value: 'Reward', angle: -90, position: 'insideLeft', style: { fill: '#6b7280' } }}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px'
                  }}
                  formatter={(value) => [Number(value).toFixed(3), 'Reward']}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="reward" 
                  stroke="#3b82f6" 
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#3b82f6' }}
                  activeDot={{ r: 5 }}
                  name="Reward" 
                />
              </LineChart>
            </ResponsiveContainer>
            {metrics.performance_metrics && (
              <div className="mt-4 text-xs text-gray-500 text-center">
                <p>
                  Avg: {metrics.performance_metrics.avg_reward.toFixed(3)} | 
                  Max: {metrics.performance_metrics.max_reward.toFixed(3)} | 
                  Min: {metrics.performance_metrics.min_reward.toFixed(3)}
                </p>
                {metrics.performance_metrics.reward_trend !== 0 && (
                  <p className="mt-1">
                    Trend: {metrics.performance_metrics.reward_trend > 0 ? '+' : ''}
                    {metrics.performance_metrics.reward_trend.toFixed(3)} 
                    ({metrics.performance_metrics.reward_trend > 0 ? 'Improving' : 'Declining'})
                  </p>
                )}
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* Exploration vs Exploitation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1.5 }}
        className="card"
      >
        <h2 className="card-title mb-6">Exploration vs Exploitation</h2>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Exploration</span>
              <span className="text-lg font-bold text-yellow-600">{metrics.exploration_ratio.exploration}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-yellow-500 h-4 rounded-full transition-all"
                style={{ width: `${metrics.exploration_ratio.ratio * 100}%` }}
              ></div>
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Exploitation</span>
              <span className="text-lg font-bold text-blue-600">{metrics.exploration_ratio.exploitation}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-blue-500 h-4 rounded-full transition-all"
                style={{ width: `${(1 - metrics.exploration_ratio.ratio) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Q-Value vs Reward Correlation */}
      {qValueData.length > 0 && (() => {
        // Prepare line chart data - sorted by episode
        const lineData = qValueData
          .filter(d => d.qValue != null && d.reward != null)
          .sort((a, b) => a.episode - b.episode)
          .map(d => ({
            episode: d.episode,
            qValue: d.qValue,
            reward: d.reward
          }))
        
        if (lineData.length === 0) {
          return null
        }
        
        // Calculate correlation coefficient
        const n = lineData.length
        const qMean = lineData.reduce((sum, d) => sum + d.qValue, 0) / n
        const rMean = lineData.reduce((sum, d) => sum + d.reward, 0) / n
        
        const qVariance = lineData.reduce((sum, d) => sum + Math.pow(d.qValue - qMean, 2), 0) / n
        const rVariance = lineData.reduce((sum, d) => sum + Math.pow(d.reward - rMean, 2), 0) / n
        
        const covariance = lineData.reduce((sum, d) => sum + (d.qValue - qMean) * (d.reward - rMean), 0) / n
        
        const correlation = covariance / (Math.sqrt(qVariance) * Math.sqrt(rVariance)) || 0
        
        // Calculate domains with proper padding
        const qValues = lineData.map(d => d.qValue)
        const rewards = lineData.map(d => d.reward)
        const episodes = lineData.map(d => d.episode)
        
        const qMin = Math.min(...qValues)
        const qMax = Math.max(...qValues)
        const qRange = qMax - qMin || 1
        const qPadding = qRange * 0.1
        
        const rMin = Math.min(...rewards)
        const rMax = Math.max(...rewards)
        const rRange = rMax - rMin || 2
        const rPadding = rRange * 0.1
        
        const minEpisode = Math.min(...episodes)
        const maxEpisode = Math.max(...episodes)
        
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.6 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="card-title mb-0">Q-Value vs Reward Correlation</h2>
              <div className="text-sm text-gray-600">
                <span className="font-semibold">Correlation: </span>
                <span className={`font-bold ${correlation > 0.5 ? 'text-green-600' : correlation > 0 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {correlation.toFixed(3)}
                </span>
                <span className="text-xs text-gray-500 ml-2">
                  ({correlation > 0.7 ? 'Strong' : correlation > 0.3 ? 'Moderate' : correlation > 0 ? 'Weak' : 'Negative'} correlation)
                </span>
              </div>
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart
                data={lineData}
                margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="episode"
                  stroke="#6b7280"
                  style={{ fontSize: '12px' }}
                  type="number"
                  scale="linear"
                  domain={[minEpisode, maxEpisode]}
                  tickCount={6}
                  allowDecimals={false}
                  label={{ value: 'Episode', position: 'insideBottom', offset: -5, style: { fill: '#6b7280' } }}
                />
                <YAxis
                  yAxisId="left"
                  stroke="#3b82f6"
                  style={{ fontSize: '12px' }}
                  domain={[qMin - qPadding, qMax + qPadding]}
                  label={{ value: 'Q-Value', angle: -90, position: 'insideLeft', style: { fill: '#3b82f6' } }}
                  tick={{ fill: '#3b82f6' }}
                />
                <YAxis
                  yAxisId="right"
                  orientation="right"
                  stroke="#10b981"
                  style={{ fontSize: '12px' }}
                  domain={[rMin - rPadding, rMax + rPadding]}
                  label={{ value: 'Reward', angle: 90, position: 'insideRight', style: { fill: '#10b981' } }}
                  tick={{ fill: '#10b981' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#fff',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    padding: '8px'
                  }}
                  formatter={(value, name) => {
                    if (name === 'qValue') return [`Q-Value: ${Number(value).toFixed(3)}`, 'Q-Value']
                    if (name === 'reward') return [`Reward: ${Number(value).toFixed(3)}`, 'Reward']
                    return [value, name]
                  }}
                />
                <Legend 
                  wrapperStyle={{ paddingTop: '20px' }}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="qValue"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#3b82f6' }}
                  activeDot={{ r: 5 }}
                  name="Q-Value"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="reward"
                  stroke="#10b981"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#10b981' }}
                  activeDot={{ r: 5 }}
                  name="Reward"
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="mt-4 text-xs text-gray-500 text-center">
              <p>Shows Q-Value and Reward trends over episodes. A positive correlation suggests the RL agent is learning to associate higher Q-values with better rewards.</p>
            </div>
          </motion.div>
        )
      })()}
    </div>
  )
}

export default RLMetrics

