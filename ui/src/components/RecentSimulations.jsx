import React from 'react'
import { motion } from 'framer-motion'
import { Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { formatDistanceToNow, parseISO } from 'date-fns'

const RecentSimulations = ({ simulations, loading }) => {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-success-600" />
      case 'failed':
        return <XCircle className="w-4 h-4 text-danger-600" />
      case 'running':
        return <Clock className="w-4 h-4 text-primary-600 animate-spin" />
      default:
        return <AlertTriangle className="w-4 h-4 text-yellow-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'bg-success-50 text-success-700 border-success-200'
      case 'failed':
        return 'bg-danger-50 text-danger-700 border-danger-200'
      case 'running':
        return 'bg-primary-50 text-primary-700 border-primary-200'
      default:
        return 'bg-yellow-50 text-yellow-700 border-yellow-200'
    }
  }

  if (loading) {
    return (
      <div className="card">
        <h2 className="card-title mb-4">Recent Simulations</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    )
  }

  // NO DEFAULT/MOCK DATA - only show real simulations
  const sims = simulations

  return (
    <div className="card h-full">
      <h2 className="card-title mb-6">Recent Simulations</h2>
      {sims.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No simulations yet.</p>
          <p className="text-sm mt-2">Start a simulation to see results here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {sims.map((sim, index) => (
          <motion.div
            key={sim.id}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            whileHover={{ scale: 1.02, x: 4 }}
            className={`
              p-4 rounded-xl border-2 transition-all duration-200 hover:shadow-lg cursor-pointer
              ${getStatusColor(sim.status)}
            `}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                {getStatusIcon(sim.status)}
                <span className="font-semibold">{sim.attackType}</span>
              </div>
              <span className="text-xs text-gray-600">
                {sim.timestamp 
                  ? formatDistanceToNow(
                      typeof sim.timestamp === 'string' 
                        ? parseISO(sim.timestamp) 
                        : new Date(sim.timestamp),
                      { addSuffix: true }
                    )
                  : 'Unknown'
                }
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">{sim.episodes} episodes</span>
              <span className="font-medium">
                {(sim.successRate * 100).toFixed(0)}% success
              </span>
            </div>
          </motion.div>
        ))}
        </div>
      )}
    </div>
  )
}

export default RecentSimulations

