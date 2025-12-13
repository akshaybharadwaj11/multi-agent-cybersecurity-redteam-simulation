import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  PlayCircle, 
  Users, 
  BarChart3,
  Menu,
  X,
  Shield,
  Terminal,
  Brain,
  Activity
} from 'lucide-react'

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const location = useLocation()

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/orchestration', icon: Activity, label: 'Orchestration' },
    { path: '/simulations', icon: PlayCircle, label: 'Simulations' },
    { path: '/agents', icon: Users, label: 'Agents' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/rl-metrics', icon: Brain, label: 'RL Metrics' },
    { path: '/logs', icon: Terminal, label: 'Logs' },
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 via-blue-50/30 to-gray-50 overflow-hidden">
      {/* Sidebar */}
      <aside className={`
        ${sidebarOpen ? 'w-64' : 'w-20'} 
        bg-gradient-to-b from-gray-900 via-gray-900 to-gray-800 text-white 
        transition-all duration-300 ease-in-out
        flex flex-col shadow-2xl border-r border-gray-700/50
        backdrop-blur-xl
      `}>
        {/* Logo */}
        <div className={`relative flex flex-col border-b border-gray-700/50 bg-gray-800/50 transition-all duration-300 ${
          sidebarOpen ? 'p-6' : 'p-4'
        }`}>
          <div className={`flex items-center ${sidebarOpen ? 'justify-between' : 'flex-col space-y-3'}`}>
            <div className={`flex items-center ${sidebarOpen ? 'space-x-3' : 'justify-center'}`}>
              <div className="bg-gradient-to-br from-primary-500 to-blue-600 p-2.5 rounded-xl shadow-lg shadow-primary-500/30">
                <Shield className="w-6 h-6 text-white" />
              </div>
              {sidebarOpen && (
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
                    CyberDefense
                  </h1>
                  <p className="text-xs text-gray-400 font-medium">Simulator</p>
                </div>
              )}
            </div>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-gray-700/50 rounded-lg transition-all duration-200 active:scale-95"
              aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
              title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  group relative flex items-center rounded-xl transition-all duration-200
                  ${sidebarOpen 
                    ? 'px-4 py-3 space-x-3' 
                    : 'justify-center px-2 py-3'
                  }
                  ${active 
                    ? 'bg-gradient-to-r from-primary-600 to-blue-600 text-white shadow-lg shadow-primary-500/30 scale-[1.02]' 
                    : 'text-gray-300 hover:bg-gray-800/70 hover:text-white hover:scale-[1.01]'
                  }
                `}
                aria-current={active ? "page" : undefined}
                title={!sidebarOpen ? item.label : undefined}
              >
                <Icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-200 ${active ? 'scale-110' : 'group-hover:scale-110'}`} />
                {sidebarOpen && (
                  <>
                    <span className={`font-semibold transition-all duration-200 ${active ? 'text-white' : ''}`}>
                      {item.label}
                    </span>
                    {active && (
                      <div className="ml-auto w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
                    )}
                  </>
                )}
                {/* Tooltip for collapsed state */}
                {!sidebarOpen && (
                  <div className="absolute left-full ml-2 px-3 py-2 bg-gray-900 text-white text-sm rounded-lg shadow-xl opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity duration-200 whitespace-nowrap z-50">
                    {item.label}
                    <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900"></div>
                  </div>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Status Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-gray-700/50 bg-gray-800/30">
            <div className="flex items-center space-x-2.5 text-sm">
              <div className="relative">
                <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse"></div>
                <div className="absolute inset-0 w-2.5 h-2.5 bg-green-500 rounded-full animate-ping opacity-75"></div>
              </div>
              <span className="text-gray-300 font-medium">System Operational</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6 lg:p-8 max-w-7xl mx-auto w-full">
          <div className="animate-fadeIn">
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}

export default Layout

