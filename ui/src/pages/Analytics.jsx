import React, { useState, useEffect } from 'react'
import { getAnalytics } from '../services/api'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('24h')
  const [analyticsData, setAnalyticsData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadAnalytics()
    let interval = null
    
    const handleVisibilityChange = () => {
      if (document.hidden) {
        if (interval) {
          clearInterval(interval)
          interval = null
        }
      } else {
        if (!interval) {
          loadAnalytics()
          interval = setInterval(loadAnalytics, 15000)
        }
      }
    }
    
    if (!document.hidden) {
      interval = setInterval(loadAnalytics, 15000)
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      if (interval) clearInterval(interval)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [timeRange])

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      const data = await getAnalytics(timeRange)
      setAnalyticsData(data)
    } catch (error) {
      console.error('Failed to load analytics:', error)
      setAnalyticsData({ episodes: [], rewards: [], actions: [] })
    } finally {
      setLoading(false)
    }
  }

  const rewardData = analyticsData?.rewards || [
    { episode: 1, reward: 0.45 },
    { episode: 2, reward: 0.52 },
    { episode: 3, reward: 0.48 },
    { episode: 4, reward: 0.55 },
    { episode: 5, reward: 0.58 },
    { episode: 6, reward: 0.62 },
    { episode: 7, reward: 0.65 },
    { episode: 8, reward: 0.68 },
    { episode: 9, reward: 0.70 },
    { episode: 10, reward: 0.72 },
  ]

  const actionDistribution = analyticsData?.actions?.map((action, index) => ({
    name: action.name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
    value: action.value,
    color: ['#ef4444', '#f59e0b', '#3b82f6', '#8b5cf6', '#10b981'][index % 5]
  })) || []

  // Calculate attack type data from episodes if available
  const attackTypeData = analyticsData?.attackTypes || []

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-1">Detailed performance metrics and insights</p>
        </div>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
        >
          <option value="1h">Last Hour</option>
          <option value="24h">Last 24 Hours</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
        </select>
      </div>

      {/* Reward Trend */}
      <div className="card">
        <h2 className="card-title mb-4">Reward Trend Over Time</h2>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rewardData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="episode" stroke="#6b7280" />
              <YAxis stroke="#6b7280" />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="reward"
                stroke="#0ea5e9"
                strokeWidth={2}
                name="Average Reward"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Action Distribution */}
        <div className="card">
          <h2 className="card-title mb-4">Action Distribution</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={actionDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {actionDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Attack Type Performance */}
        <div className="card">
          <h2 className="card-title mb-4">Attack Type Performance</h2>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={attackTypeData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="type" stroke="#6b7280" />
                <YAxis stroke="#6b7280" />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" name="Total Attacks" />
                <Bar dataKey="success" fill="#22c55e" name="Successful Defenses" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Analytics

