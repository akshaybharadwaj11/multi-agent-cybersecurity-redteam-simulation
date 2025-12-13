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
            <p className="text-2xl font-bold">
              {episode.duration && episode.duration > 0 
                ? `${episode.duration.toFixed(2)}s` 
                : '0.0s'}
            </p>
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

      {/* RAG Context */}
      {episode.rag_context && (
        <div className="card">
          <h2 className="card-title mb-4">RAG Retrieval Results</h2>
          <div className="space-y-4">
            {episode.rag_context.runbooks && episode.rag_context.runbooks.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  Runbooks Retrieved ({episode.rag_context.runbooks.length})
                </h3>
                <div className="space-y-2">
                  {episode.rag_context.runbooks.map((rb, i) => (
                    <div key={i} className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-blue-900">{rb.title}</span>
                        {rb.technique_id && (
                          <span className="text-xs text-blue-700 bg-blue-100 px-2 py-1 rounded">
                            {rb.technique_id}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-blue-800">{rb.description}</p>
                      {rb.steps && rb.steps.length > 0 && (
                        <div className="mt-2 text-xs text-blue-700">
                          <span className="font-medium">Steps: </span>
                          {rb.steps.slice(0, 3).join(', ')}
                          {rb.steps.length > 3 && ` +${rb.steps.length - 3} more`}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {episode.rag_context.threat_intel && episode.rag_context.threat_intel.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">
                  Threat Intelligence Retrieved ({episode.rag_context.threat_intel.length})
                </h3>
                <div className="space-y-2">
                  {episode.rag_context.threat_intel.map((ti, i) => (
                    <div key={i} className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-yellow-900">{ti.title}</span>
                        {ti.severity && (
                          <span className={`text-xs px-2 py-1 rounded ${
                            ti.severity === 'high' ? 'bg-red-100 text-red-700' :
                            ti.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {ti.severity}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-yellow-800">{ti.description}</p>
                      {ti.technique_id && (
                        <span className="text-xs text-yellow-700 mt-1 inline-block">
                          MITRE: {ti.technique_id}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* RL Decision with Q-Values and Comparison */}
      {episode.rl_decision && (
        <div className="card">
          <h2 className="card-title mb-4">RL Agent Decision</h2>
          
          {/* Decision Summary */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div>
              <p className="text-sm text-gray-600">Selected Action</p>
              <p className="font-semibold text-lg">{episode.rl_decision.selected_action?.replace('_', ' ').toUpperCase()}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Mode</p>
              <p className={`font-semibold text-lg ${
                episode.rl_decision.is_exploration ? 'text-yellow-600' : 'text-green-600'
              }`}>
                {episode.rl_decision.is_exploration ? 'Exploration' : 'Exploitation'}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Epsilon (Exploration Rate)</p>
              <p className="font-semibold text-lg">{episode.rl_decision.epsilon?.toFixed(4)}</p>
            </div>
          </div>

          {/* Q-Values for All Actions */}
          {episode.rl_decision.q_values && Object.keys(episode.rl_decision.q_values).length > 0 && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Q-Values (Expected Rewards)</h3>
              <div className="space-y-2">
                {Object.entries(episode.rl_decision.q_values)
                  .sort((a, b) => b[1] - a[1]) // Sort by Q-value descending
                  .map(([action, qValue]) => {
                    const isSelected = action === episode.rl_decision.selected_action
                    const isRecommended = episode.remediation?.recommended_action?.toLowerCase() === action.toLowerCase()
                    return (
                      <div
                        key={action}
                        className={`p-3 rounded-lg border-2 ${
                          isSelected
                            ? 'bg-blue-50 border-blue-400'
                            : isRecommended
                            ? 'bg-green-50 border-green-300'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-medium text-gray-900">
                              {action.replace('_', ' ').toUpperCase()}
                            </span>
                            {isSelected && (
                              <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">SELECTED</span>
                            )}
                            {isRecommended && !isSelected && (
                              <span className="text-xs bg-green-600 text-white px-2 py-1 rounded">RECOMMENDED</span>
                            )}
                          </div>
                          <span className={`font-semibold ${
                            qValue > 0 ? 'text-green-600' : qValue < 0 ? 'text-red-600' : 'text-gray-600'
                          }`}>
                            {qValue.toFixed(3)}
                          </span>
                        </div>
                      </div>
                    )
                  })}
              </div>
            </div>
          )}

          {/* Why RL Chose Differently */}
          {episode.remediation?.recommended_action && 
           episode.rl_decision.selected_action &&
           episode.remediation.recommended_action.toLowerCase() !== episode.rl_decision.selected_action.toLowerCase() && (
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <h3 className="font-semibold text-yellow-900 mb-2">Why RL Chose Differently</h3>
              <div className="text-sm text-yellow-800 space-y-2">
                <p>
                  <strong>Remediation Agent Recommended:</strong> {episode.remediation.recommended_action.replace('_', ' ').toUpperCase()}
                  {episode.remediation.options?.find(opt => opt.action.toLowerCase() === episode.remediation.recommended_action.toLowerCase()) && (
                    <span className="ml-2">
                      (Confidence: {(episode.remediation.options.find(opt => opt.action.toLowerCase() === episode.remediation.recommended_action.toLowerCase()).confidence * 100).toFixed(0)}%)
                    </span>
                  )}
                </p>
                <p>
                  <strong>RL Agent Selected:</strong> {episode.rl_decision.selected_action.replace('_', ' ').toUpperCase()}
                  {episode.rl_decision.q_values && episode.rl_decision.q_values[episode.rl_decision.selected_action] !== undefined && (
                    <span className="ml-2">
                      (Q-value: {episode.rl_decision.q_values[episode.rl_decision.selected_action].toFixed(3)})
                    </span>
                  )}
                </p>
                <div className="mt-3 p-3 bg-white rounded border border-yellow-200">
                  <p className="font-medium mb-1">Explanation:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    {episode.rl_decision.is_exploration ? (
                      <li>The RL agent is <strong>exploring</strong> (random action) to learn about different actions' effectiveness</li>
                    ) : (
                      <li>The RL agent is <strong>exploiting</strong> its learned knowledge (Q-values) to select the action with highest expected reward</li>
                    )}
                    <li>The RL agent learns from <strong>past rewards</strong>, not just the current incident analysis</li>
                    <li>If the selected action has a higher Q-value, it means the RL agent has learned from experience that this action typically yields better rewards</li>
                    <li>As the RL agent learns more (more episodes), it will better align with remediation recommendations</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default EpisodeDetail

