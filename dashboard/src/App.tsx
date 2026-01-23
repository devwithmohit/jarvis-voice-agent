import React, { useState } from 'react';
import { BrowserRouter as Router, Link } from 'react-router-dom';
import { MessageSquare, Database, Settings as SettingsIcon, Activity } from 'lucide-react';
import VoiceInterface from './components/VoiceInterface';
import MemoryViewer from './components/MemoryViewer';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState('voice');

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-lg flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Voice AI Agent</h1>
                <p className="text-sm text-gray-500">Production-grade conversational AI</p>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <div className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium flex items-center space-x-2">
                <Activity className="w-4 h-4" />
                <span>All Services Online</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-140px)]">
          {/* Sidebar Navigation */}
          <div className="col-span-2">
            <nav className="bg-white rounded-lg shadow-lg p-2 space-y-1">
              <button
                onClick={() => setActiveTab('voice')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  activeTab === 'voice'
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <MessageSquare className="w-5 h-5" />
                <span className="font-medium">Voice Chat</span>
              </button>

              <button
                onClick={() => setActiveTab('memory')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  activeTab === 'memory'
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Database className="w-5 h-5" />
                <span className="font-medium">Memory</span>
              </button>

              <button
                onClick={() => setActiveTab('settings')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                  activeTab === 'settings'
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <SettingsIcon className="w-5 h-5" />
                <span className="font-medium">Settings</span>
              </button>
            </nav>

            {/* Info Panel */}
            <div className="mt-4 bg-white rounded-lg shadow-lg p-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Quick Stats</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Conversations</span>
                  <span className="font-medium text-gray-700">127</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Actions</span>
                  <span className="font-medium text-gray-700">43</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Uptime</span>
                  <span className="font-medium text-green-600">99.8%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content Area */}
          <div className="col-span-10">
            {activeTab === 'voice' && <VoiceInterface />}
            {activeTab === 'memory' && <MemoryViewer />}
            {activeTab === 'settings' && <Settings />}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-gray-500">
          <div>Voice AI Agent v0.1.0 - Phase 6 Complete</div>
          <div className="flex items-center space-x-4">
            <span>© 2026 Voice AI Agent</span>
            <Link to="/privacy" className="hover:text-primary-600">Privacy</Link>
            <Link to="/terms" className="hover:text-primary-600">Terms</Link>
          </div>
        </div>
      </footer>
    </div>
    </Router>
  );
}

export default App;
