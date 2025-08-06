import React, { useEffect, useRef, useState } from 'react';

interface AgentEvent {
  event_type: string;
  run_id: string;
  timestamp: string;
  message?: string;
  input_text?: string;
  tool_name?: string;
  tool_args?: any;
  output?: any;
  content?: string;
  is_complete?: boolean;
  final_output?: string;
  error_message?: string;
  error_type?: string;
}

interface AgentStreamProps {
  baseUrl?: string;
}

const AgentStream: React.FC<AgentStreamProps> = ({ baseUrl = 'ws://localhost:8000' }) => {
  const [inputText, setInputText] = useState('Tell me a joke');
  const [runId, setRunId] = useState<string | null>(null);
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  const startAgentRun = async () => {
    try {
      setError(null);
      setIsRunning(true);

      const response = await fetch(
        `${baseUrl.replace('ws://', 'http://').replace('wss://', 'https://')}/agent/run`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ input_text: inputText }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setRunId(result.run_id);
      setIsRunning(false);

      // Connect to WebSocket stream to see historical events
      connectToStream(result.run_id);
    } catch (err) {
      setError(`Failed to run agent: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setIsRunning(false);
    }
  };

  const connectToStream = (agentRunId: string) => {
    const wsUrl = `${baseUrl}/agent/stream/${agentRunId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const agentEvent: AgentEvent = JSON.parse(event.data);
        setEvents((prev) => [...prev, agentEvent]);

        // Check if agent completed or errored
        if (agentEvent.event_type === 'agent_complete' || agentEvent.event_type === 'agent_error') {
          setIsRunning(false);
          ws.close();
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      setError(`WebSocket error: ${error}`);
      setIsConnected(false);
      setIsRunning(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };
  };

  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsRunning(false);
  };

  const clearEvents = () => {
    setEvents([]);
    setRunId(null);
  };

  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const getEventIcon = (eventType: string) => {
    switch (eventType) {
      case 'agent_start':
        return '🚀';
      case 'tool_call':
        return '🔧';
      case 'tool_output':
        return '📤';
      case 'llm_output':
        return '🤖';
      case 'agent_complete':
        return '✅';
      case 'agent_error':
        return '❌';
      case 'connection_established':
        return '🔗';
      default:
        return '📨';
    }
  };

  const formatEvent = (event: AgentEvent) => {
    const timestamp = new Date(event.timestamp).toLocaleTimeString();

    switch (event.event_type) {
      case 'agent_start':
        return `${timestamp} - Agent started with input: "${event.input_text}"`;
      case 'tool_call':
        return `${timestamp} - Tool called: ${event.tool_name}`;
      case 'tool_output':
        return `${timestamp} - Tool output: ${JSON.stringify(event.output)}`;
      case 'llm_output':
        return `${timestamp} - LLM: ${event.content}`;
      case 'agent_complete':
        return `${timestamp} - Agent completed: ${event.final_output}`;
      case 'agent_error':
        return `${timestamp} - Agent error: ${event.error_message}`;
      default:
        return `${timestamp} - ${event.message || 'Unknown event'}`;
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Agent Streaming Demo</h1>

      {/* Controls */}
      <div className="bg-gray-100 p-4 rounded-lg mb-6">
        <div className="flex gap-4 items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium mb-2">Input Text:</label>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="w-full p-2 border rounded"
              placeholder="Enter your prompt..."
              disabled={isRunning}
            />
          </div>
          <button
            onClick={startAgentRun}
            disabled={isRunning}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 disabled:bg-gray-400"
          >
            {isRunning ? 'Running...' : 'Run Agent'}
          </button>
          <button
            onClick={disconnect}
            disabled={!isConnected}
            className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 disabled:bg-gray-400"
          >
            Disconnect
          </button>
          <button
            onClick={clearEvents}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          >
            Clear
          </button>
        </div>

        {/* Status */}
        <div className="mt-4 flex gap-4 text-sm">
          <span
            className={`px-2 py-1 rounded ${isConnected ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800'}`}
          >
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
          <span
            className={`px-2 py-1 rounded ${isRunning ? 'bg-yellow-200 text-yellow-800' : 'bg-gray-200 text-gray-800'}`}
          >
            {isRunning ? 'Running' : 'Idle'}
          </span>
          {runId && (
            <span className="px-2 py-1 rounded bg-blue-200 text-blue-800">
              Run ID: {runId.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Events Display */}
      <div className="bg-white border rounded-lg">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Agent Events ({events.length})</h2>
        </div>
        <div className="max-h-96 overflow-y-auto">
          {events.length === 0 ? (
            <div className="p-4 text-gray-500 text-center">
              No events yet. Start an agent run to see events here.
            </div>
          ) : (
            <div className="divide-y">
              {events.map((event, index) => (
                <div key={index} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start gap-3">
                    <span className="text-2xl">{getEventIcon(event.event_type)}</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {event.event_type.replace('_', ' ').toUpperCase()}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">{formatEvent(event)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentStream;
