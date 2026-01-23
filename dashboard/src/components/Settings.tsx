import React, { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Save, Volume2, Mic, Zap } from 'lucide-react';
import { settingsApi } from '../services/api';

interface UserSettings {
  voice: {
    speech_rate: number;
    pitch: number;
    volume: number;
    auto_play_responses: boolean;
  };
  agent: {
    response_style: 'concise' | 'detailed' | 'conversational';
    confirmation_level: 'none' | 'medium' | 'high';
    wake_word_enabled: boolean;
    wake_word_sensitivity: number;
  };
  privacy: {
    store_conversations: boolean;
    learn_from_behavior: boolean;
    share_anonymous_data: boolean;
  };
}

export const Settings: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings>({
    voice: {
      speech_rate: 1.0,
      pitch: 1.0,
      volume: 1.0,
      auto_play_responses: true,
    },
    agent: {
      response_style: 'conversational',
      confirmation_level: 'medium',
      wake_word_enabled: true,
      wake_word_sensitivity: 0.5,
    },
    privacy: {
      store_conversations: true,
      learn_from_behavior: true,
      share_anonymous_data: false,
    },
  });

  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const data = await settingsApi.getSettings();
      if (data.settings) {
        setSettings(data.settings);
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);

    try {
      await settingsApi.updateSettings(settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const updateVoiceSetting = (key: keyof UserSettings['voice'], value: any) => {
    setSettings((prev) => ({
      ...prev,
      voice: { ...prev.voice, [key]: value },
    }));
  };

  const updateAgentSetting = (key: keyof UserSettings['agent'], value: any) => {
    setSettings((prev) => ({
      ...prev,
      agent: { ...prev.agent, [key]: value },
    }));
  };

  const updatePrivacySetting = (key: keyof UserSettings['privacy'], value: any) => {
    setSettings((prev) => ({
      ...prev,
      privacy: { ...prev.privacy, [key]: value },
    }));
  };

  return (
    <div className="h-full flex flex-col bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <SettingsIcon className="w-6 h-6 text-primary-500" />
          <h2 className="text-xl font-semibold text-gray-800">Settings</h2>
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className={`px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors flex items-center space-x-2 ${
            saved
              ? 'bg-green-600 hover:bg-green-700'
              : 'bg-primary-600 hover:bg-primary-700'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <Save className="w-4 h-4" />
          <span>{saving ? 'Saving...' : saved ? 'Saved!' : 'Save Changes'}</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">
        {/* Voice Settings */}
        <section>
          <div className="flex items-center space-x-2 mb-4">
            <Volume2 className="w-5 h-5 text-gray-700" />
            <h3 className="text-lg font-semibold text-gray-800">Voice Settings</h3>
          </div>

          <div className="space-y-4">
            {/* Speech Rate */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Speech Rate: {settings.voice.speech_rate.toFixed(1)}x
              </label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={settings.voice.speech_rate}
                onChange={(e) => updateVoiceSetting('speech_rate', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Slower</span>
                <span>Faster</span>
              </div>
            </div>

            {/* Pitch */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Pitch: {settings.voice.pitch.toFixed(1)}
              </label>
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={settings.voice.pitch}
                onChange={(e) => updateVoiceSetting('pitch', parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Lower</span>
                <span>Higher</span>
              </div>
            </div>

            {/* Volume */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Volume: {Math.round(settings.voice.volume * 100)}%
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.voice.volume}
                onChange={(e) => updateVoiceSetting('volume', parseFloat(e.target.value))}
                className="w-full"
              />
            </div>

            {/* Auto-play */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Auto-play voice responses
              </label>
              <input
                type="checkbox"
                checked={settings.voice.auto_play_responses}
                onChange={(e) => updateVoiceSetting('auto_play_responses', e.target.checked)}
                className="w-5 h-5 text-primary-600 rounded"
              />
            </div>
          </div>
        </section>

        {/* Agent Settings */}
        <section>
          <div className="flex items-center space-x-2 mb-4">
            <Zap className="w-5 h-5 text-gray-700" />
            <h3 className="text-lg font-semibold text-gray-800">Agent Behavior</h3>
          </div>

          <div className="space-y-4">
            {/* Response Style */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Response Style
              </label>
              <select
                value={settings.agent.response_style}
                onChange={(e) => updateAgentSetting('response_style', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="concise">Concise - Brief and to the point</option>
                <option value="detailed">Detailed - Comprehensive explanations</option>
                <option value="conversational">Conversational - Natural and friendly</option>
              </select>
            </div>

            {/* Confirmation Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Action Confirmation Level
              </label>
              <select
                value={settings.agent.confirmation_level}
                onChange={(e) => updateAgentSetting('confirmation_level', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="none">None - Execute immediately</option>
                <option value="medium">Medium - Confirm risky actions</option>
                <option value="high">High - Confirm all actions</option>
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Controls when the agent asks for confirmation before executing tools
              </p>
            </div>

            {/* Wake Word */}
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Enable wake word detection
              </label>
              <input
                type="checkbox"
                checked={settings.agent.wake_word_enabled}
                onChange={(e) => updateAgentSetting('wake_word_enabled', e.target.checked)}
                className="w-5 h-5 text-primary-600 rounded"
              />
            </div>

            {/* Wake Word Sensitivity */}
            {settings.agent.wake_word_enabled && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Wake Word Sensitivity: {settings.agent.wake_word_sensitivity.toFixed(1)}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={settings.agent.wake_word_sensitivity}
                  onChange={(e) => updateAgentSetting('wake_word_sensitivity', parseFloat(e.target.value))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Less sensitive</span>
                  <span>More sensitive</span>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Privacy Settings */}
        <section>
          <div className="flex items-center space-x-2 mb-4">
            <Mic className="w-5 h-5 text-gray-700" />
            <h3 className="text-lg font-semibold text-gray-800">Privacy & Data</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Store conversation history
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Save conversations for context and memory
                </p>
              </div>
              <input
                type="checkbox"
                checked={settings.privacy.store_conversations}
                onChange={(e) => updatePrivacySetting('store_conversations', e.target.checked)}
                className="w-5 h-5 text-primary-600 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Learn from my behavior
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Allow agent to learn patterns and preferences
                </p>
              </div>
              <input
                type="checkbox"
                checked={settings.privacy.learn_from_behavior}
                onChange={(e) => updatePrivacySetting('learn_from_behavior', e.target.checked)}
                className="w-5 h-5 text-primary-600 rounded"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Share anonymous usage data
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Help improve the service (no personal info)
                </p>
              </div>
              <input
                type="checkbox"
                checked={settings.privacy.share_anonymous_data}
                onChange={(e) => updatePrivacySetting('share_anonymous_data', e.target.checked)}
                className="w-5 h-5 text-primary-600 rounded"
              />
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Settings;
