import React, { useState, useEffect } from 'react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { getAnalytics } from '../services/api'

const MetricsChart = () => {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
    const interval = setInterval(loadMetrics, 5000) // Refresh every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const loadMetrics = async () => {
    try {
      const analytics = await getAnalytics('24h')
      
      if (analytics.performance_metrics && analytics.performance_metrics.length > 0) {
        setData(analytics.performance_metrics)
      } else {
        // If no data, show empty state
        setData([])
      }
    } catch (error) {
      console.error('Error loading metrics:', error)
      setData([])
    } finally {
      setLoading(false)
    }
  }

  // Show loading or empty state
  if (loading && data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="text-gray-500">Loading metrics...</div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="h-80 flex items-center justify-center">
        <div className="text-gray-500">No metrics data available. Run some simulations to see performance metrics.</div>
      </div>
    )
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorReward" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorDetection" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="time" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            domain={[0, 1]}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#fff', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px'
            }}
          />
          <Legend />
          <Area 
            type="monotone" 
            dataKey="reward" 
            stroke="#0ea5e9" 
            fillOpacity={1} 
            fill="url(#colorReward)"
            name="Avg Reward"
          />
          <Area 
            type="monotone" 
            dataKey="success" 
            stroke="#22c55e" 
            fillOpacity={1} 
            fill="url(#colorSuccess)"
            name="Success Rate"
          />
          <Area 
            type="monotone" 
            dataKey="detection" 
            stroke="#ef4444" 
            fillOpacity={1} 
            fill="url(#colorDetection)"
            name="Detection Rate"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default MetricsChart

