import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Grid,
  Typography,
  Box,
  Alert,
  Chip,
  LinearProgress,
  Badge,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  People as PeopleIcon,
  HowToVote as VoteIcon,
  Timeline as TimelineIcon,
  Dashboard as DashboardIcon
} from '@mui/icons-material';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend
);

const ConstitutionalCouncilDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // WebSocket connection management
  useEffect(() => {
    connectWebSocket();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8001/api/v1/dashboard/ws`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected to Constitutional Council Dashboard');
        setConnectionStatus('connected');
        setError(null);
        
        // Send initial ping
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
        setError('WebSocket connection failed');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to connect to dashboard');
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'pong':
        // Handle ping response
        break;
      case 'amendment_update':
        handleAmendmentUpdate(data);
        break;
      case 'voting_update':
        handleVotingUpdate(data);
        break;
      case 'stakeholder_activity':
        handleStakeholderActivity(data);
        break;
      case 'error':
        setError(data.message);
        break;
      default:
        // Handle full dashboard data
        setDashboardData(data);
        setAlerts(data.alerts?.active_alerts || []);
        setLoading(false);
        break;
    }
  };

  const handleAmendmentUpdate = (data) => {
    console.log('Amendment update:', data);
    // Update specific amendment data
    if (dashboardData) {
      // Trigger a refresh of dashboard data
      requestDashboardData();
    }
  };

  const handleVotingUpdate = (data) => {
    console.log('Voting update:', data);
    // Update voting progress
    if (dashboardData) {
      requestDashboardData();
    }
  };

  const handleStakeholderActivity = (data) => {
    console.log('Stakeholder activity:', data);
    // Update stakeholder engagement metrics
    if (dashboardData) {
      requestDashboardData();
    }
  };

  const requestDashboardData = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'request_data',
        data_type: 'full_dashboard'
      }));
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'success';
      case 'disconnected': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'critical': return <ErrorIcon color="error" />;
      case 'warning': return <WarningIcon color="warning" />;
      default: return <CheckCircleIcon color="info" />;
    }
  };

  const renderAmendmentStatusChart = () => {
    if (!dashboardData?.amendment_workflows?.status_distribution) return null;

    const statusData = dashboardData.amendment_workflows.status_distribution;
    const data = {
      labels: Object.keys(statusData),
      datasets: [{
        data: Object.values(statusData),
        backgroundColor: [
          '#4CAF50', // approved - green
          '#F44336', // rejected - red
          '#FF9800', // under_review - orange
          '#2196F3', // voting - blue
          '#9C27B0', // proposed - purple
        ],
        borderWidth: 2,
      }]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'bottom',
        },
        title: {
          display: true,
          text: 'Amendment Status Distribution'
        }
      }
    };

    return <Doughnut data={data} options={options} />;
  };

  const renderVotingProgressChart = () => {
    if (!dashboardData?.voting_progress?.voting_progress) return null;

    const votingData = dashboardData.voting_progress.voting_progress;
    const labels = votingData.map(vp => `Amendment ${vp.amendment_id}`);
    const approvalRates = votingData.map(vp => vp.approval_rate * 100);

    const data = {
      labels,
      datasets: [{
        label: 'Approval Rate (%)',
        data: approvalRates,
        backgroundColor: approvalRates.map(rate => 
          rate > 50 ? '#4CAF50' : rate < 50 ? '#F44336' : '#FF9800'
        ),
        borderColor: '#1976D2',
        borderWidth: 1,
      }]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: 'Current Voting Progress'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + '%';
            }
          }
        }
      }
    };

    return <Bar data={data} options={options} />;
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <DashboardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Constitutional Council Dashboard
        </Typography>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Connecting to real-time dashboard...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <IconButton onClick={connectWebSocket} color="primary">
          <RefreshIcon />
        </IconButton>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <DashboardIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Constitutional Council Dashboard
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip 
            label={`Connection: ${connectionStatus}`}
            color={getConnectionStatusColor()}
            size="small"
          />
          <Chip 
            label={`${dashboardData?.active_connections || 0} Active Users`}
            color="primary"
            size="small"
            icon={<PeopleIcon />}
          />
          <Tooltip title="Refresh Dashboard">
            <IconButton onClick={requestDashboardData} color="primary">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Alerts */}
      {alerts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          {alerts.slice(0, 3).map((alert, index) => (
            <Alert 
              key={alert.id || index}
              severity={alert.severity}
              icon={getAlertIcon(alert.severity)}
              sx={{ mb: 1 }}
            >
              {alert.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Main Dashboard Grid */}
      <Grid container spacing={3}>
        {/* Amendment Workflow Metrics */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Amendment Workflows"
              avatar={<TimelineIcon color="primary" />}
            />
            <CardContent>
              {renderAmendmentStatusChart()}
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Total Amendments: {dashboardData?.amendment_workflows?.workflow_efficiency?.total_amendments || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Completion Rate: {((dashboardData?.amendment_workflows?.workflow_efficiency?.completion_rate || 0) * 100).toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Voting Progress */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader 
              title="Active Voting"
              avatar={<VoteIcon color="primary" />}
            />
            <CardContent>
              {renderVotingProgressChart()}
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Active Votes: {dashboardData?.voting_progress?.active_votes || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Avg Participation: {((dashboardData?.voting_progress?.overall_participation?.average_participation_rate || 0) * 100).toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Stakeholder Engagement */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Stakeholder Engagement" />
            <CardContent>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="primary">
                  {dashboardData?.stakeholder_engagement?.active_sessions || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Active Sessions
                </Typography>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Comments (24h): {dashboardData?.stakeholder_engagement?.recent_activity?.comments_24h || 0}
                </Typography>
                <Typography variant="body2">
                  Votes (24h): {dashboardData?.stakeholder_engagement?.recent_activity?.votes_24h || 0}
                </Typography>
                <Typography variant="body2">
                  Avg Session: {dashboardData?.stakeholder_engagement?.average_session_duration_minutes || 0} min
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Performance" />
            <CardContent>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="success.main">
                  {dashboardData?.performance_metrics?.workflow_performance?.average_processing_time_hours?.toFixed(1) || 0}h
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Avg Processing Time
                </Typography>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Completed (24h): {dashboardData?.performance_metrics?.workflow_performance?.completed_amendments_24h || 0}
                </Typography>
                <Typography variant="body2">
                  Efficiency: {((dashboardData?.performance_metrics?.workflow_performance?.processing_efficiency || 0) * 100).toFixed(1)}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Health */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="System Health" />
            <CardContent>
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h3" color="info.main">
                  {dashboardData?.alerts?.total_alerts || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Active Alerts
                </Typography>
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2">
                  Critical: {dashboardData?.alerts?.alerts_by_severity?.critical || 0}
                </Typography>
                <Typography variant="body2">
                  Warning: {dashboardData?.alerts?.alerts_by_severity?.warning || 0}
                </Typography>
                <Typography variant="body2">
                  Last Update: {new Date(dashboardData?.timestamp || Date.now()).toLocaleTimeString()}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ConstitutionalCouncilDashboard;
