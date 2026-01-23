import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, Loader } from 'lucide-react';
import { VoiceWebSocket } from '../services/websocket';
import { useAudioRecorder } from '../hooks/useAudioRecorder';

interface Message {
  id: string;
  type: 'user' | 'agent';
  text: string;
  timestamp: Date;
  hasAudio?: boolean;
}

export const VoiceInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [transcript, setTranscript] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  const wsRef = useRef<VoiceWebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { isRecording, startRecording, stopRecording, audioLevel } = useAudioRecorder(
    (audioData) => {
      if (wsRef.current?.isConnected()) {
        wsRef.current.sendAudio(audioData);
      }
    }
  );

  useEffect(() => {
    // Initialize WebSocket
    const userId = localStorage.getItem('userId') || 'demo-user';
    const ws = new VoiceWebSocket(userId);

    ws.on('transcript', (data) => {
      setTranscript(data.text);
      if (data.is_final) {
        addMessage('user', data.text);
        setTranscript('');
        setIsProcessing(true);
      }
    });

    ws.on('response', (data) => {
      addMessage('agent', data.text, true);
      playAudio(data.audio);
      setIsProcessing(false);
    });

    ws.on('error', (data) => {
      console.error('WebSocket error:', data);
      setWsConnected(false);
    });

    ws.connect()
      .then(() => setWsConnected(true))
      .catch(console.error);

    wsRef.current = ws;

    return () => {
      ws.disconnect();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const addMessage = (type: 'user' | 'agent', text: string, hasAudio = false) => {
    const message: Message = {
      id: Date.now().toString(),
      type,
      text,
      timestamp: new Date(),
      hasAudio,
    };
    setMessages((prev) => [...prev, message]);
  };

  const playAudio = (audioHex: string) => {
    try {
      // Convert hex to ArrayBuffer
      const bytes = new Uint8Array(
        audioHex.match(/.{1,2}/g)!.map((byte) => parseInt(byte, 16))
      );

      const audioBlob = new Blob([bytes], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);

      audio.play().catch(console.error);
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  };

  const handleToggleRecording = async () => {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${wsConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <h2 className="text-xl font-semibold text-gray-800">Voice AI Agent</h2>
        </div>
        <div className="text-sm text-gray-500">
          {wsConnected ? 'Connected' : 'Disconnected'}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Mic className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <p className="text-lg">Start a conversation</p>
            <p className="text-sm mt-2">Click the microphone button to begin</p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-3 ${
                message.type === 'user'
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <div className="flex items-center justify-between mt-2 text-xs opacity-70">
                <span>{message.timestamp.toLocaleTimeString()}</span>
                {message.hasAudio && <Volume2 className="w-3 h-3" />}
              </div>
            </div>
          </div>
        ))}

        {transcript && (
          <div className="flex justify-end">
            <div className="max-w-[70%] rounded-lg p-3 bg-primary-300 text-white opacity-70">
              <p className="text-sm italic">{transcript}...</p>
            </div>
          </div>
        )}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="max-w-[70%] rounded-lg p-3 bg-gray-100">
              <Loader className="w-5 h-5 animate-spin text-gray-500" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Voice Control */}
      <div className="p-6 border-t border-gray-200">
        <div className="flex items-center justify-center space-x-6">
          {/* Audio Level Indicator */}
          {isRecording && (
            <div className="flex items-center space-x-2">
              <div className="flex space-x-1">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-primary-500 rounded-full transition-all duration-100"
                    style={{
                      height: `${Math.max(8, audioLevel * 40 * (i + 1) / 5)}px`,
                    }}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Recording Button */}
          <button
            onClick={handleToggleRecording}
            disabled={!wsConnected}
            className={`relative w-20 h-20 rounded-full transition-all duration-200 ${
              isRecording
                ? 'bg-red-500 hover:bg-red-600 recording-active'
                : 'bg-primary-500 hover:bg-primary-600'
            } ${!wsConnected ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            shadow-lg hover:shadow-xl flex items-center justify-center`}
          >
            {isRecording ? (
              <MicOff className="w-8 h-8 text-white" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}

            {isRecording && (
              <div className="absolute inset-0 rounded-full border-4 border-red-500 animate-pulse-ring" />
            )}
          </button>

          {/* Status Text */}
          <div className="text-sm text-gray-600 min-w-[100px]">
            {isRecording ? (
              <span className="text-red-500 font-medium">Recording...</span>
            ) : isProcessing ? (
              <span className="text-primary-500 font-medium">Processing...</span>
            ) : (
              <span>Click to speak</span>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-4 text-center text-xs text-gray-500">
          <p>Click the microphone and speak naturally</p>
          <p className="mt-1">The agent will respond with voice and text</p>
        </div>
      </div>
    </div>
  );
};

export default VoiceInterface;
