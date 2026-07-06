/**
 * LexOrch-KG — Knowledge Graph Visualization Page
 * React Flow interactive graph of legal entities and relationships.
 */

import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ReactFlow, {
  Background, Controls, MiniMap,
  Node, Edge, MarkerType,
  BackgroundVariant,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Network, AlertCircle } from 'lucide-react'
import { casesApi } from '@/lib/api'
import { useMemo } from 'react'

const nodeColors: Record<string, string> = {
  Case:         '#3a70f5',
  Judge:        '#8b5cf6',
  Court:        '#10b981',
  Person:       '#f59e0b',
  Law:          '#ef4444',
  Act:          '#ef4444',
  Evidence:     '#06b6d4',
  Witness:      '#84cc16',
  Precedent:    '#f97316',
  Organization: '#ec4899',
  Location:     '#a78bfa',
}

function buildFlowNodes(nodes: any[]): Node[] {
  return nodes.map((node, i) => {
    const angle = (i / Math.max(nodes.length - 1, 1)) * 2 * Math.PI
    const radius = node.label === 'Case' ? 0 : 300
    const color = nodeColors[node.label] || '#64748b'
    return {
      id: node.id,
      position: {
        x: 500 + radius * Math.cos(angle),
        y: 350 + radius * Math.sin(angle),
      },
      data: {
        label: (
          <div className="text-center">
            <div className="text-xs font-bold text-white truncate max-w-24">
              {String(node.data?.name || node.data?.title || node.label).substring(0, 20)}
            </div>
            <div className="text-[9px] opacity-70 text-white mt-0.5">{node.label}</div>
          </div>
        ),
      },
      style: {
        background: color,
        border: `2px solid ${color}`,
        borderRadius: node.label === 'Case' ? '12px' : '50%',
        width: node.label === 'Case' ? 120 : 90,
        height: node.label === 'Case' ? 50 : 90,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        boxShadow: `0 0 20px ${color}40`,
      },
      type: 'default',
    }
  })
}

function buildFlowEdges(edges: any[]): Edge[] {
  return edges.map((edge, i) => ({
    id: `edge-${i}`,
    source: edge.source,
    target: edge.target,
    label: edge.type?.replace(/_/g, ' '),
    labelStyle: { fill: '#94a3b8', fontSize: 10 },
    style: { stroke: 'rgba(58, 112, 245, 0.5)', strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: 'rgba(58, 112, 245, 0.5)' },
    animated: true,
  }))
}

export default function KnowledgeGraph() {
  const { id } = useParams<{ id: string }>()

  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ['kg', id],
    queryFn: async () => {
      const { data } = await casesApi.knowledgeGraph(id!)
      return data
    },
  })

  const nodes = useMemo(
    () => buildFlowNodes(graphData?.nodes || []),
    [graphData]
  )
  const edges = useMemo(
    () => buildFlowEdges(graphData?.edges || []),
    [graphData]
  )

  const legend = Object.entries(nodeColors).slice(0, 8)

  return (
    <div className="space-y-4 animate-slide-up h-full">
      <div>
        <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
          <Network className="w-6 h-6 text-primary-400" />
          Knowledge Graph
        </h1>
        <p className="text-dark-400 mt-0.5 text-sm">
          Legal entity relationships visualized from case analysis
        </p>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-2">
        {legend.map(([label, color]) => (
          <div key={label} className="flex items-center gap-1.5 text-xs text-dark-400">
            <div className="w-3 h-3 rounded-full" style={{ background: color }} />
            {label}
          </div>
        ))}
      </div>

      {/* Graph */}
      <div className="glass rounded-2xl overflow-hidden" style={{ height: '600px' }}>
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="spinner mx-auto mb-3" style={{ width: 40, height: 40 }} />
              <p className="text-dark-400">Loading knowledge graph...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
              <p className="text-dark-400">Knowledge graph unavailable</p>
              <p className="text-dark-600 text-sm mt-1">Neo4j may not be connected</p>
            </div>
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Network className="w-10 h-10 text-dark-600 mx-auto mb-3" />
              <p className="text-dark-400">No graph data yet</p>
              <p className="text-dark-600 text-sm">Run the AI pipeline first</p>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            className="bg-dark-900"
          >
            <Background
              variant={BackgroundVariant.Dots}
              color="#334155"
              gap={24}
              size={1}
            />
            <Controls className="bg-dark-800 border-dark-700 rounded-xl" />
            <MiniMap
              className="bg-dark-800 border border-dark-700 rounded-xl"
              nodeColor={(node) => {
                const label = String(node.data?.label || '')
                return nodeColors[label] || '#64748b'
              }}
              maskColor="rgba(15, 23, 42, 0.7)"
            />
          </ReactFlow>
        )}
      </div>

      {/* Stats */}
      {graphData && (
        <div className="flex gap-4 text-sm text-dark-400">
          <span>{graphData.nodes?.length ?? 0} nodes</span>
          <span>·</span>
          <span>{graphData.edges?.length ?? 0} relationships</span>
        </div>
      )}
    </div>
  )
}
