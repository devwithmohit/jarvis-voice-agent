import React, { useState, useEffect } from 'react';
import { Download, Trash2, RefreshCw, Database, Tag, Brain } from 'lucide-react';
import { memoryApi } from '../services/api';

interface Preference {
  id: number;
  category: string;
  key: string;
  value: Record<string, any>;
  created_at: string;
}

interface Behavior {
  id: number;
  behavior_type: string;
  pattern: string;
  confidence: number;
  occurrence_count: number;
  last_seen: string;
}

export const MemoryViewer: React.FC = () => {
  const [preferences, setPreferences] = useState<Preference[]>([]);
  const [behaviors, setBehaviors] = useState<Behavior[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedTab, setSelectedTab] = useState<'preferences' | 'behaviors'>('preferences');

  useEffect(() => {
    loadMemory();
  }, []);

  const loadMemory = async () => {
    setLoading(true);
    try {
      const [prefsData, behaviorsData] = await Promise.all([
        memoryApi.getPreferences(),
        memoryApi.getBehaviors(),
      ]);

      setPreferences(prefsData.preferences || []);
      setBehaviors(behaviorsData.behaviors || []);
    } catch (error) {
      console.error('Failed to load memory:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteBehavior = async (behaviorId: number) => {
    if (!window.confirm('Are you sure you want to delete this learned behavior?')) {
      return;
    }

    try {
      await memoryApi.deleteBehavior(behaviorId);
      await loadMemory();
    } catch (error) {
      console.error('Failed to delete behavior:', error);
      alert('Failed to delete behavior');
    }
  };

  const handleExportMemory = async () => {
    try {
      const data = await memoryApi.exportMemory();

      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: 'application/json'
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `voice-agent-memory-${new Date().toISOString()}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export memory:', error);
      alert('Failed to export memory');
    }
  };

  const handleClearAll = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to delete ALL your memory? This action cannot be undone.'
    );

    if (!confirmed) return;

    const doubleConfirm = window.prompt(
      'Type "DELETE ALL" to confirm:'
    );

    if (doubleConfirm !== 'DELETE ALL') {
      return;
    }

    try {
      await memoryApi.clearAll();
      await loadMemory();
      alert('All memory has been cleared');
    } catch (error) {
      console.error('Failed to clear memory:', error);
      alert('Failed to clear memory');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Database className="w-6 h-6 text-primary-500" />
            <h2 className="text-xl font-semibold text-gray-800">Your Memory</h2>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={loadMemory}
              className="px-3 py-2 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={handleExportMemory}
              className="px-3 py-2 text-sm text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg transition-colors flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </button>
            <button
              onClick={handleClearAll}
              className="px-3 py-2 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors flex items-center space-x-2"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear All</span>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 mt-4">
          <button
            onClick={() => setSelectedTab('preferences')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              selectedTab === 'preferences'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Tag className="w-4 h-4" />
              <span>Preferences ({preferences.length})</span>
            </div>
          </button>
          <button
            onClick={() => setSelectedTab('behaviors')}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              selectedTab === 'behaviors'
                ? 'bg-primary-100 text-primary-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <div className="flex items-center space-x-2">
              <Brain className="w-4 h-4" />
              <span>Learned Behaviors ({behaviors.length})</span>
            </div>
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {selectedTab === 'preferences' && (
          <div className="space-y-3">
            {preferences.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <Tag className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No preferences stored yet</p>
                <p className="text-sm mt-1">Preferences will appear as you use the agent</p>
              </div>
            ) : (
              preferences.map((pref) => (
                <div
                  key={pref.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="px-2 py-1 text-xs font-medium bg-primary-100 text-primary-700 rounded">
                          {pref.category}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {pref.key}
                        </span>
                      </div>
                      <pre className="text-sm text-gray-600 bg-gray-50 p-2 rounded overflow-x-auto">
                        {JSON.stringify(pref.value, null, 2)}
                      </pre>
                      <div className="mt-2 text-xs text-gray-500">
                        Created: {new Date(pref.created_at).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {selectedTab === 'behaviors' && (
          <div className="space-y-3">
            {behaviors.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <Brain className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No learned behaviors yet</p>
                <p className="text-sm mt-1">The agent will learn from your interactions</p>
              </div>
            ) : (
              behaviors.map((behavior) => (
                <div
                  key={behavior.id}
                  className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-700 rounded">
                          {behavior.behavior_type}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                          {behavior.pattern}
                        </span>
                      </div>

                      <div className="flex items-center space-x-4 mt-3">
                        <div className="flex items-center space-x-2">
                          <div className="text-xs text-gray-500">Confidence:</div>
                          <div className="flex-1 h-2 bg-gray-200 rounded-full w-24">
                            <div
                              className="h-full bg-green-500 rounded-full transition-all"
                              style={{ width: `${behavior.confidence * 100}%` }}
                            />
                          </div>
                          <div className="text-xs font-medium text-gray-700">
                            {(behavior.confidence * 100).toFixed(0)}%
                          </div>
                        </div>

                        <div className="text-xs text-gray-500">
                          Occurrences: <span className="font-medium text-gray-700">{behavior.occurrence_count}</span>
                        </div>
                      </div>

                      <div className="mt-2 text-xs text-gray-500">
                        Last seen: {new Date(behavior.last_seen).toLocaleString()}
                      </div>
                    </div>

                    <button
                      onClick={() => handleDeleteBehavior(behavior.id)}
                      className="ml-4 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete behavior"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MemoryViewer;
