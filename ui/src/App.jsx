import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Simulations from './pages/Simulations'
import Agents from './pages/Agents'
import Analytics from './pages/Analytics'
import EpisodeDetail from './pages/EpisodeDetail'
import Logs from './pages/Logs'
import RLMetrics from './pages/RLMetrics'
import Orchestration from './pages/Orchestration'

function App() {
  try {
    return (
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <Layout>
          <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/orchestration" element={<Orchestration />} />
          <Route path="/simulations" element={<Simulations />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/rl-metrics" element={<RLMetrics />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/episodes/:episodeNumber" element={<EpisodeDetail />} />
          </Routes>
        </Layout>
      </Router>
    )
  } catch (error) {
    console.error('App error:', error)
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        <h1>Error loading application</h1>
        <p>{error.message}</p>
        <pre>{error.stack}</pre>
      </div>
    )
  }
}

export default App

