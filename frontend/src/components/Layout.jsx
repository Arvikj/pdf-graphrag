import React from 'react';
import { LayoutDashboard, Upload, MessageSquare, Network } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

const Layout = ({ children, currentView, onNavigate }) => {
    return (
        <div className="flex h-screen bg-gray-50 dark:bg-dark-bg text-gray-900 dark:text-gray-100 transition-colors duration-300">
            {/* Sidebar */}
            <aside className="w-20 lg:w-64 bg-white dark:bg-dark-card border-r border-gray-200 dark:border-gray-700 flex flex-col items-center lg:items-stretch py-6 transition-all duration-300">
                <div className="mb-8 px-4 flex justify-center lg:justify-start items-center gap-3">
                    <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/30">
                        <Network className="text-white" size={24} />
                    </div>
                    <span className="hidden lg:block font-bold text-xl tracking-tight">GraphRAG</span>
                </div>

                <nav className="flex-1 flex flex-col gap-2 px-2">
                    <NavItem
                        icon={<Upload size={20} />}
                        label="Upload PDF"
                        active={currentView === 'upload'}
                        onClick={() => onNavigate('upload')}
                    />
                    <NavItem
                        icon={<MessageSquare size={20} />}
                        label="Chat"
                        active={currentView === 'chat'}
                        onClick={() => onNavigate('chat')}
                    />
                    <NavItem
                        icon={<Network size={20} />}
                        label="Knowledge Graph"
                        active={currentView === 'graph'}
                        onClick={() => onNavigate('graph')}
                    />
                </nav>

                <div className="mt-auto px-4 flex justify-center lg:justify-start">
                    <ThemeToggle />
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden relative">
                <div className="absolute inset-0 overflow-y-auto p-4 lg:p-8">
                    <div className="max-w-6xl mx-auto h-full">
                        {children}
                    </div>
                </div>
            </main>
        </div>
    );
};

const NavItem = ({ icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group w-full
      ${active
                ? 'bg-primary/10 text-primary dark:text-primary'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-gray-100'
            }`}
    >
        <span className={`${active ? 'text-primary' : 'group-hover:text-primary transition-colors'}`}>
            {icon}
        </span>
        <span className="hidden lg:block font-medium">{label}</span>
    </button>
);

export default Layout;
