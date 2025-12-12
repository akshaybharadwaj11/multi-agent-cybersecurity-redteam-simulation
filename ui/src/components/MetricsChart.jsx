import React from 'react'
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

const MetricsChart = () => {
  // Sample data - in real app, this would come from API
  const data = [
    { time: '00:00', reward: 0.45, success: 0.65, detection: 0.72 },
    { time: '01:00', reward: 0.52, success: 0.68, detection: 0.75 },
    { time: '02:00', reward: 0.48, success: 0.70, detection: 0.78 },
    { time: '03:00', reward: 0.55, success: 0.72, detection: 0.80 },
    { time: '04:00', reward: 0.58, success: 0.75, detection: 0.82 },
    { time: '05:00', reward: 0.62, success: 0.78, detection: 0.85 },
    { time: '06:00', reward: 0.65, success: 0.80, detection: 0.88 },
  ]

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

