document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = 'http://localhost:8000/api/v1/reliability'; // Adjust if your backend runs on a different port/host

    const summaryElements = {
        overallReliability: document.getElementById('overall-reliability'),
        reliabilityTrend: document.getElementById('reliability-trend'),
        targetAchievement: document.getElementById('target-achievement'),
        avgSuccessRate: document.getElementById('avg-success-rate'),
        avgConsensusRate: document.getElementById('avg-consensus-rate'),
        avgBiasDetectionRate: document.getElementById('avg-bias-detection-rate'),
        avgSemanticFaithfulness: document.getElementById('avg-semantic-faithfulness'),
        avgResponseTime: document.getElementById('avg-response-time'),
        avgErrorRate: document.getElementById('avg-error-rate'),
        cacheHitRate: document.getElementById('cache-hit-rate')
    };

    let responseTimeChart, successRateChart, errorRateChart, modelFailureChart;

    async function fetchMetricsSummary() {
        try {
            const response = await fetch(`${API_BASE_URL}/reliability_metrics`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            updateSummary(data);
        } catch (error) {
            console.error("Error fetching metrics summary:", error);
            for (const key in summaryElements) {
                summaryElements[key].textContent = 'Error loading data.';
            }
        }
    }

    async function fetchMetricsHistory() {
        try {
            const response = await fetch(`${API_BASE_URL}/reliability_metrics/history`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            renderCharts(data.history);
        } catch (error) {
            console.error("Error fetching metrics history:", error);
            // Optionally, display an error message on charts
        }
    }

    function updateSummary(data) {
        summaryElements.overallReliability.textContent = data.overall_reliability ? data.overall_reliability.toFixed(4) : 'N/A';
        summaryElements.reliabilityTrend.textContent = data.reliability_trend ? `${data.reliability_trend.trend} (Slope: ${data.reliability_trend.slope.toFixed(4)})` : 'N/A';
        summaryElements.targetAchievement.textContent = data.target_achievement ? (data.target_achievement ? 'Achieved ✅' : 'Not Achieved ❌') : 'N/A';
        summaryElements.avgSuccessRate.textContent = data.metrics.avg_success_rate ? data.metrics.avg_success_rate.toFixed(4) : 'N/A';
        summaryElements.avgConsensusRate.textContent = data.metrics.avg_consensus_rate ? data.metrics.avg_consensus_rate.toFixed(4) : 'N/A';
        summaryElements.avgBiasDetectionRate.textContent = data.metrics.avg_bias_detection_rate ? data.metrics.avg_bias_detection_rate.toFixed(4) : 'N/A';
        summaryElements.avgSemanticFaithfulness.textContent = data.metrics.avg_semantic_faithfulness ? data.metrics.avg_semantic_faithfulness.toFixed(4) : 'N/A';
        summaryElements.avgResponseTime.textContent = data.metrics.avg_response_time ? `${data.metrics.avg_response_time.toFixed(4)} s` : 'N/A';
        summaryElements.avgErrorRate.textContent = data.metrics.avg_error_rate ? data.metrics.avg_error_rate.toFixed(4) : 'N/A';
        summaryElements.cacheHitRate.textContent = data.metrics.cache_hit_rate ? data.metrics.cache_hit_rate.toFixed(4) : 'N/A';
    }

    function renderCharts(history) {
        const timestamps = history.map(item => new Date(item.timestamp).toLocaleTimeString());
        const responseTimes = history.map(item => item.average_response_time);
        const successRates = history.map(item => item.success_rate);
        const errorRates = history.map(item => item.error_rate);

        // Aggregate model failure counts
        const modelFailureCounts = {};
        history.forEach(item => {
            if (item.model_failures_total) { // Check if model_failures_total exists
                for (const modelName in item.model_failures_total) {
                    if (item.model_failures_total.hasOwnProperty(modelName)) {
                        modelFailureCounts[modelName] = (modelFailureCounts[modelName] || 0) + item.model_failures_total[modelName];
                    }
                }
            }
        });
        const modelNames = Object.keys(modelFailureCounts);
        const failureCounts = Object.values(modelFailureCounts);

        // Destroy existing charts if they exist
        if (responseTimeChart) responseTimeChart.destroy();
        if (successRateChart) successRateChart.destroy();
        if (errorRateChart) errorRateChart.destroy();
        if (modelFailureChart) modelFailureChart.destroy();

        // Response Time Chart
        const ctxResponseTime = document.getElementById('responseTimeChart').getContext('2d');
        responseTimeChart = new Chart(ctxResponseTime, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Average Response Time (s)',
                    data: responseTimes,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Success Rate Chart
        const ctxSuccessRate = document.getElementById('successRateChart').getContext('2d');
        successRateChart = new Chart(ctxSuccessRate, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Success Rate',
                    data: successRates,
                    borderColor: 'rgb(153, 102, 255)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });

        // Error Rate Chart
        const ctxErrorRate = document.getElementById('errorRateChart').getContext('2d');
        errorRateChart = new Chart(ctxErrorRate, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [{
                    label: 'Error Rate',
                    data: errorRates,
                    borderColor: 'rgb(255, 99, 132)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1
                    }
                }
            }
        });

        // Model Failure Chart (Bar Chart)
        const ctxModelFailure = document.getElementById('modelFailureChart').getContext('2d');
        modelFailureChart = new Chart(ctxModelFailure, {
            type: 'bar',
            data: {
                labels: modelNames,
                datasets: [{
                    label: 'Total Model Failures',
                    data: failureCounts,
                    backgroundColor: [
                        'rgba(255, 159, 64, 0.6)',
                        'rgba(54, 162, 235, 0.6)',
                        'rgba(255, 206, 86, 0.6)',
                        'rgba(75, 192, 192, 0.6)',
                        'rgba(153, 102, 255, 0.6)'
                    ],
                    borderColor: [
                        'rgba(255, 159, 64, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        precision: 0
                    }
                }
            }
        });
    }

    // Initial fetch
    fetchMetricsSummary();
    fetchMetricsHistory();

    // Refresh data every 10 seconds
    setInterval(() => {
        fetchMetricsSummary();
        fetchMetricsHistory();
    }, 10000);
});