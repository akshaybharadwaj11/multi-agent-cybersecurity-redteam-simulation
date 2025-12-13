import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { getSimulationStatus } from '../services/api'
import { 
  Activity, 
  Shield, 
  AlertTriangle, 
  CheckCircle,
  TrendingUp,
  Zap,
  Clock,
  Target
} from 'lucide-react'
import StatCard from '../components/StatCard'
import AgentFlow from '../components/AgentFlow'
import RecentSimulations from '../components/RecentSimulations'
import MetricsChart from '../components/MetricsChart'
import AgentOrchestrationGraph from '../components/AgentOrchestrationGraph'
import { getDashboardStats, getRecentSimulations } from '../services/api'

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalEpisodes: 0,
    successRate: 0,
    avgReward: 0,
    activeSimulations: 0,
    totalDetections: 0,
    avgResponseTime: 0,
  })
  const [recentSims, setRecentSims] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeSimulationId, setActiveSimulationId] = useState(null)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 3000) // Refresh every 3 seconds for real-time updates
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [statsData, simsData] = await Promise.all([
        getDashboardStats().catch(err => {
          console.error('Error loading stats:', err)
          return {
            totalEpisodes: 0,
            successRate: 0,
            avgReward: 0,
            activeSimulations: 0,
            totalDetections: 0,
            avgResponseTime: 0,
          }
        }),
        getRecentSimulations(5).catch(err => {
          console.error('Error loading simulations:', err)
          return []
        })
      ])
      setStats(statsData)
      setRecentSims(simsData)
      
      // Set active simulation if one is running
      const runningSim = simsData.find(s => s.status === 'running')
      if (runningSim) {
        setActiveSimulationId(runningSim.id)
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      // Set zeros/empty on error - NO MOCK DATA
      setStats({
        totalEpisodes: 0,
        successRate: 0,
        avgReward: 0,
        activeSimulations: 0,
        totalDetections: 0,
        avgResponseTime: 0,
      })
      setRecentSims([])
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    {
      title: 'Total Episodes',
      value: stats.totalEpisodes.toLocaleString(),
      icon: Activity,
      color: 'primary',
      change: '+12%',
      trend: 'up'
    },
    {
      title: 'Success Rate',
      value: `${(stats.successRate * 100).toFixed(1)}%`,
      icon: CheckCircle,
      color: 'success',
      change: '+5.2%',
      trend: 'up'
    },
    {
      title: 'Avg Reward',
      value: stats.avgReward.toFixed(3),
      icon: TrendingUp,
      color: 'primary',
      change: '+0.15',
      trend: 'up'
    },
    {
      title: 'Active Simulations',
      value: stats.activeSimulations,
      icon: Zap,
      color: 'warning',
      change: '2 running',
      trend: 'neutral'
    },
    {
      title: 'Total Detections',
      value: stats.totalDetections.toLocaleString(),
      icon: Shield,
      color: 'danger',
      change: '+23',
      trend: 'up'
    },
    {
      title: 'Avg Response Time',
      value: `${stats.avgResponseTime.toFixed(1)}s`,
      icon: Clock,
      color: 'primary',
      change: '-2.3s',
      trend: 'down'
    },
  ]

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2 gradient-text">
            Dashboard
          </h1>
          <p className="text-gray-600 text-lg">Real-time overview of your cyber defense simulation</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2.5 px-5 py-2.5 bg-white/80 backdrop-blur-sm rounded-xl border border-green-200/50 shadow-sm">
            <div className="relative">
              <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse"></div>
              <div className="absolute inset-0 w-2.5 h-2.5 bg-green-500 rounded-full animate-ping opacity-75"></div>
            </div>
            <span className="text-sm font-semibold text-gray-700">Live</span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <StatCard {...stat} loading={loading} />
          </motion.div>
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Agent Flow - Takes 2 columns */}
        <div className="lg:col-span-2">
          <AgentFlow 
            simulationId={activeSimulationId} 
            onSimulationStart={(simId) => {
              setActiveSimulationId(simId)
              // Reload data to show the new simulation
              loadData()
            }}
          />
        </div>

        {/* Recent Simulations - Takes 1 column */}
        <div className="lg:col-span-1">
          <RecentSimulations simulations={recentSims} loading={loading} />
        </div>
      </div>

      {/* Agent Orchestration Graph */}
      <div className="card p-0 overflow-hidden">
        <AgentOrchestrationGraph 
          simulationId={activeSimulationId}
        />
      </div>

      {/* Metrics Chart */}
      <div className="card">
        <div className="card-header">
          <h2 className="card-title">Performance Metrics</h2>
        </div>
        <MetricsChart />
      </div>
    </div>
  )
}

export default Dashboard

