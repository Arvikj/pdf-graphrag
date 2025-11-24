import React, { useState } from 'react';
import Layout from './components/Layout';
import UploadZone from './components/UploadZone';
import ChatInterface from './components/ChatInterface';
import KnowledgeGraphView from './components/KnowledgeGraphView';
import { motion } from 'framer-motion';

function App() {
  const [currentView, setCurrentView] = useState('upload'); // upload | chat | graph

  const handleUploadComplete = () => {
    setCurrentView('chat');
  };

  const renderContent = () => {
    switch (currentView) {
      case 'upload':
        return (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            <UploadZone onUploadComplete={handleUploadComplete} />
          </motion.div>
        );
      case 'chat':
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="h-full"
          >
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
                <span className="w-3 h-8 bg-primary rounded-full"></span>
                Chat Assistant
              </h2>
              <p className="text-gray-500 dark:text-gray-400 ml-6 mt-1">
                Ask questions about your uploaded PDF.
              </p>
            </div>
            <ChatInterface />
          </motion.div>
        );
      case 'graph':
        return (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="h-full"
          >
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-800 dark:text-white flex items-center gap-3">
                <span className="w-3 h-8 bg-secondary rounded-full"></span>
                Knowledge Graph
              </h2>
              <p className="text-gray-500 dark:text-gray-400 ml-6 mt-1">
                Visualize entities and relationships.
              </p>
            </div>
            <KnowledgeGraphView />
          </motion.div>
        );
      default:
        return null;
    }
  };

  return (
    <Layout currentView={currentView} onNavigate={setCurrentView}>
      <div className="h-full flex flex-col">
        {/* Header Section - Only show on Upload view */}
        {currentView === 'upload' && (
          <div className="text-center lg:text-left mb-10">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2 tracking-tight">
              PDF Knowledge Assistant
            </h1>
            <p className="text-lg text-gray-500 dark:text-gray-400">
              Upload your documents and let AI extract the hidden connections.
            </p>
          </div>
        )}

        {/* Main Content Area */}
        <div className="flex-1">
          {renderContent()}
        </div>
      </div>
    </Layout>
  );
}

export default App;
