import React, { useEffect, useRef, useState } from 'react';
import { Network } from 'lucide-react';
import NeoVis from 'neovis.js';
import axios from 'axios';

const KnowledgeGraphView = () => {
    const [databases, setDatabases] = useState([]);
    const [selectedDb, setSelectedDb] = useState();
    const [loading, setLoading] = useState(true);

    // const renderGraph = (creds, labels, relationships) => {
    //     const config = {
    //         containerId: "graph",
    //         serverDatabase: selectedDb,
    //         neo4j: {
    //             serverUrl: creds.url,
    //             serverUser: creds.user,
    //             serverPassword: creds.pass
    //         },
    //         labels: Object.fromEntries(labels.map(label => 
    //             [label, {
    //                 label: "id"
    //             }]
    //         )),
    //         relationships: Object.fromEntries(relationships.map(relationship => 
    //             [relationship, {
    //                 id: 1 // I genuinely have no idea why this is necessary but without it only 1 relationship ever renders
    //             }]
    //         )),
    //         groupAsLabel: true,
    //         initialCypher: "MATCH (n)-[r]->(m) RETURN *"
    //     };

    //     let viz = new NeoVis(config);
    //     viz.render();
    // };

    const renderGraph = (creds, labels, relationships) => {
    const config = {
        containerId: "graph",
        serverDatabase: selectedDb,
        neo4j: {
            serverUrl: creds.url,
            serverUser: creds.user,
            serverPassword: creds.pass
        },
        labels: Object.fromEntries(labels.map(label => 
            [label, {
                label: "id", // This refers to properties.id
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                    static: {
                        color: "#4287f5"
                    }
                }
            }]
        )),
        relationships: Object.fromEntries(relationships.map(relationship => 
            [relationship, {
                thickness: "1",
                caption: true
            }]
        )),
        initialCypher: "MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN n, r, m"
    };
    
    let viz = new NeoVis(config);
    viz.render();
};

    useEffect(() => {
        axios.get('/api/neo4j/databases').then(obj => {
            console.log("here",obj);
            setDatabases(obj.data)
        });
    }, []);

    useEffect(() => {
        if (!selectedDb) return;

        // Dynamically map labels and relationships for graph visualizer
        axios.get('/api/neo4j/config').then(configResponse => {
            axios.get(`/api/neo4j/${selectedDb}/node-labels`).then(labelsResponse => {
                axios.get(`/api/neo4j/${selectedDb}/relationship-types`).then(relationshipsResponse => {
                    console.log("configResponse", configResponse);
                    
                    renderGraph(configResponse.data, labelsResponse.data, relationshipsResponse.data);
                    setLoading(false);
                });
            });
        });
    }, [selectedDb]);

    return (<>
        <div className="w-full h-[600px] bg-gray-900 rounded-3xl overflow-hidden relative flex items-center justify-center group">
            {/* Content Card */}
            <div className="relative items-center z-10 text-center p-8 bg-white/10 backdrop-blur-md rounded-2xl border border-white/10 max-w-md mx-4 transform transition-transform duration-500 group-hover:scale-105">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-blue-500/20">
                    <Network className="text-white" size={32} />
                </div>
                <h3 className="text-2xl font-bold text-white mb-3">Select a Database</h3>
                <select
                    className="bg-gray-800 border border-gray-600 p-2 rounded"
                    value={selectedDb}
                    onChange={(e) => setSelectedDb(e.target.value)}>
                    {!selectedDb && <option key={"None"} value=""></option>}
                    {databases.map(db => (
                        <option key={db} value={db}>{db}</option>
                    ))}
                </select>
            </div>
            
            <div>
                {/* Abstract Background */}
                <div className="absolute inset-0 opacity-20">
                    <div className="absolute top-0 left-0 w-full h-full bg-[radial-gradient(circle_at_50%_50%,_rgba(59,130,246,0.5),transparent_70%)]" />
                    <div className="grid grid-cols-12 gap-4 w-full h-full p-8 opacity-30">
                        {[...Array(48)].map((_, i) => (
                            <div key={i} className="w-1 h-1 bg-blue-400 rounded-full" />
                        ))}
                    </div>
                </div>

                {selectedDb &&
                    <div>
                        {loading && <div>Loading graph...</div>}
                        <div id="graph" className="inset-0 z-5 w-full h-full"></div>
                    </div>
                }
            </div>
        </div>
    </>);
};

export default KnowledgeGraphView;
