/**
 * Constitutional Fidelity Monitor Component
 *
 * Real-time monitoring dashboard for constitutional compliance with:
 * - Live fidelity score tracking with historical trend analysis
 * - Visual indicators for compliance levels (green: >0.85, amber: 0.70-0.85, red: <0.70)
 * - Alert notifications for violations with <30 second response time
 * - Performance metrics integration with QEC-inspired error correction
 * - WebSocket integration for real-time updates
 *
 * Task 19.1: ConstitutionalFidelityMonitor Component - Enhanced Implementation
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';

// Basic UI Components
const Card = ({ children, className = "" }) => (
  <div className={`bg-white rounded-lg border shadow-sm ${className}`}>
    {children}
  </div>
);

const CardHeader = ({ children, className = "" }) => (
  <div className={`p-6 pb-2 ${className}`}>
    {children}
  </div>
);

const CardContent = ({ children, className = "" }) => (
  <div className={`p-6 pt-0 ${className}`}>
    {children}
  </div>
);

const CardTitle = ({ children, className = "" }) => (
  <h3 className={`text-lg font-semibold leading-none tracking-tight ${className}`}>
    {children}
  </h3>
);

const Alert = ({ children, className = "" }) => (
  <div className={`relative w-full rounded-lg border p-4 ${className}`}>
    {children}
  </div>
);

const AlertDescription = ({ children, className = "" }) => (
  <div className={`text-sm ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, className = "", variant = "default" }) => (
  <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${className}`}>
    {children}
  </span>
);

const Progress = ({ value = 0, className = "" }) => (
  <div className={`w-full bg-gray-200 rounded-full h-2 ${className}`}>
    <div
      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
      style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
    />
  </div>
);

const Button = ({ children, onClick, variant = "default", size = "default", className = "", disabled = false }) => (
  <button
    onClick={onClick}
    disabled={disabled}
    className={`inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors
      ${variant === 'outline' ? 'border border-gray-300 bg-white hover:bg-gray-50' : 'bg-blue-600 text-white hover:bg-blue-700'}
      ${size === 'sm' ? 'h-8 px-3 text-xs' : 'h-10 px-4'}
      ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      ${className}`}
  >
    {children}
  </button>
);

const Tabs = ({ children, defaultValue, className = "" }) => {
  const [activeTab, setActiveTab] = useState(defaultValue);

  return (
    <div className={className}>
      {React.Children.map(children, child =>
        React.cloneElement(child, { activeTab, setActiveTab })
      )}
    </div>
  );
};

const TabsList = ({ children, activeTab, setActiveTab }) => (
  <div className="inline-flex h-10 items-center justify-center rounded-md bg-gray-100 p-1 text-gray-500">
    {React.Children.map(children, child =>
      React.cloneElement(child, { activeTab, setActiveTab })
    )}
  </div>
);

const TabsTrigger = ({ children, value, activeTab, setActiveTab }) => (
  <button
    onClick={() => setActiveTab(value)}
    className={`inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-white transition-all
      ${activeTab === value ? 'bg-white text-gray-950 shadow-sm' : 'hover:bg-gray-200'}`}
  >
    {children}
  </button>
);

const TabsContent = ({ children, value, activeTab }) => (
  activeTab === value ? <div>{children}</div> : null
);

// Simple SVG Icons
const AlertTriangle = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
  </svg>
);

const CheckCircle = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const XCircle = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Activity = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const TrendingUp = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
  </svg>
);

const TrendingDown = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
  </svg>
);

const Wifi = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
  </svg>
);

const WifiOff = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636L5.636 18.364m12.728 0L5.636 5.636m7.071 7.071l2.122-2.122M9.879 9.879l2.122-2.122" />
  </svg>
);

const Clock = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const Shield = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
);

const BarChart3 = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
  </svg>
);

const RefreshCw = ({ className = "" }) => (
  <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

// Simple Line Chart Component
const SimpleLineChart = ({ data, className = "" }) => {
  if (!data || data.length === 0) return null;

  const width = 400;
  const height = 200;
  const padding = 40;

  const maxScore = Math.max(...data.map(d => d.score));
  const minScore = Math.min(...data.map(d => d.score));
  const scoreRange = maxScore - minScore || 1;

  const points = data.map((d, i) => {
    const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
    const y = height - padding - ((d.score - minScore) / scoreRange) * (height - 2 * padding);
    return `${x},${y}`;
  }).join(' ');

  return (
    <div className={`w-full ${className}`}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} className="border rounded">
        {/* Grid lines */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Threshold lines */}
        <line
          x1={padding}
          y1={height - padding - (0.85 * (height - 2 * padding))}
          x2={width - padding}
          y2={height - padding - (0.85 * (height - 2 * padding))}
          stroke="#16a34a"
          strokeDasharray="5,5"
          strokeWidth="1"
        />
        <line
          x1={padding}
          y1={height - padding - (0.70 * (height - 2 * padding))}
          x2={width - padding}
          y2={height - padding - (0.70 * (height - 2 * padding))}
          stroke="#ca8a04"
          strokeDasharray="5,5"
          strokeWidth="1"
        />

        {/* Data line */}
        <polyline
          fill="none"
          stroke="#2563eb"
          strokeWidth="2"
          points={points}
        />

        {/* Data points */}
        {data.map((d, i) => {
          const x = padding + (i / (data.length - 1)) * (width - 2 * padding);
          const y = height - padding - ((d.score - minScore) / scoreRange) * (height - 2 * padding);
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="3"
              fill="#2563eb"
              stroke="white"
              strokeWidth="2"
            />
          );
        })}

        {/* Axes */}
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#374151" strokeWidth="1"/>
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} stroke="#374151" strokeWidth="1"/>

        {/* Labels */}
        <text x={padding} y={height - 10} fontSize="12" fill="#6b7280">0%</text>
        <text x={width - padding} y={height - 10} fontSize="12" fill="#6b7280" textAnchor="end">100%</text>
      </svg>
    </div>
  );
};

const ConstitutionalFidelityMonitor = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [fidelityScores, setFidelityScores] = useState({});
  const [performanceMetrics, setPerformanceMetrics] = useState({});
  const [alerts, setAlerts] = useState([]);
  const [subscribedWorkflows, setSubscribedWorkflows] = useState(new Set());
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // Enhanced state for historical tracking and real-time monitoring
  const [fidelityHistory, setFidelityHistory] = useState([]);
  const [currentFidelityScore, setCurrentFidelityScore] = useState(null);
  const [alertLevel, setAlertLevel] = useState('green');
  const [violationCount, setViolationCount] = useState(0);
  const [violationAlerts, setViolationAlerts] = useState([]);
  const [escalationNotifications, setEscalationNotifications] = useState([]);
  const [lastUpdateTime, setLastUpdateTime] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // 30 seconds

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const refreshIntervalRef = useRef(null);
  const maxReconnectAttempts = 5;
  const [reconnectAttempts, setReconnectAttempts] = useState(0);

  // Fidelity thresholds for alert levels
  const FIDELITY_THRESHOLDS = {
    green: 0.85,
    amber: 0.70,
    red: 0.55
  };

  // Enhanced WebSocket connection management with auto-refresh
  useEffect(() => {
    connectWebSocket();

    if (autoRefresh) {
      startAutoRefresh();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  // Auto-refresh management
  useEffect(() => {
    if (autoRefresh && isConnected) {
      startAutoRefresh();
    } else {
      stopAutoRefresh();
    }

    return () => stopAutoRefresh();
  }, [autoRefresh, isConnected, refreshInterval]);

  const startAutoRefresh = useCallback(() => {
    stopAutoRefresh();
    refreshIntervalRef.current = setInterval(() => {
      if (isConnected) {
        sendMessage({ type: 'get_performance_metrics' });
        sendMessage({ type: 'get_fidelity_status' });
      }
    }, refreshInterval * 1000);
  }, [isConnected, refreshInterval]);

  const stopAutoRefresh = useCallback(() => {
    if (refreshIntervalRef.current) {
      clearInterval(refreshIntervalRef.current);
      refreshIntervalRef.current = null;
    }
  }, []);

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8004/api/v1/ws/fidelity-monitor`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('Constitutional Fidelity Monitor WebSocket connected');
        setIsConnected(true);
        setConnectionStatus('connected');
        setReconnectAttempts(0);
        
        // Request initial performance metrics
        sendMessage({
          type: 'get_performance_metrics'
        });
      };
      
      wsRef.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      wsRef.current.onclose = () => {
        console.log('Constitutional Fidelity Monitor WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.pow(2, reconnectAttempts) * 1000; // Exponential backoff
          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts(prev => prev + 1);
            connectWebSocket();
          }, delay);
        }
      };
      
      wsRef.current.onerror = (error) => {
        console.error('Constitutional Fidelity Monitor WebSocket error:', error);
        setConnectionStatus('error');
      };
      
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      setConnectionStatus('error');
    }
  };

  const sendMessage = (message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  const handleWebSocketMessage = (message) => {
    const timestamp = new Date().toISOString();
    setLastUpdateTime(timestamp);

    switch (message.type) {
      case 'connection_established':
        console.log('Fidelity monitor connection established:', message.session_id);
        // Request initial data
        sendMessage({ type: 'get_performance_metrics' });
        sendMessage({ type: 'get_fidelity_status' });
        break;

      case 'fidelity_update':
        const fidelityScore = message.fidelity_score;
        setFidelityScores(prev => ({
          ...prev,
          [message.workflow_id]: {
            ...fidelityScore,
            timestamp: message.timestamp
          }
        }));

        // Update current fidelity score and history
        if (fidelityScore.overall_score !== undefined) {
          setCurrentFidelityScore(fidelityScore.overall_score);
          updateFidelityHistory(fidelityScore.overall_score, message.timestamp);
          updateAlertLevel(fidelityScore.overall_score);
        }
        break;

      case 'fidelity_status':
        // Handle comprehensive fidelity status updates
        if (message.current_fidelity_score !== undefined) {
          setCurrentFidelityScore(message.current_fidelity_score);
          updateFidelityHistory(message.current_fidelity_score, timestamp);
          updateAlertLevel(message.current_fidelity_score);
        }
        if (message.violation_count !== undefined) {
          setViolationCount(message.violation_count);
        }
        break;

      case 'performance_metrics':
        setPerformanceMetrics(message.metrics);

        // Extract overall fidelity score from performance metrics
        const overallScore = message.metrics?.overall?.overall_success_rate;
        if (overallScore !== undefined) {
          setCurrentFidelityScore(overallScore);
          updateFidelityHistory(overallScore, timestamp);
          updateAlertLevel(overallScore);
        }
        break;

      case 'alert':
        setAlerts(prev => [message.alert, ...prev.slice(0, 19)]); // Keep last 20 alerts

        // Update violation count if alert contains violations
        if (message.alert.violations !== undefined) {
          setViolationCount(prev => prev + message.alert.violations);
        }
        break;

      case 'violation_alert':
        setViolationAlerts(prev => [message.alert, ...prev.slice(0, 19)]); // Keep last 20 violation alerts

        // Update violation count
        setViolationCount(prev => prev + 1);

        // Update alert level based on violation severity
        if (message.alert.severity === 'critical') {
          setAlertLevel('red');
        } else if (message.alert.severity === 'high' && alertLevel !== 'red') {
          setAlertLevel('amber');
        }
        break;

      case 'escalation_notification':
        setEscalationNotifications(prev => [message.escalation, ...prev.slice(0, 19)]); // Keep last 20 escalations

        // Show critical escalation alert
        if (message.escalation.escalation_level === 'emergency_response') {
          setAlertLevel('red');
        }
        break;

      case 'subscription_confirmed':
        setSubscribedWorkflows(prev => new Set([...prev, message.workflow_id]));
        break;

      case 'unsubscription_confirmed':
        setSubscribedWorkflows(prev => {
          const newSet = new Set(prev);
          newSet.delete(message.workflow_id);
          return newSet;
        });
        break;

      case 'error':
        console.error('WebSocket error:', message.message);
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  };

  // Helper function to update fidelity history for trend analysis
  const updateFidelityHistory = useCallback((score, timestamp) => {
    setFidelityHistory(prev => {
      const newEntry = {
        score: score,
        timestamp: timestamp,
        time: new Date(timestamp).getTime()
      };

      const updated = [...prev, newEntry];
      // Keep last 100 entries for trend analysis
      return updated.slice(-100);
    });
  }, []);

  // Helper function to update alert level based on fidelity score
  const updateAlertLevel = useCallback((score) => {
    if (score >= FIDELITY_THRESHOLDS.green) {
      setAlertLevel('green');
    } else if (score >= FIDELITY_THRESHOLDS.amber) {
      setAlertLevel('amber');
    } else {
      setAlertLevel('red');
    }
  }, []);

  const subscribeToWorkflow = (workflowId) => {
    sendMessage({
      type: 'subscribe_workflow',
      workflow_id: workflowId
    });
  };

  const unsubscribeFromWorkflow = (workflowId) => {
    sendMessage({
      type: 'unsubscribe_workflow',
      workflow_id: workflowId
    });
  };

  const getComplianceLevelColor = (level) => {
    switch (level) {
      case 'fully_compliant':
        return 'bg-green-500';
      case 'mostly_compliant':
        return 'bg-blue-500';
      case 'partially_compliant':
        return 'bg-yellow-500';
      case 'non_compliant':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getComplianceLevelIcon = (level) => {
    switch (level) {
      case 'fully_compliant':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'mostly_compliant':
        return <CheckCircle className="h-4 w-4 text-blue-500" />;
      case 'partially_compliant':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'non_compliant':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Activity className="h-4 w-4 text-gray-500" />;
    }
  };

  const getAlertSeverityColor = (severity) => {
    switch (severity) {
      case 'green':
        return 'border-green-500 bg-green-50';
      case 'amber':
        return 'border-yellow-500 bg-yellow-50';
      case 'red':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-500 bg-gray-50';
    }
  };

  // Enhanced helper functions for fidelity score visualization
  const getFidelityScoreColor = (score) => {
    if (score >= FIDELITY_THRESHOLDS.green) return 'text-green-600';
    if (score >= FIDELITY_THRESHOLDS.amber) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getFidelityScoreBgColor = (score) => {
    if (score >= FIDELITY_THRESHOLDS.green) return 'bg-green-100';
    if (score >= FIDELITY_THRESHOLDS.amber) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getFidelityTrend = () => {
    if (fidelityHistory.length < 2) return null;

    const recent = fidelityHistory.slice(-5);
    const trend = recent[recent.length - 1].score - recent[0].score;

    if (Math.abs(trend) < 0.01) return null;
    return trend > 0 ? 'up' : 'down';
  };

  const formatScore = (score) => {
    return (score * 100).toFixed(1) + '%';
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const ConnectionStatus = () => (
    <div className="flex items-center space-x-2">
      {isConnected ? (
        <>
          <Wifi className="h-4 w-4 text-green-500" />
          <span className="text-sm text-green-600">Connected</span>
        </>
      ) : (
        <>
          <WifiOff className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-600">
            {connectionStatus === 'error' ? 'Connection Error' : 'Disconnected'}
          </span>
          {reconnectAttempts > 0 && (
            <span className="text-xs text-gray-500">
              (Attempt {reconnectAttempts}/{maxReconnectAttempts})
            </span>
          )}
        </>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Enhanced Header with Real-time Status */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Constitutional Fidelity Monitor</h2>
          <div className="flex items-center space-x-4 mt-2">
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-blue-500" />
              <span className="text-sm text-gray-600">
                Current Score:
                <span className={`ml-1 font-bold ${currentFidelityScore ? getFidelityScoreColor(currentFidelityScore) : 'text-gray-500'}`}>
                  {currentFidelityScore ? formatScore(currentFidelityScore) : 'N/A'}
                </span>
              </span>
              {getFidelityTrend() && (
                getFidelityTrend() === 'up' ?
                  <TrendingUp className="h-4 w-4 text-green-500" /> :
                  <TrendingDown className="h-4 w-4 text-red-500" />
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-gray-500" />
              <span className="text-sm text-gray-600">
                Last Update: {lastUpdateTime ? formatTimestamp(lastUpdateTime) : 'Never'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={autoRefresh ? 'bg-green-50 border-green-200' : ''}
            >
              <RefreshCw className={`h-4 w-4 mr-1 ${autoRefresh ? 'animate-spin' : ''}`} />
              Auto Refresh
            </Button>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="text-sm border rounded px-2 py-1"
              disabled={!autoRefresh}
            >
              <option value={10}>10s</option>
              <option value={30}>30s</option>
              <option value={60}>1m</option>
              <option value={300}>5m</option>
            </select>
          </div>
          <ConnectionStatus />
        </div>
      </div>

      {/* Alert Level Indicator */}
      {currentFidelityScore !== null && (
        <Alert className={`${
          alertLevel === 'green' ? 'border-green-500 bg-green-50' :
          alertLevel === 'amber' ? 'border-yellow-500 bg-yellow-50' :
          'border-red-500 bg-red-50'
        }`}>
          <Shield className="h-4 w-4" />
          <AlertDescription>
            <div className="flex justify-between items-center">
              <span>
                Constitutional Fidelity Level:
                <strong className="ml-1">
                  {alertLevel === 'green' ? 'EXCELLENT' :
                   alertLevel === 'amber' ? 'CAUTION' : 'CRITICAL'}
                </strong>
                {violationCount > 0 && (
                  <span className="ml-2 text-sm">
                    ({violationCount} violations detected)
                  </span>
                )}
              </span>
              <Badge variant="outline" className={`${
                alertLevel === 'green' ? 'border-green-500 text-green-700' :
                alertLevel === 'amber' ? 'border-yellow-500 text-yellow-700' :
                'border-red-500 text-red-700'
              }`}>
                {formatScore(currentFidelityScore)}
              </Badge>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Main Dashboard */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Historical Trends</TabsTrigger>
          <TabsTrigger value="workflows">Workflows</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
          <TabsTrigger value="alerts">Alerts</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        {/* Enhanced Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Current Fidelity Score */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Current Fidelity Score</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${currentFidelityScore ? getFidelityScoreColor(currentFidelityScore) : 'text-gray-500'}`}>
                  {currentFidelityScore ? formatScore(currentFidelityScore) : 'N/A'}
                </div>
                <Progress
                  value={(currentFidelityScore || 0) * 100}
                  className="mt-2"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>Target: {formatScore(FIDELITY_THRESHOLDS.green)}</span>
                  <span>Alert: {formatScore(FIDELITY_THRESHOLDS.amber)}</span>
                </div>
              </CardContent>
            </Card>

            {/* Active Workflows */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Active Workflows</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{Object.keys(fidelityScores).length}</div>
                <p className="text-xs text-gray-500 mt-1">
                  {subscribedWorkflows.size} subscribed
                </p>
                <div className="flex items-center mt-2">
                  <Activity className="h-3 w-3 text-blue-500 mr-1" />
                  <span className="text-xs text-gray-600">Real-time monitoring</span>
                </div>
              </CardContent>
            </Card>

            {/* Constitutional Violations */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Constitutional Violations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${violationCount > 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {violationCount}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {violationCount === 0 ? 'No violations' : 'Violations detected'}
                </p>
                <div className="flex items-center mt-2">
                  {violationCount === 0 ?
                    <CheckCircle className="h-3 w-3 text-green-500 mr-1" /> :
                    <AlertTriangle className="h-3 w-3 text-red-500 mr-1" />
                  }
                  <span className="text-xs text-gray-600">
                    {violationCount === 0 ? 'Compliant' : 'Needs attention'}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Recent Alerts */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Recent Alerts</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{alerts.length}</div>
                <div className="flex space-x-1 mt-1">
                  {alerts.slice(0, 5).map((alert, index) => (
                    <div
                      key={index}
                      className={`w-2 h-2 rounded-full ${
                        alert.severity === 'red' ? 'bg-red-500' :
                        alert.severity === 'amber' ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      title={`${alert.severity.toUpperCase()}: ${alert.message}`}
                    />
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Last 24 hours
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Recent Fidelity Scores */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Workflow Scores</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(fidelityScores).slice(0, 5).map(([workflowId, score]) => (
                  <div key={workflowId} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      {getComplianceLevelIcon(score.compliance_level)}
                      <div>
                        <p className="font-medium">{workflowId}</p>
                        <p className="text-sm text-gray-500">
                          {new Date(score.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold">{formatScore(score.overall_score)}</p>
                      <Badge className={getComplianceLevelColor(score.compliance_level)}>
                        {score.compliance_level.replace('_', ' ')}
                      </Badge>
                    </div>
                  </div>
                ))}
                {Object.keys(fidelityScores).length === 0 && (
                  <p className="text-gray-500 text-center py-4">No workflow scores available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Historical Trends Tab */}
        <TabsContent value="trends" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <BarChart3 className="h-5 w-5 mr-2" />
                Constitutional Fidelity Trends
              </CardTitle>
            </CardHeader>
            <CardContent>
              {fidelityHistory.length > 0 ? (
                <div className="space-y-4">
                  <SimpleLineChart
                    data={fidelityHistory.slice(-50)}
                    className="h-64"
                  />
                  <div className="flex justify-between text-sm text-gray-600">
                    <div className="flex items-center">
                      <div className="w-3 h-0.5 bg-green-500 mr-2"></div>
                      <span>Target (85%)</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-0.5 bg-yellow-500 mr-2"></div>
                      <span>Warning (70%)</span>
                    </div>
                    <div className="flex items-center">
                      <div className="w-3 h-0.5 bg-blue-600 mr-2"></div>
                      <span>Current Score</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-500">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No historical data available</p>
                    <p className="text-sm">Data will appear as the system collects fidelity scores</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Trend Analysis Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Average Score (24h)</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {fidelityHistory.length > 0 ?
                    formatScore(fidelityHistory.reduce((sum, entry) => sum + entry.score, 0) / fidelityHistory.length) :
                    'N/A'
                  }
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Trend Direction</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  {getFidelityTrend() === 'up' && (
                    <>
                      <TrendingUp className="h-6 w-6 text-green-500 mr-2" />
                      <span className="text-green-600 font-medium">Improving</span>
                    </>
                  )}
                  {getFidelityTrend() === 'down' && (
                    <>
                      <TrendingDown className="h-6 w-6 text-red-500 mr-2" />
                      <span className="text-red-600 font-medium">Declining</span>
                    </>
                  )}
                  {!getFidelityTrend() && (
                    <>
                      <Activity className="h-6 w-6 text-gray-500 mr-2" />
                      <span className="text-gray-600 font-medium">Stable</span>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Data Points</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{fidelityHistory.length}</div>
                <p className="text-xs text-gray-500 mt-1">
                  {fidelityHistory.length > 0 ?
                    `Since ${new Date(fidelityHistory[0].timestamp).toLocaleDateString()}` :
                    'No data collected'
                  }
                </p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Workflows Tab */}
        <TabsContent value="workflows" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Subscriptions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Enter workflow ID"
                    className="flex-1 px-3 py-2 border rounded-md"
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && e.target.value.trim()) {
                        subscribeToWorkflow(e.target.value.trim());
                        e.target.value = '';
                      }
                    }}
                  />
                  <Button
                    onClick={() => {
                      const input = document.querySelector('input[placeholder="Enter workflow ID"]');
                      if (input.value.trim()) {
                        subscribeToWorkflow(input.value.trim());
                        input.value = '';
                      }
                    }}
                  >
                    Subscribe
                  </Button>
                </div>
                
                <div className="space-y-2 mt-4">
                  {Array.from(subscribedWorkflows).map(workflowId => (
                    <div key={workflowId} className="flex items-center justify-between p-2 border rounded">
                      <span>{workflowId}</span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => unsubscribeFromWorkflow(workflowId)}
                      >
                        Unsubscribe
                      </Button>
                    </div>
                  ))}
                  {subscribedWorkflows.size === 0 && (
                    <p className="text-gray-500 text-center py-4">No workflow subscriptions</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Violations Tab */}
        <TabsContent value="violations" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Violation Alerts */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-red-500" />
                  Constitutional Violations
                  {violationAlerts.length > 0 && (
                    <Badge variant="destructive" className="ml-2">
                      {violationAlerts.length}
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {violationAlerts.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                      <p>No constitutional violations detected</p>
                    </div>
                  ) : (
                    violationAlerts.map((alert, index) => (
                      <div
                        key={alert.alert_id || index}
                        className={`p-3 rounded-lg border-l-4 ${
                          alert.severity === 'critical' ? 'border-red-500 bg-red-50' :
                          alert.severity === 'high' ? 'border-orange-500 bg-orange-50' :
                          alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                          'border-blue-500 bg-blue-50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h4 className="font-medium text-sm">{alert.title}</h4>
                              <Badge variant="outline" className={`text-xs ${
                                alert.severity === 'critical' ? 'border-red-500 text-red-700' :
                                alert.severity === 'high' ? 'border-orange-500 text-orange-700' :
                                alert.severity === 'medium' ? 'border-yellow-500 text-yellow-700' :
                                'border-blue-500 text-blue-700'
                              }`}>
                                {alert.severity}
                              </Badge>
                              {alert.escalated && (
                                <Badge variant="destructive" className="text-xs">
                                  Escalated
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-gray-600 mt-1">{alert.description}</p>
                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                              <span>Type: {alert.violation_type?.replace('_', ' ')}</span>
                              {alert.fidelity_score && (
                                <span>Fidelity: {(alert.fidelity_score * 100).toFixed(1)}%</span>
                              )}
                              {alert.distance_score && (
                                <span>Distance: {(alert.distance_score * 100).toFixed(1)}%</span>
                              )}
                            </div>
                            {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                              <div className="mt-2">
                                <p className="text-xs font-medium text-gray-700">Recommended Actions:</p>
                                <ul className="text-xs text-gray-600 list-disc list-inside">
                                  {alert.recommended_actions.slice(0, 2).map((action, idx) => (
                                    <li key={idx}>{action}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                          <div className="text-xs text-gray-500 ml-2">
                            {formatTimestamp(alert.timestamp)}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Escalation Notifications */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2 text-orange-500" />
                  Escalation Notifications
                  {escalationNotifications.length > 0 && (
                    <Badge variant="secondary" className="ml-2">
                      {escalationNotifications.length}
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {escalationNotifications.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                      <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                      <p>No escalations required</p>
                    </div>
                  ) : (
                    escalationNotifications.map((escalation, index) => (
                      <div
                        key={escalation.escalation_id || index}
                        className={`p-3 rounded-lg border-l-4 ${
                          escalation.escalation_level === 'emergency_response' ? 'border-red-500 bg-red-50' :
                          escalation.escalation_level === 'constitutional_council' ? 'border-orange-500 bg-orange-50' :
                          escalation.escalation_level === 'policy_manager' ? 'border-yellow-500 bg-yellow-50' :
                          'border-blue-500 bg-blue-50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <h4 className="font-medium text-sm">
                                Escalated to {escalation.escalation_level?.replace('_', ' ')}
                              </h4>
                              <Badge variant="outline" className={`text-xs ${
                                escalation.escalation_level === 'emergency_response' ? 'border-red-500 text-red-700' :
                                escalation.escalation_level === 'constitutional_council' ? 'border-orange-500 text-orange-700' :
                                'border-yellow-500 text-yellow-700'
                              }`}>
                                {escalation.escalation_level}
                              </Badge>
                            </div>
                            <div className="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                              <span>Violation: {escalation.violation_id}</span>
                              {escalation.assigned_to && (
                                <span>Assigned: {escalation.assigned_to}</span>
                              )}
                              <span>Target: {escalation.response_time_target}min</span>
                            </div>
                            <div className="flex items-center space-x-2 mt-2">
                              {escalation.notification_sent ? (
                                <div className="flex items-center text-xs text-green-600">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Notification sent
                                </div>
                              ) : (
                                <div className="flex items-center text-xs text-red-600">
                                  <XCircle className="h-3 w-3 mr-1" />
                                  Notification failed
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="text-xs text-gray-500 ml-2">
                            {formatTimestamp(escalation.timestamp)}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Alerts Tab */}
        <TabsContent value="alerts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Constitutional Fidelity Alerts</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {alerts.map((alert, index) => (
                  <Alert key={index} className={getAlertSeverityColor(alert.severity)}>
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{alert.message}</p>
                          <p className="text-sm text-gray-600 mt-1">
                            Score: {formatScore(alert.fidelity_score)} | 
                            Violations: {alert.violations} | 
                            {new Date(alert.timestamp).toLocaleString()}
                          </p>
                        </div>
                        <Badge variant="outline" className={`ml-2 ${
                          alert.severity === 'red' ? 'border-red-500 text-red-700' :
                          alert.severity === 'amber' ? 'border-yellow-500 text-yellow-700' :
                          'border-green-500 text-green-700'
                        }`}>
                          {alert.severity.toUpperCase()}
                        </Badge>
                      </div>
                    </AlertDescription>
                  </Alert>
                ))}
                {alerts.length === 0 && (
                  <p className="text-gray-500 text-center py-4">No alerts</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(performanceMetrics).map(([modelName, metrics]) => {
                  if (modelName === 'overall') return null;
                  
                  return (
                    <div key={modelName} className="p-4 border rounded-lg">
                      <div className="flex justify-between items-center mb-2">
                        <h4 className="font-medium">{modelName}</h4>
                        <Badge className={metrics.circuit_breaker_open ? 'bg-red-500' : 'bg-green-500'}>
                          {metrics.circuit_breaker_open ? 'Circuit Open' : 'Healthy'}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-gray-500">Success Rate</p>
                          <p className="font-medium">{formatScore(metrics.success_rate)}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Total Requests</p>
                          <p className="font-medium">{metrics.total_requests}</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Avg Response Time</p>
                          <p className="font-medium">{metrics.average_response_time?.toFixed(2)}s</p>
                        </div>
                        <div>
                          <p className="text-gray-500">Quality Score</p>
                          <p className="font-medium">{formatScore(metrics.average_quality_score || 0)}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ConstitutionalFidelityMonitor;
