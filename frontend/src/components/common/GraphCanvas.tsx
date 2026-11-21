import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import dagre from '@dagrejs/dagre';
import { useUIStore, type SourceSpan } from '../../store/uiStore';

export interface GraphNodeData extends Record<string, unknown> {
  label: string;
  subtitle?: string;
  span?: SourceSpan | null;
  phaseColor?: string;
  isError?: boolean;
  extra?: Record<string, any>;
}

interface GraphCanvasProps {
  initialNodes: Array<{
    id: string;
    label: string;
    subtitle?: string;
    span?: SourceSpan | null;
    phaseColor?: string;
    isError?: boolean;
    extra?: Record<string, any>;
  }>;
  initialEdges: Array<{
    id: string;
    source: string;
    target: string;
    label?: string;
    dashed?: boolean;
    color?: string;
  }>;
  direction?: 'TB' | 'LR';
  className?: string;
}

// Dagre layout computation
const getLayoutedElements = (
  nodes: Node<GraphNodeData>[],
  edges: Edge[],
  direction = 'TB'
) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction, ranksep: 40, nodesep: 30 });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: 160, height: 60 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const newNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: isHorizontal ? Position.Left : Position.Top,
      sourcePosition: isHorizontal ? Position.Right : Position.Bottom,
      position: {
        x: nodeWithPosition ? nodeWithPosition.x - 80 : 0,
        y: nodeWithPosition ? nodeWithPosition.y - 30 : 0,
      },
    };
  });

  return { nodes: newNodes, edges };
};

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  initialNodes,
  initialEdges,
  direction = 'TB',
  className = '',
}) => {
  const { setHoverSpan, setPinnedSpan } = useUIStore();

  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    const rfNodes: Node<GraphNodeData>[] = initialNodes.map((n) => ({
      id: n.id,
      data: {
        label: n.label,
        subtitle: n.subtitle,
        span: n.span,
        phaseColor: n.phaseColor,
        isError: n.isError,
        extra: n.extra,
      },
      position: { x: 0, y: 0 },
      className: `px-3 py-2 rounded-lg border text-xs shadow-md transition-all cursor-pointer ${
        n.isError
          ? 'bg-err/10 border-err text-err'
          : n.phaseColor
          ? 'bg-bg-2 text-text-0'
          : 'bg-bg-2 border-border text-text-0'
      }`,
      style: n.phaseColor
        ? { borderColor: n.phaseColor, boxShadow: `0 0 10px ${n.phaseColor}20` }
        : undefined,
    }));

    const rfEdges: Edge[] = initialEdges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: e.dashed,
      style: {
        stroke: e.color || 'var(--border)',
        strokeDasharray: e.dashed ? '5,5' : undefined,
      },
      labelStyle: { fill: 'var(--text-1)', fontSize: 10, fontFamily: 'monospace' },
    }));

    const layout = getLayoutedElements(rfNodes, rfEdges, direction);
    return { layoutedNodes: layout.nodes, layoutedEdges: layout.edges };
  }, [initialNodes, initialEdges, direction]);

  const [nodes, , onNodesChange] = useNodesState(layoutedNodes);
  const [edges, , onEdgesChange] = useEdgesState(layoutedEdges);

  return (
    <div className={`w-full h-full bg-bg-0 relative rounded-lg border border-border overflow-hidden ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeMouseEnter={(_, node) => {
          const span = node.data?.span as SourceSpan | null | undefined;
          if (span) setHoverSpan(span);
        }}
        onNodeMouseLeave={() => setHoverSpan(null)}
        onNodeClick={(_, node) => {
          const span = node.data?.span as SourceSpan | null | undefined;
          if (span) setPinnedSpan(span);
        }}
        fitView
        minZoom={0.2}
        maxZoom={2.5}
      >
        <Background color="var(--border)" gap={16} size={1} />
        <Controls className="!bg-bg-1 !border-border !fill-text-0 !text-text-0" />
        {nodes.length > 25 && (
          <MiniMap
            nodeColor="var(--accent)"
            maskColor="rgba(11, 14, 20, 0.7)"
            className="!bg-bg-1 !border-border"
          />
        )}
      </ReactFlow>
    </div>
  );
};
