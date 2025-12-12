import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Shield, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'
import { getEpisodeDetails } from '../services/api'

const EpisodeDetail = () => {
  const { episodeNumber } = useParams()
  const navigate = useNavigate()
  const [episode, setEpisode] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadEpisode()
  }, [episodeNumber])

  const loadEpisode = async () => {
    try {
      setLoading(true)
      const data = await getEpisodeDetails(episodeNumber)
      setEpisode(data)
    } catch (err) {
      setError(err.message || 'Failed to load episode')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (error || !episode) {
    return (
      <div className="card">
        <p className="text-danger-600">{error || 'Episode not found'}</p>
        <button onClick={() => navigate(-1)} className="btn btn-secondary mt-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <button onClick={() => navigate(-1)} className="btn btn-secondary">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Episode {episode.episode_number}</h1>
          <p className="text-gray-600">Detailed episode information</p>
        </div>
      </div>

      {/* Outcome Summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="card-title">Outcome</h2>
          {episode.outcome?.success ? (
            <span className="badge bg-success-100 text-success-700 border-success-300">
              <CheckCircle className="w-4 h-4 mr-1" />
              Success
            </span>
          ) : (
            <span className="badge bg-danger-100 text-danger-700 border-danger-300">
              <XCircle className="w-4 h-4 mr-1" />
              Failed
            </span>
          )}
        </div>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-600">Reward</p>
            <p className="text-2xl font-bold">{episode.reward.toFixed(3)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Duration</p>
            <p className="text-2xl font-bold">{episode.duration.toFixed(1)}s</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">False Positive</p>
            <p className="text-2xl font-bold">{episode.outcome?.false_positive ? 'Yes' : 'No'}</p>
          </div>
        </div>
      </div>

      {/* Attack Scenario */}
      {episode.attack_scenario && (
        <div className="card">
          <h2 className="card-title mb-4">Attack Scenario</h2>
          <div className="space-y-2 mb-4">
            <p><span className="font-medium">Type:</span> {episode.attack_scenario.type}</p>
            <p><span className="font-medium">Target:</span> {episode.attack_scenario.target}</p>
          </div>
          <div>
            <h3 className="font-semibold mb-2">Attack Steps:</h3>
            <div className="space-y-2">
              {episode.attack_scenario.steps.map((step) => (
                <div key={step.step_number} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="font-medium">Step {step.step_number}:</span>
                    <span className="text-sm text-gray-600">{step.technique_name}</span>
                    <span className="text-xs text-gray-500">({step.technique_id})</span>
                  </div>
                  <p className="text-sm text-gray-700">{step.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Incident Report */}
      {episode.incident_report && (
        <div className="card">
          <h2 className="card-title mb-4">Incident Report</h2>
          <div className="space-y-3">
            <div>
              <span className="font-medium">Severity:</span>
              <span className={`ml-2 badge ${
                episode.incident_report.severity === 'critical' ? 'bg-danger-100 text-danger-700' :
                episode.incident_report.severity === 'high' ? 'bg-yellow-100 text-yellow-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {episode.incident_report.severity}
              </span>
            </div>
            <div>
              <span className="font-medium">Confidence:</span>
              <span className="ml-2">{(episode.incident_report.confidence * 100).toFixed(1)}%</span>
            </div>
            <div>
              <p className="font-medium mb-1">Summary:</p>
              <p className="text-gray-700">{episode.incident_report.summary}</p>
            </div>
            {episode.incident_report.mitre_techniques.length > 0 && (
              <div>
                <p className="font-medium mb-1">MITRE Techniques:</p>
                <div className="flex flex-wrap gap-2">
                  {episode.incident_report.mitre_techniques.map((tech, i) => (
                    <span key={i} className="badge bg-primary-100 text-primary-700">
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Remediation */}
      {episode.remediation && (
        <div className="card">
          <h2 className="card-title mb-4">Remediation Plan</h2>
          <div className="space-y-3">
            <div>
              <span className="font-medium">Recommended Action:</span>
              <span className="ml-2 badge bg-success-100 text-success-700">
                {episode.remediation.recommended_action?.replace('_', ' ').toUpperCase()}
              </span>
            </div>
            <div>
              <p className="font-medium mb-2">Action Options:</p>
              <div className="space-y-2">
                {episode.remediation.options.map((opt, i) => (
                  <div key={i} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium">{opt.action.replace('_', ' ').toUpperCase()}</span>
                      <span className="text-sm text-gray-600">Confidence: {(opt.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-sm text-gray-700">{opt.description}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* RL Decision */}
      {episode.rl_decision && (
        <div className="card">
          <h2 className="card-title mb-4">RL Agent Decision</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Selected Action</p>
              <p className="font-semibold">{episode.rl_decision.selected_action?.replace('_', ' ').toUpperCase()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Mode</p>
              <p className="font-semibold">{episode.rl_decision.is_exploration ? 'Exploration' : 'Exploitation'}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Epsilon</p>
              <p className="font-semibold">{episode.rl_decision.epsilon.toFixed(4)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default EpisodeDetail

