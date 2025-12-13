import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  EdgeLabelRenderer,
  Handle,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { motion } from 'framer-motion'
import { 
  User, 
  FileText, 
  Search, 
  Brain, 
  Shield, 
  Zap,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowRight,
  Activity,
  Network
} from 'lucide-react'
import { getSimulationEpisodes, getEpisodeDetails } from '../services/api'

// Custom Node Component (defined before use)
function CustomNode({ data }) {
  const { label, role, icon: Icon, color, description, status, episodeData } = data
  const isActive = status === 'active'
  const isCompleted = status === 'completed'

  const getStatusIcon = () => {
    if (isActive) return <Clock className="w-4 h-4 text-blue-600 animate-spin" />
    if (isCompleted) return <CheckCircle className="w-4 h-4 text-green-600" />
    return <AlertCircle className="w-4 h-4 text-gray-400" />
  }

  const getStatusColor = () => {
    if (isActive) return 'border-blue-500 bg-blue-50 shadow-lg shadow-blue-500/20'
    if (isCompleted) return 'border-green-500 bg-green-50'
    return 'border-gray-300 bg-white'
  }

  return (
    <motion.div
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ 
        scale: isActive ? 1.05 : 1,
        opacity: 1,
      }}
      transition={{ duration: 0.3 }}
      className={`relative p-4 rounded-xl border-2 w-[280px] ${getStatusColor()} transition-all duration-300`}
    >
      {/* React Flow Handles */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#94a3b8', width: 8, height: 8 }}
      />
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#94a3b8', width: 8, height: 8 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#94a3b8', width: 8, height: 8 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#94a3b8', width: 8, height: 8 }}
      />
      
      {/* Status indicator */}
      <div className="absolute -top-2 -right-2">
        {getStatusIcon()}
      </div>

      {/* Icon and Label */}
      <div className="flex items-center space-x-3 mb-2">
        <div
          className="p-2 rounded-lg"
          style={{ backgroundColor: `${color}20`, color: color }}
        >
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <h4 className="font-bold text-gray-900 text-sm">{label}</h4>
          <p className="text-xs text-gray-600">{role}</p>
        </div>
      </div>

      {/* Description */}
      <p className="text-xs text-gray-600 mb-2">{description}</p>

      {/* Episode Data */}
      {episodeData && isCompleted && (
        <div className="mt-2 pt-2 border-t border-gray-200">
          {label === 'Red Team' && episodeData.attack_scenario && (
            <div className="text-xs">
              <span className="font-medium">Attack:</span>{' '}
              <span className="text-gray-700">
                {episodeData.attack_scenario.type?.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          )}
          {label === 'Detection' && episodeData.incident_report && (
            <div className="text-xs">
              <span className="font-medium">Severity:</span>{' '}
              <span className="text-gray-700 capitalize">
                {episodeData.incident_report.severity}
              </span>
            </div>
          )}
          {label === 'RAG Agent' && episodeData.rag_context && (
            <div className="text-xs">
              <span className="font-medium">Retrieved:</span>{' '}
              <span className="text-gray-700">
                {episodeData.rag_context.runbooks?.length || 0} runbooks,{' '}
                {episodeData.rag_context.threat_intel?.length || 0} intel items
              </span>
            </div>
          )}
          {label === 'Remediation' && episodeData.remediation && (
            <div className="text-xs">
              <span className="font-medium">Recommended:</span>{' '}
              <span className="text-gray-700">
                {episodeData.remediation.recommended_action?.replace('_', ' ').toUpperCase()}
              </span>
            </div>
          )}
          {label === 'RL Agent' && episodeData.rl_decision && (
            <div className="text-xs">
              <span className="font-medium">Selected:</span>{' '}
              <span className="text-gray-700">
                {episodeData.rl_decision.selected_action?.replace('_', ' ').toUpperCase()}
              </span>
              <div className="mt-1">
                <span className="text-xs text-gray-500">
                  {episodeData.rl_decision.is_exploration ? 'Exploration' : 'Exploitation'}
                </span>
              </div>
            </div>
          )}
          {label === 'Orchestrator' && episodeData && (
            <div className="text-xs">
              <span className="font-medium">Status:</span>{' '}
              <span className="text-gray-700">
                {episodeData.outcome ? 'Episode Complete' : 'Coordinating Agents'}
              </span>
              {episodeData.episode_number && (
                <div className="mt-1">
                  <span className="font-medium">Episode:</span>{' '}
                  <span className="text-gray-700">{episodeData.episode_number}</span>
                </div>
              )}
            </div>
          )}
          {label === 'Outcome' && episodeData.outcome && (
            <div className="text-xs">
              <span className="font-medium">Result:</span>{' '}
              <span className={episodeData.outcome.success ? 'text-green-600' : 'text-red-600'}>
                {episodeData.outcome.success ? 'Success' : 'Failure'}
              </span>
              {episodeData.reward && (
                <div className="mt-1">
                  <span className="font-medium">Reward:</span>{' '}
                  <span className="text-gray-700">{episodeData.reward.toFixed(3)}</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Active pulse effect */}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-xl"
          style={{ borderColor: color }}
          animate={{
            boxShadow: [
              `0 0 0 0 ${color}40`,
              `0 0 0 8px ${color}00`,
            ],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      )}
    </motion.div>
  )
}

const nodeTypes = {
  custom: CustomNode,
}

const AgentOrchestrationGraph = ({ simulationId = null, episodeNumber = null }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [currentStep, setCurrentStep] = useState(0)
  const [episodeData, setEpisodeData] = useState(null)
  const [isRunning, setIsRunning] = useState(false)
  const initializedRef = useRef(false)
  const lastEpisodeRef = useRef(null)
  const updateInProgressRef = useRef(false)
  const containerRef = useRef(null)
  const [containerReady, setContainerReady] = useState(false)

  // Orchestrator and Agent definitions
  // Orchestrator is in the center, agents are arranged around it
  const orchestrator = {
    id: 'orchestrator',
    label: 'Orchestrator',
    role: 'Agent Coordinator',
    icon: Network,
    color: '#6366f1',
    description: 'Coordinates and calls agents in sequence to execute the simulation workflow',
    position: { x: 550, y: 250 },
  }

  // Better organized layout: Top row (input), Center (orchestrator), Bottom row (output)
  const agents = [
    {
      id: 'red-team',
      label: 'Red Team',
      role: 'Attack Generation',
      icon: User,
      color: '#ef4444',
      description: 'Generates realistic cyberattack scenarios using MITRE ATT&CK framework',
      position: { x: 100, y: 50 },
    },
    {
      id: 'telemetry',
      label: 'Telemetry',
      role: 'Log Generation',
      icon: FileText,
      color: '#3b82f6',
      description: 'Creates synthetic system logs based on attack scenario',
      position: { x: 400, y: 50 },
    },
    {
      id: 'detection',
      label: 'Detection',
      role: 'Incident Analysis',
      icon: Search,
      color: '#f59e0b',
      description: 'Analyzes telemetry using LLM to detect security incidents',
      position: { x: 700, y: 50 },
    },
    {
      id: 'rag',
      label: 'RAG Agent',
      role: 'Context Retrieval',
      icon: Brain,
      color: '#8b5cf6',
      description: 'Retrieves threat intelligence and runbooks from knowledge base',
      position: { x: 1000, y: 50 },
    },
    {
      id: 'remediation',
      label: 'Remediation',
      role: 'Action Planning',
      icon: Shield,
      color: '#10b981',
      description: 'Generates remediation action recommendations based on incident and context',
      position: { x: 100, y: 450 },
    },
    {
      id: 'rl-agent',
      label: 'RL Agent',
      role: 'Action Selection',
      icon: Zap,
      color: '#ec4899',
      description: 'Selects optimal action using reinforcement learning (Q-learning)',
      position: { x: 400, y: 450 },
    },
    {
      id: 'outcome',
      label: 'Outcome',
      role: 'Result & Reward',
      icon: Activity,
      color: '#06b6d4',
      description: 'Simulates action outcome and calculates reward for RL learning',
      position: { x: 700, y: 450 },
    },
  ]

  const initializeGraph = useCallback(() => {
    // Add orchestrator node
    const orchestratorNode = {
      id: orchestrator.id,
      type: 'custom',
      position: orchestrator.position,
      data: {
        label: orchestrator.label,
        role: orchestrator.role,
        icon: orchestrator.icon,
        color: orchestrator.color,
        description: orchestrator.description,
        status: 'pending',
      },
      style: {
        width: 300,
      },
    }

    // Add agent nodes
    const agentNodes = agents.map((agent, index) => ({
      id: agent.id,
      type: 'custom',
      position: agent.position,
      data: {
        label: agent.label,
        role: agent.role,
        icon: agent.icon,
        color: agent.color,
        description: agent.description,
        status: 'pending',
      },
      style: {
        width: 280,
      },
    }))

    const initialNodes = [orchestratorNode, ...agentNodes]

    // Edges with better routing using smoothstep
    const initialEdges = [
      // Orchestrator calls Red Team (top-left)
      {
        id: 'e1',
        source: 'orchestrator',
        target: 'red-team',
        type: 'smoothstep',
        label: '1. Call Red Team',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // Red Team output flows to Telemetry (horizontal)
      {
        id: 'e2',
        source: 'red-team',
        target: 'telemetry',
        type: 'smoothstep',
        label: 'Attack Scenario',
        labelStyle: { fill: '#ef4444', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#ef4444', strokeWidth: 2.5, opacity: 0.8 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#ef4444', width: 18, height: 18 },
      },
      // Orchestrator calls Telemetry
      {
        id: 'e3',
        source: 'orchestrator',
        target: 'telemetry',
        type: 'smoothstep',
        label: '2. Call Telemetry',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // Telemetry output flows to Detection (horizontal)
      {
        id: 'e4',
        source: 'telemetry',
        target: 'detection',
        type: 'smoothstep',
        label: 'System Logs',
        labelStyle: { fill: '#3b82f6', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#3b82f6', strokeWidth: 2.5, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6', width: 18, height: 18 },
      },
      // Orchestrator calls Detection
      {
        id: 'e5',
        source: 'orchestrator',
        target: 'detection',
        type: 'smoothstep',
        label: '3. Call Detection',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // Detection output flows to RAG (horizontal)
      {
        id: 'e6',
        source: 'detection',
        target: 'rag',
        type: 'smoothstep',
        label: 'Incident Report',
        labelStyle: { fill: '#f59e0b', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#f59e0b', strokeWidth: 2.5, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#f59e0b', width: 18, height: 18 },
      },
      // Orchestrator calls RAG
      {
        id: 'e7',
        source: 'orchestrator',
        target: 'rag',
        type: 'smoothstep',
        label: '4. Call RAG',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // RAG output flows to Remediation (diagonal down-left)
      {
        id: 'e8',
        source: 'rag',
        target: 'remediation',
        type: 'smoothstep',
        label: 'RAG Context',
        labelStyle: { fill: '#8b5cf6', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#8b5cf6', strokeWidth: 2.5, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#8b5cf6', width: 18, height: 18 },
      },
      // Orchestrator calls Remediation
      {
        id: 'e9',
        source: 'orchestrator',
        target: 'remediation',
        type: 'smoothstep',
        label: '5. Call Remediation',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // Remediation output flows to RL Agent (horizontal)
      {
        id: 'e10',
        source: 'remediation',
        target: 'rl-agent',
        type: 'smoothstep',
        label: 'Action Options',
        labelStyle: { fill: '#10b981', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#10b981', strokeWidth: 2.5, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981', width: 18, height: 18 },
      },
      // Orchestrator calls RL Agent
      {
        id: 'e11',
        source: 'orchestrator',
        target: 'rl-agent',
        type: 'smoothstep',
        label: '6. Call RL Agent',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // RL Agent output flows to Outcome (horizontal)
      {
        id: 'e12',
        source: 'rl-agent',
        target: 'outcome',
        type: 'smoothstep',
        label: 'Selected Action',
        labelStyle: { fill: '#ec4899', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#ec4899', strokeWidth: 2.5, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#ec4899', width: 18, height: 18 },
      },
      // Orchestrator calls Outcome
      {
        id: 'e13',
        source: 'orchestrator',
        target: 'outcome',
        type: 'smoothstep',
        label: '7. Call Outcome',
        labelStyle: { fill: '#6366f1', fontWeight: 600, fontSize: 12 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#6366f1', strokeWidth: 3, opacity: 0.7 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 22, height: 22 },
      },
      // Outcome feedback to RL Agent (learning loop - curved back)
      {
        id: 'e14',
        source: 'outcome',
        target: 'rl-agent',
        type: 'smoothstep',
        label: 'Reward Feedback',
        labelStyle: { fill: '#10b981', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#10b981', strokeWidth: 2.5, strokeDasharray: '5,5', opacity: 0.6 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#10b981', width: 18, height: 18 },
      },
      // Outcome feedback to Orchestrator (up)
      {
        id: 'e15',
        source: 'outcome',
        target: 'orchestrator',
        type: 'smoothstep',
        label: 'Episode Complete',
        labelStyle: { fill: '#06b6d4', fontWeight: 600, fontSize: 11 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        labelBgPadding: [4, 4],
        animated: false,
        style: { stroke: '#06b6d4', strokeWidth: 2.5, strokeDasharray: '5,5', opacity: 0.6 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#06b6d4', width: 18, height: 18 },
      },
    ]

    setNodes(initialNodes)
    setEdges(initialEdges)
  }, [])

  const updateGraphFromEpisode = useCallback((episode) => {
    if (!episode || updateInProgressRef.current) return
    const stepMap = {
      'orchestrator': episode.outcome ? 'completed' : (episode.attack_scenario ? 'active' : 'pending'),
      'red-team': episode.attack_scenario ? 'completed' : 'pending',
      'telemetry': episode.telemetry ? 'completed' : 'pending',
      'detection': episode.incident_report ? 'completed' : 'pending',
      'rag': episode.rag_context ? 'completed' : 'pending',
      'remediation': episode.remediation ? 'completed' : 'pending',
      'rl-agent': episode.rl_decision ? 'completed' : 'pending',
      'outcome': episode.outcome ? 'completed' : 'pending',
    }

    // Determine current active step
    let activeStep = -1
    let activeAgentId = null
    if (episode.attack_scenario && !episode.telemetry) {
      activeStep = 0
      activeAgentId = 'red-team'
    } else if (episode.telemetry && !episode.incident_report) {
      activeStep = 1
      activeAgentId = 'telemetry'
    } else if (episode.incident_report && !episode.rag_context) {
      activeStep = 2
      activeAgentId = 'detection'
    } else if (episode.rag_context && !episode.remediation) {
      activeStep = 3
      activeAgentId = 'rag'
    } else if (episode.remediation && !episode.rl_decision) {
      activeStep = 4
      activeAgentId = 'remediation'
    } else if (episode.rl_decision && !episode.outcome) {
      activeStep = 5
      activeAgentId = 'rl-agent'
    } else if (episode.outcome) {
      activeStep = 6
      activeAgentId = 'outcome'
    }

    setCurrentStep(activeStep)
    setIsRunning(activeStep >= 0 && activeStep < 7)

    // Update nodes
    setNodes((nds) =>
      nds.map((node) => {
        const status = stepMap[node.id] || 'pending'
        const isActive = node.id === activeAgentId
        const isOrchestratorActive = node.id === 'orchestrator' && activeStep >= 0 && activeStep < 7
        
        return {
          ...node,
          data: {
            ...node.data,
            status: isActive ? 'active' : (isOrchestratorActive ? 'active' : status),
            episodeData: episode,
          },
        }
      })
    )

    // Update edges - animate active connections with current flow effect
    setEdges((eds) => {
      const updated = eds.map((edge) => {
        // Check if this is an orchestrator call edge
        const isOrchestratorCall = edge.source === 'orchestrator'
        const isActiveCall = isOrchestratorCall && edge.target === activeAgentId
        
        // Check if this is a data flow edge (flowing TO the active agent)
        const isDataFlow = !isOrchestratorCall && edge.target !== 'orchestrator'
        const sourceAgentIndex = agents.findIndex(a => a.id === edge.source)
        const targetAgentIndex = agents.findIndex(a => a.id === edge.target)
        // Data flow is active when it's flowing TO the currently active agent
        const isActiveDataFlow = isDataFlow && targetAgentIndex === activeStep && sourceAgentIndex === activeStep - 1
        
        // Check if this is a feedback edge
        const isFeedback = edge.target === 'rl-agent' && edge.source === 'outcome' && activeStep === 6
        const isCompleteFeedback = edge.target === 'orchestrator' && episode.outcome
        
        const isActive = isActiveCall || isActiveDataFlow || isFeedback || isCompleteFeedback
        
        // Determine edge color and style based on type and active state
        let newStroke, newStrokeWidth, newOpacity
        
        if (isActive) {
          // Active edge - bright, thick, animated (current flowing)
          if (isOrchestratorCall) {
            newStroke = '#6366f1' // Bright blue for orchestrator calls
            newStrokeWidth = 5
            newOpacity = 1.0
          } else if (isDataFlow) {
            // Keep original color for data flows
            newStroke = edge.style?.stroke || '#3b82f6'
            newStrokeWidth = 4
            newOpacity = 1.0
          } else {
            // Feedback edges
            newStroke = edge.style?.stroke || '#10b981'
            newStrokeWidth = 4
            newOpacity = 1.0
          }
        } else {
          // Inactive edge - visible but dimmed
          if (isOrchestratorCall) {
            newStroke = '#c7d2fe' // Light blue
            newStrokeWidth = 2.5
            newOpacity = 0.5
          } else {
            newStroke = edge.style?.stroke || '#94a3b8' // Keep original color but dimmed
            newStrokeWidth = 2
            newOpacity = 0.4
          }
        }
        
        // Only update if something changed
        const currentAnimated = edge.animated || false
        const currentStroke = edge.style?.stroke || '#94a3b8'
        const currentStrokeWidth = edge.style?.strokeWidth || 2
        const currentOpacity = edge.style?.opacity !== undefined ? edge.style.opacity : 1.0
        
        if (currentAnimated === isActive && 
            currentStroke === newStroke && 
            currentStrokeWidth === newStrokeWidth &&
            Math.abs(currentOpacity - newOpacity) < 0.01) {
          return edge
        }
        
        // Create updated edge
        const updatedEdge = {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type || 'default',
          label: edge.label,
          labelStyle: edge.labelStyle,
          labelBgStyle: edge.labelBgStyle,
          labelBgPadding: edge.labelBgPadding,
          animated: isActive, // This enables React Flow's built-in animation
          style: {
            ...edge.style,
            stroke: newStroke,
            strokeWidth: newStrokeWidth,
            opacity: newOpacity,
            filter: isActive ? `drop-shadow(0 0 6px ${newStroke})` : 'none',
          },
          markerEnd: edge.markerEnd,
        }
        
        // Only include handle properties if they exist
        if (edge.sourceHandle !== undefined) {
          updatedEdge.sourceHandle = edge.sourceHandle
        }
        if (edge.targetHandle !== undefined) {
          updatedEdge.targetHandle = edge.targetHandle
        }
        
        return updatedEdge
      })
      return updated
    })
  }, [])

  const loadEpisodeData = useCallback(async () => {
    try {
      let episode = null
      
      if (episodeNumber) {
        episode = await getEpisodeDetails(episodeNumber)
      } else if (simulationId) {
        const episodes = await getSimulationEpisodes(simulationId)
        if (episodes.length > 0) {
          const latest = episodes[episodes.length - 1]
          episode = await getEpisodeDetails(latest.episode_number)
        }
      }

      // Only update if episode data actually changed
      if (episode) {
        const episodeKey = `${episode.episode_number}_${episode.timestamp || ''}_${episode.outcome ? 'complete' : 'running'}`
        if (lastEpisodeRef.current !== episodeKey) {
          lastEpisodeRef.current = episodeKey
          setEpisodeData(episode)
          updateGraphFromEpisode(episode)
        }
      }
    } catch (error) {
      console.error('Error loading episode data:', error)
    }
  }, [simulationId, episodeNumber, updateGraphFromEpisode])

  // Initialize graph - only once
  useEffect(() => {
    if (!initializedRef.current) {
      initializeGraph()
      initializedRef.current = true
    }
  }, [initializeGraph])

  // Wait for container to be ready with dimensions
  useEffect(() => {
    if (!containerRef.current) return
    
    let timer1, timer2
    
    const checkReady = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        if (rect.width > 0 && rect.height > 0) {
          setContainerReady(true)
          return true
        }
      }
      return false
    }
    
    // Try immediately
    if (checkReady()) return
    
    // Try after a short delay
    timer1 = setTimeout(() => {
      if (checkReady()) return
      
      // Try after animation frame
      requestAnimationFrame(() => {
        if (!checkReady()) {
          // Final fallback - set ready anyway after delay
          timer2 = setTimeout(() => {
            setContainerReady(true)
          }, 200)
        }
      })
    }, 50)
    
    return () => {
      if (timer1) clearTimeout(timer1)
      if (timer2) clearTimeout(timer2)
    }
  }, [])

  // Monitor simulation/episode progress
  useEffect(() => {
    if (!simulationId && !episodeNumber) return
    
    loadEpisodeData() // Load immediately
    
    const interval = setInterval(() => {
      if (!updateInProgressRef.current) {
        loadEpisodeData()
      }
    }, 5000) // Increased to 5 seconds to reduce flickering
    
    return () => clearInterval(interval)
  }, [simulationId, episodeNumber, loadEpisodeData])


  return (
    <div className="w-full h-[800px] bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Agent Orchestration Flow</h3>
            <p className="text-sm text-gray-600">Real-time visualization of multi-agent interactions</p>
          </div>
          {isRunning && (
            <div className="flex items-center space-x-2 text-sm text-blue-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Simulation Running</span>
            </div>
          )}
        </div>
      </div>
      <div 
        ref={containerRef}
        className="w-full" 
        style={{ 
          width: '100%', 
          height: '732px', 
          minHeight: '732px',
          position: 'relative',
          display: 'block'
        }}
      >
        {nodes.length > 0 && containerReady && (
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.2, maxZoom: 1.2 }}
          minZoom={0.3}
          maxZoom={2}
          attributionPosition="bottom-left"
          className="bg-gradient-to-br from-gray-50 to-gray-100"
          defaultEdgeOptions={{
            style: { strokeWidth: 3, stroke: '#6366f1' },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1', width: 20, height: 20 },
            type: 'default',
          }}
          connectionLineStyle={{ stroke: '#6366f1', strokeWidth: 2 }}
        >
        <Background color="#e5e7eb" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const status = node.data?.status || 'pending'
            if (status === 'active') return '#3b82f6'
            if (status === 'completed') return '#10b981'
            return '#94a3b8'
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        </ReactFlow>
        )}
        {(!nodes.length || !containerReady) && (
          <div className="flex items-center justify-center h-full" style={{ minHeight: '732px' }}>
            <div className="text-gray-500">Initializing graph...</div>
          </div>
        )}
      </div>
    </div>
  )
}

export default AgentOrchestrationGraph

