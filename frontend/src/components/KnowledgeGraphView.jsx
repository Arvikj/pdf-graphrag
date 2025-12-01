import React, { useEffect, useRef, useState } from 'react';
import { Network, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import axios from 'axios';

// Color palette for different node labels
const LABEL_COLORS = {
    Person: '#ef4444',      // red
    Organization: '#3b82f6', // blue
    Location: '#22c55e',     // green
    Concept: '#a855f7',      // purple
    Document: '#f59e0b',     // amber
    Event: '#06b6d4',        // cyan
    Date: '#ec4899',         // pink
    Entity: '#6b7280',       // gray (default)
};

const getNodeColor = (label) => LABEL_COLORS[label] || LABEL_COLORS.Entity;

const KnowledgeGraphView = () => {
    const containerRef = useRef(null);
    const networkRef = useRef(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [stats, setStats] = useState({ nodes: 0, relationships: 0 });
    const [selectedNode, setSelectedNode] = useState(null);

    const fetchAndRenderGraph = async () => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.get('/api/graph');
            const { nodes, relationships } = response.data.data;
            
            setStats({
                nodes: nodes.length,
                relationships: relationships.length
            });

            // Transform data for vis-network format
            const visNodes = nodes.map(node => ({
                id: node.id,
                label: node.properties?.name || node.id.replace(/_/g, ' ').slice(0, 20),
                title: `${node.label}: ${node.properties?.name || node.id}\n${node.properties?.description || ''}`,
                color: {
                    background: getNodeColor(node.label),
                    border: getNodeColor(node.label),
                    highlight: { background: '#fff', border: getNodeColor(node.label) }
                },
                font: { color: '#fff', size: 12 },
                shape: 'dot',
                size: 15,
                data: node // Store original data
            }));

            const visEdges = relationships.map((rel, idx) => ({
                id: `edge-${idx}`,
                from: rel.source_id,
                to: rel.target_id,
                label: rel.type.replace(/_/g, ' '),
                arrows: 'to',
                color: { color: '#64748b', highlight: '#3b82f6' },
                font: { size: 10, color: '#94a3b8', strokeWidth: 0 },
                smooth: { type: 'continuous' }
            }));

            // Initialize vis-network
            if (containerRef.current && window.vis) {
                const data = {
                    nodes: new window.vis.DataSet(visNodes),
                    edges: new window.vis.DataSet(visEdges)
                };

                const options = {
                    physics: {
                        enabled: true,
                        solver: 'forceAtlas2Based',
                        forceAtlas2Based: {
                            gravitationalConstant: -50,
                            centralGravity: 0.01,
                            springLength: 100,
                            springConstant: 0.08
                        },
                        stabilization: { iterations: 100 }
                    },
                    interaction: {
                        hover: true,
                        tooltipDelay: 200,
                        zoomView: true,
                        dragView: true
                    },
                    nodes: {
                        borderWidth: 2,
                        shadow: true
                    },
                    edges: {
                        width: 1,
                        shadow: true
                    }
                };

                // Destroy previous network if exists
                if (networkRef.current) {
                    networkRef.current.destroy();
                }

                networkRef.current = new window.vis.Network(containerRef.current, data, options);

                // Handle node selection
                networkRef.current.on('selectNode', (params) => {
                    const nodeId = params.nodes[0];
                    const node = visNodes.find(n => n.id === nodeId);
                    if (node) {
                        setSelectedNode(node.data);
                    }
                });

                networkRef.current.on('deselectNode', () => {
                    setSelectedNode(null);
                });
            }

            setLoading(false);
        } catch (err) {
            console.error('Error fetching graph:', err);
            setError(err.response?.data?.detail || 'Failed to load graph. Make sure Neo4j is running.');
            setLoading(false);
        }
    };

    useEffect(() => {
        // Load vis-network from CDN
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js';
        script.async = true;
        script.onload = () => {
            fetchAndRenderGraph();
        };
        document.body.appendChild(script);

        return () => {
            if (networkRef.current) {
                networkRef.current.destroy();
            }
        };
    }, []);

    const handleZoomIn = () => {
        if (networkRef.current) {
            const scale = networkRef.current.getScale();
            networkRef.current.moveTo({ scale: scale * 1.3 });
        }
    };

    const handleZoomOut = () => {
        if (networkRef.current) {
            const scale = networkRef.current.getScale();
            networkRef.current.moveTo({ scale: scale / 1.3 });
        }
    };

    const handleFit = () => {
        if (networkRef.current) {
            networkRef.current.fit({ animation: true });
        }
    };

    // Loading state
    if (loading) {
        return (
            <div className="w-full h-[600px] bg-gray-900 rounded-3xl overflow-hidden relative flex items-center justify-center">
                <div className="text-center">
                    <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
                    <p className="text-blue-200">Loading knowledge graph...</p>
                </div>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="w-full h-[600px] bg-gray-900 rounded-3xl overflow-hidden relative flex items-center justify-center">
                <div className="text-center p-8 max-w-md">
                    <Network className="w-16 h-16 text-red-400 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">Connection Error</h3>
                    <p className="text-red-300 mb-4">{error}</p>
                    <button
                        onClick={fetchAndRenderGraph}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto"
                    >
                        <RefreshCw size={16} /> Retry
                    </button>
                    <p className="text-gray-400 text-sm mt-4">
                        Start Neo4j with: <code className="bg-gray-800 px-2 py-1 rounded">docker-compose up -d</code>
                    </p>
                </div>
            </div>
        );
    }

    // Empty state
    if (stats.nodes === 0) {
        return (
            <div className="w-full h-[600px] bg-gray-900 rounded-3xl overflow-hidden relative flex items-center justify-center">
                <div className="text-center p-8">
                    <Network className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">No Graph Data</h3>
                    <p className="text-gray-400 mb-4">Upload a PDF to extract and visualize the knowledge graph.</p>
                    <button
                        onClick={fetchAndRenderGraph}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto"
                    >
                        <RefreshCw size={16} /> Refresh
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full h-[600px] bg-gray-900 rounded-3xl overflow-hidden relative">
            {/* Graph container */}
            <div ref={containerRef} className="w-full h-full" />

            {/* Controls */}
            <div className="absolute top-4 right-4 flex flex-col gap-2">
                <button
                    onClick={handleZoomIn}
                    className="p-2 bg-gray-800/80 hover:bg-gray-700 text-white rounded-lg backdrop-blur-sm"
                    title="Zoom In"
                >
                    <ZoomIn size={20} />
                </button>
                <button
                    onClick={handleZoomOut}
                    className="p-2 bg-gray-800/80 hover:bg-gray-700 text-white rounded-lg backdrop-blur-sm"
                    title="Zoom Out"
                >
                    <ZoomOut size={20} />
                </button>
                <button
                    onClick={handleFit}
                    className="p-2 bg-gray-800/80 hover:bg-gray-700 text-white rounded-lg backdrop-blur-sm"
                    title="Fit to View"
                >
                    <Maximize2 size={20} />
                </button>
                <button
                    onClick={fetchAndRenderGraph}
                    className="p-2 bg-gray-800/80 hover:bg-gray-700 text-white rounded-lg backdrop-blur-sm"
                    title="Refresh"
                >
                    <RefreshCw size={20} />
                </button>
            </div>

            {/* Stats */}
            <div className="absolute top-4 left-4 bg-gray-800/80 backdrop-blur-sm rounded-lg p-3">
                <div className="flex gap-4 text-sm">
                    <div>
                        <span className="text-gray-400">Nodes:</span>
                        <span className="text-white ml-1 font-medium">{stats.nodes}</span>
                    </div>
                    <div>
                        <span className="text-gray-400">Relationships:</span>
                        <span className="text-white ml-1 font-medium">{stats.relationships}</span>
                    </div>
                </div>
            </div>

            {/* Legend */}
            <div className="absolute bottom-4 left-4 bg-gray-800/80 backdrop-blur-sm rounded-lg p-3">
                <div className="text-xs text-gray-400 mb-2">Node Types</div>
                <div className="flex flex-wrap gap-2">
                    {Object.entries(LABEL_COLORS).slice(0, 6).map(([label, color]) => (
                        <div key={label} className="flex items-center gap-1">
                            <div
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: color }}
                            />
                            <span className="text-xs text-gray-300">{label}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Selected Node Info */}
            {selectedNode && (
                <div className="absolute bottom-4 right-4 bg-gray-800/90 backdrop-blur-sm rounded-lg p-4 max-w-xs">
                    <div className="text-sm">
                        <div className="text-blue-400 font-medium mb-1">{selectedNode.label}</div>
                        <div className="text-white font-bold mb-2">
                            {selectedNode.properties?.name || selectedNode.id}
                        </div>
                        {selectedNode.properties?.description && (
                            <div className="text-gray-400 text-xs">
                                {selectedNode.properties.description}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default KnowledgeGraphView;
