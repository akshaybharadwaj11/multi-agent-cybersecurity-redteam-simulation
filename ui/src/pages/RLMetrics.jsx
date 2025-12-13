import React, { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Brain, TrendingUp, TrendingDown, Activity, Target, Zap, BarChart3 } from 'lucide-react'
import { getRLMetrics } from '../services/api'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const RLMetrics = () => {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const hasShownErrorRef = useRef(false)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 3000) // Refresh every 3 seconds
    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      const data = await getRLMetrics()
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

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">RL Agent Metrics</h1>
        <p className="text-gray-600 text-lg">Reinforcement Learning performance and parameters</p>
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
      </div>

      {/* Statistics Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {[
          { label: 'Total Episodes', value: metrics.statistics.episode_count, color: 'blue' },
          { label: 'Q-Value Updates', value: metrics.statistics.update_count, color: 'purple' },
          { label: 'Avg Q-Value', value: metrics.statistics.avg_q_value.toFixed(3), color: 'green' },
          { label: 'Exploration Ratio', value: `${(metrics.exploration_ratio.ratio * 100).toFixed(1)}%`, color: 'yellow' },
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
          {qValueData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={qValueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="episode" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="qValue" stroke="#3b82f6" strokeWidth={2} name="Q-Value" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
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
          {epsilonData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={epsilonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="episode" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="epsilon" stroke="#f59e0b" strokeWidth={2} name="Epsilon" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
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
      {qValueData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.6 }}
          className="card"
        >
          <h2 className="card-title mb-6">Q-Value vs Reward Correlation</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={qValueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="episode" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="qValue" stroke="#3b82f6" strokeWidth={2} name="Q-Value" />
              <Line yAxisId="right" type="monotone" dataKey="reward" stroke="#10b981" strokeWidth={2} name="Reward" />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      )}
    </div>
  )
}

export default RLMetrics

