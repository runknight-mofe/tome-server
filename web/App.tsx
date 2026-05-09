/**
 * Aether Mesh Management - Web Client
 * React + TypeScript + D3.js + Tailwind CSS
 * 
 * Main application entry point
 */

import React, { useEffect, useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import TopologyViewer from './components/TopologyViewer';
import NodeManager from './components/NodeManager';
import PredicateEditor from './components/PredicateEditor';
import EventTimeline from './components/EventTimeline';
import MeshSelector from './components/MeshSelector';
import { useMeshStore } from './store/meshStore';
import './styles/tailwind.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 10, // 10 seconds
      gcTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

interface LayoutMode {
  type: 'desktop' | 'mobile-portrait' | 'mobile-landscape';
  width: number;
  height: number;
}

const getLayoutMode = (): LayoutMode => {
  const width = window.innerWidth;
  const height = window.innerHeight;
  
  if (width > 1024) {
    return { type: 'desktop', width, height };
  } else if (height > width) {
    return { type: 'mobile-portrait', width, height };
  } else {
    return { type: 'mobile-landscape', width, height };
  }
};

export default function App() {
  const [layoutMode, setLayoutMode] = useState<LayoutMode>(getLayoutMode());
  const [sidebarOpen, setSidebarOpen] = useState(layoutMode.type === 'desktop');
  const { currentMesh } = useMeshStore();

  useEffect(() => {
    const handleResize = () => {
      setLayoutMode(getLayoutMode());
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="h-screen w-screen bg-gray-950 text-gray-100 flex flex-col overflow-hidden">
          {/* Header */}
          <header className="bg-gray-900 border-b border-gray-700 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 hover:bg-gray-800 rounded"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
                  <span className="font-bold text-white text-sm">A</span>
                </div>
                <h1 className="text-xl font-bold">Aether Mesh</h1>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <MeshSelector />
              
              <div className="flex items-center gap-2 text-sm">
                {currentMesh && (
                  <>
                    <div className="flex items-center gap-1">
                      <div className={`w-2 h-2 rounded-full ${
                        currentMesh.status === 'connected' ? 'bg-green-500' : 'bg-red-500'
                      }`}></div>
                      <span className="text-gray-400">{currentMesh.name}</span>
                    </div>
                    <span className="text-gray-600">•</span>
                    <span className="text-gray-400">
                      {currentMesh.anchorCount} anchors, {currentMesh.clientCount} clients
                    </span>
                  </>
                )}
              </div>
            </div>
          </header>

          {/* Main Content Area */}
          <div className="flex-1 flex overflow-hidden">
            {/* Sidebar - Responsive */}
            <aside className={`
              bg-gray-900 border-r border-gray-700 transition-all duration-300
              ${layoutMode.type === 'desktop' ? 'w-64' : (sidebarOpen ? 'w-64' : 'w-0')}
              overflow-y-auto
            `}>
              {sidebarOpen && (
                <nav className="p-4 space-y-2">
                  <div className="mb-6">
                    <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Tools
                    </h2>
                    <div className="space-y-2">
                      <NavButton icon="📊" label="Topology" href="/" />
                      <NavButton icon="🔴" label="Nodes" href="/nodes" />
                      <NavButton icon="📦" label="Predicates" href="/predicates" />
                      <NavButton icon="📋" label="Events" href="/events" />
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-700">
                    <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Quick Stats
                    </h2>
                    {currentMesh && (
                      <div className="space-y-2 text-sm">
                        <StatItem label="Mode" value={currentMesh.operatingMode} />
                        <StatItem label="GDOP" value={currentMesh.gdop?.toFixed(2) || 'N/A'} />
                        <StatItem label="Update Rate" value={currentMesh.updateFrequency?.toFixed(1) + ' Hz' || 'N/A'} />
                      </div>
                    )}
                  </div>
                </nav>
              )}
            </aside>

            {/* Main Content */}
            <main className="flex-1 flex flex-col overflow-hidden">
              <Routes>
                <Route path="/" element={<TopologyViewer layoutMode={layoutMode} />} />
                <Route path="/nodes" element={<NodeManager />} />
                <Route path="/predicates" element={<PredicateEditor />} />
                <Route path="/events" element={<EventTimeline />} />
              </Routes>
            </main>

            {/* Right Panel - Node/Predicate Details */}
            {layoutMode.type === 'desktop' && (
              <aside className="w-80 bg-gray-900 border-l border-gray-700 overflow-y-auto">
                <DetailPanel />
              </aside>
            )}
          </div>

          {/* Status Bar */}
          <footer className="bg-gray-900 border-t border-gray-700 px-4 py-2 text-xs text-gray-500 flex items-center justify-between">
            <div>Aether Mesh Management v1.0.0</div>
            <div className="flex gap-4">
              <span>Connected to: {currentMesh?.name || 'No mesh'}</span>
              <span>Layout: {layoutMode.type}</span>
            </div>
          </footer>
        </div>
      </Router>
    </QueryClientProvider>
  );
}

function NavButton({ icon, label, href }: { icon: string; label: string; href: string }) {
  return (
    <a
      href={href}
      className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800 transition-colors group"
    >
      <span className="text-lg">{icon}</span>
      <span className="text-sm font-medium group-hover:text-cyan-400 transition-colors">{label}</span>
    </a>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-500">{label}</span>
      <span className="font-mono text-cyan-400">{value}</span>
    </div>
  );
}

function DetailPanel() {
  const { selectedNode, selectedPredicate } = useMeshStore();

  return (
    <div className="p-4">
      {selectedNode ? (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-bold mb-2">{selectedNode.id}</h3>
            <div className="space-y-2 text-sm">
              <DetailRow label="Type" value={selectedNode.type} />
              <DetailRow label="Status" value={selectedNode.status} />
              <DetailRow label="Signal Quality" value={`${(selectedNode.signalQuality * 100).toFixed(0)}%`} />
              <DetailRow
                label="Position"
                value={`(${selectedNode.position.x.toFixed(2)}, ${selectedNode.position.y.toFixed(2)}, ${selectedNode.position.z.toFixed(2)})`}
              />
              {selectedNode.isRoot && <DetailRow label="Role" value="ROOT ANCHOR" />}
              {selectedNode.isAdmin && <DetailRow label="Role" value="ADMIN" />}
            </div>
          </div>
        </div>
      ) : selectedPredicate ? (
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-bold mb-2">{selectedPredicate.id}</h3>
            <div className="space-y-2 text-sm">
              <DetailRow label="Type" value={selectedPredicate.type} />
              <DetailRow label="Event Type" value={selectedPredicate.eventType || 'N/A'} />
              <DetailRow label="Hysteresis" value={`${selectedPredicate.hysteresis.toFixed(3)} m`} />
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-8">
          <p>Select a node or predicate to view details</p>
        </div>
      )}
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string | React.ReactNode }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-400">{label}</span>
      <span className="font-mono text-cyan-300">{value}</span>
    </div>
  );
}
