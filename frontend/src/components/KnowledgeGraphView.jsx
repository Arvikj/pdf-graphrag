import React from 'react';
import { Network } from 'lucide-react';

const KnowledgeGraphView = () => {
    return (
        <div className="w-full h-[600px] bg-gray-900 rounded-3xl overflow-hidden relative flex items-center justify-center group">
            {/* Abstract Background */}
            <div className="absolute inset-0 opacity-20">
                <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,_rgba(59,130,246,0.5),transparent_70%)]" />
                <div className="grid grid-cols-12 gap-4 w-full h-full p-8 opacity-30">
                    {[...Array(48)].map((_, i) => (
                        <div key={i} className="w-1 h-1 bg-blue-400 rounded-full" />
                    ))}
                </div>
            </div>

            {/* Content Card */}
            <div className="relative z-10 text-center p-8 bg-white/10 backdrop-blur-md rounded-2xl border border-white/10 max-w-md mx-4 transform transition-transform duration-500 group-hover:scale-105">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-blue-500/20">
                    <Network className="text-white" size={32} />
                </div>

                <h3 className="text-2xl font-bold text-white mb-3">Knowledge Graph</h3>
                <p className="text-blue-200 mb-6">
                    Visualization module is coming soon. This view will display the extracted entities and relationships from your PDF in an interactive 2D graph.
                </p>

                <div className="flex justify-center gap-2">
                    <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 text-xs font-medium border border-blue-500/30">Neo4j</span>
                    <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-medium border border-purple-500/30">D3.js</span>
                    <span className="px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-medium border border-cyan-500/30">Interactive</span>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeGraphView;
