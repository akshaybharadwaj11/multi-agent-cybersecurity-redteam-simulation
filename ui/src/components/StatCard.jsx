import React from 'react'
import { motion } from 'framer-motion'

const StatCard = ({ title, value, icon: Icon, color = 'primary', change, trend, loading = false }) => {
  const colorClasses = {
    primary: {
      bg: 'bg-gradient-to-br from-blue-50 to-blue-100/50',
      icon: 'text-blue-600',
      border: 'border-blue-200/50',
      glow: 'shadow-blue-500/10',
    },
    success: {
      bg: 'bg-gradient-to-br from-green-50 to-green-100/50',
      icon: 'text-green-600',
      border: 'border-green-200/50',
      glow: 'shadow-green-500/10',
    },
    warning: {
      bg: 'bg-gradient-to-br from-yellow-50 to-yellow-100/50',
      icon: 'text-yellow-600',
      border: 'border-yellow-200/50',
      glow: 'shadow-yellow-500/10',
    },
    danger: {
      bg: 'bg-gradient-to-br from-red-50 to-red-100/50',
      icon: 'text-red-600',
      border: 'border-red-200/50',
      glow: 'shadow-red-500/10',
    },
  }

  const colors = colorClasses[color] || colorClasses.primary

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="card"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="h-4 w-24 skeleton rounded"></div>
          <div className="h-10 w-10 skeleton rounded-lg"></div>
        </div>
        <div className="h-8 w-32 skeleton rounded mb-2"></div>
        <div className="h-4 w-20 skeleton rounded"></div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4, transition: { duration: 0.2 } }}
      className={`
        card relative overflow-hidden
        ${colors.glow} hover:shadow-xl
        group cursor-pointer
      `}
    >
      {/* Decorative gradient overlay */}
      <div className={`absolute top-0 right-0 w-32 h-32 ${colors.bg} rounded-full blur-3xl opacity-20 group-hover:opacity-30 transition-opacity`}></div>
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-600 uppercase tracking-wide">
            {title}
          </h3>
          <div className={`
            p-3 rounded-xl ${colors.bg} border ${colors.border}
            group-hover:scale-110 transition-transform duration-200
          `}>
            <Icon className={`w-5 h-5 ${colors.icon}`} />
          </div>
        </div>
        
        <div className="mb-2">
          <p className="text-3xl font-bold text-gray-900 mb-1">
            {value}
          </p>
          {change && (
            <div className="flex items-center space-x-1">
              {trend === 'up' ? (
                <span className="text-xs font-semibold text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
                  ↗ {change}
                </span>
              ) : trend === 'down' ? (
                <span className="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
                  ↘ {change}
                </span>
              ) : (
                <span className="text-xs font-semibold text-gray-600 bg-gray-50 px-2 py-0.5 rounded-full">
                  {change}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}

export default StatCard
