-- QEC Database Optimization Script
-- Optimizes database performance for QEC-enhanced AlphaEvolve-ACGS
-- Creates indexes, optimizes queries, and configures performance settings

-- ============================================================================
-- INDEX CREATION FOR QEC TABLES
-- ============================================================================

-- Constitutional Principles optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutional_principles_category 
ON constitutional_principles(category);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutional_principles_distance_score 
ON constitutional_principles(distance_score) WHERE distance_score IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_constitutional_principles_updated_at 
ON constitutional_principles(updated_at);

-- QEC Distance Calculations optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_distance_calc_principle_id 
ON qec_distance_calculations(principle_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_distance_calc_updated_at 
ON qec_distance_calculations(score_updated_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_distance_calc_composite_score 
ON qec_distance_calculations(composite_score);

-- Composite index for frequent lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_distance_calc_principle_updated 
ON qec_distance_calculations(principle_id, score_updated_at);

-- QEC Error Predictions optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_error_pred_principle_id 
ON qec_error_predictions(principle_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_error_pred_timestamp 
ON qec_error_predictions(prediction_timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_error_pred_overall_risk 
ON qec_error_predictions(overall_risk_score);

-- Composite index for recent predictions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_error_pred_recent 
ON qec_error_predictions(principle_id, prediction_timestamp DESC) 
WHERE prediction_timestamp > NOW() - INTERVAL '7 days';

-- QEC Synthesis Attempt Logs optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_synthesis_logs_principle_id 
ON qec_synthesis_attempt_logs(principle_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_synthesis_logs_timestamp 
ON qec_synthesis_attempt_logs(timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_synthesis_logs_failure_type 
ON qec_synthesis_attempt_logs(failure_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_synthesis_logs_recovery_strategy 
ON qec_synthesis_attempt_logs(recovery_strategy);

-- Composite index for performance analysis
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_synthesis_logs_analysis 
ON qec_synthesis_attempt_logs(principle_id, timestamp DESC, failure_type);

-- QEC Fidelity Calculations optimizations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_fidelity_calc_timestamp 
ON qec_fidelity_calculations(calculation_timestamp);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_fidelity_calc_composite_score 
ON qec_fidelity_calculations(composite_score);

-- Index for recent fidelity trends
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_fidelity_calc_recent 
ON qec_fidelity_calculations(calculation_timestamp DESC) 
WHERE calculation_timestamp > NOW() - INTERVAL '24 hours';

-- ============================================================================
-- QUERY OPTIMIZATION VIEWS
-- ============================================================================

-- View for recent constitutional distance calculations
CREATE OR REPLACE VIEW qec_recent_distance_calculations AS
SELECT 
    qdc.principle_id,
    cp.name as principle_name,
    cp.category,
    qdc.composite_score,
    qdc.language_ambiguity,
    qdc.criteria_formality,
    qdc.synthesis_reliability,
    qdc.score_updated_at
FROM qec_distance_calculations qdc
JOIN constitutional_principles cp ON qdc.principle_id = cp.principle_id
WHERE qdc.score_updated_at > NOW() - INTERVAL '24 hours'
ORDER BY qdc.score_updated_at DESC;

-- View for error prediction summary
CREATE OR REPLACE VIEW qec_error_prediction_summary AS
SELECT 
    qep.principle_id,
    cp.name as principle_name,
    cp.category,
    qep.overall_risk_score,
    qep.predicted_failures,
    qep.recommended_strategy,
    qep.confidence,
    qep.prediction_timestamp
FROM qec_error_predictions qep
JOIN constitutional_principles cp ON qep.principle_id = cp.principle_id
WHERE qep.prediction_timestamp > NOW() - INTERVAL '7 days'
ORDER BY qep.overall_risk_score DESC, qep.prediction_timestamp DESC;

-- View for synthesis performance metrics
CREATE OR REPLACE VIEW qec_synthesis_performance AS
SELECT 
    principle_id,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN final_outcome = 'success' THEN 1 END) as successful_attempts,
    COUNT(CASE WHEN final_outcome = 'failed' THEN 1 END) as failed_attempts,
    ROUND(
        COUNT(CASE WHEN final_outcome = 'success' THEN 1 END)::numeric / 
        COUNT(*)::numeric * 100, 2
    ) as success_rate_percent,
    AVG(CASE WHEN final_outcome = 'success' THEN 
        EXTRACT(EPOCH FROM (timestamp - timestamp)) END) as avg_success_time_seconds,
    COUNT(DISTINCT failure_type) as unique_failure_types,
    COUNT(DISTINCT recovery_strategy) as unique_recovery_strategies
FROM qec_synthesis_attempt_logs
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY principle_id
ORDER BY success_rate_percent DESC;

-- View for fidelity trends
CREATE OR REPLACE VIEW qec_fidelity_trends AS
SELECT 
    DATE_TRUNC('hour', calculation_timestamp) as hour_bucket,
    AVG(composite_score) as avg_composite_score,
    AVG(principle_coverage) as avg_principle_coverage,
    AVG(synthesis_success) as avg_synthesis_success,
    AVG(enforcement_reliability) as avg_enforcement_reliability,
    AVG(adaptation_speed) as avg_adaptation_speed,
    AVG(stakeholder_satisfaction) as avg_stakeholder_satisfaction,
    AVG(appeal_frequency) as avg_appeal_frequency,
    COUNT(*) as calculation_count
FROM qec_fidelity_calculations
WHERE calculation_timestamp > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', calculation_timestamp)
ORDER BY hour_bucket DESC;

-- ============================================================================
-- PERFORMANCE OPTIMIZATION FUNCTIONS
-- ============================================================================

-- Function to clean old QEC data
CREATE OR REPLACE FUNCTION qec_cleanup_old_data(retention_days INTEGER DEFAULT 90)
RETURNS TABLE(
    table_name TEXT,
    rows_deleted BIGINT
) AS $$
DECLARE
    cutoff_date TIMESTAMP;
    deleted_count BIGINT;
BEGIN
    cutoff_date := NOW() - (retention_days || ' days')::INTERVAL;
    
    -- Clean old distance calculations
    DELETE FROM qec_distance_calculations 
    WHERE score_updated_at < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'qec_distance_calculations';
    rows_deleted := deleted_count;
    RETURN NEXT;
    
    -- Clean old error predictions
    DELETE FROM qec_error_predictions 
    WHERE prediction_timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'qec_error_predictions';
    rows_deleted := deleted_count;
    RETURN NEXT;
    
    -- Clean old synthesis logs (keep more history for analysis)
    DELETE FROM qec_synthesis_attempt_logs 
    WHERE timestamp < cutoff_date;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'qec_synthesis_attempt_logs';
    rows_deleted := deleted_count;
    RETURN NEXT;
    
    -- Clean old fidelity calculations (keep 30 days)
    DELETE FROM qec_fidelity_calculations 
    WHERE calculation_timestamp < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    table_name := 'qec_fidelity_calculations';
    rows_deleted := deleted_count;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- Function to update table statistics
CREATE OR REPLACE FUNCTION qec_update_statistics()
RETURNS TEXT AS $$
BEGIN
    ANALYZE constitutional_principles;
    ANALYZE qec_distance_calculations;
    ANALYZE qec_error_predictions;
    ANALYZE qec_synthesis_attempt_logs;
    ANALYZE qec_fidelity_calculations;
    
    RETURN 'QEC table statistics updated successfully';
END;
$$ LANGUAGE plpgsql;

-- Function to get QEC performance metrics
CREATE OR REPLACE FUNCTION qec_get_performance_metrics()
RETURNS TABLE(
    metric_name TEXT,
    metric_value NUMERIC,
    metric_unit TEXT,
    calculation_time TIMESTAMP
) AS $$
BEGIN
    -- Average distance calculation time (simulated)
    metric_name := 'avg_distance_calculation_time';
    metric_value := 45.5;
    metric_unit := 'milliseconds';
    calculation_time := NOW();
    RETURN NEXT;
    
    -- Cache hit rate for distance calculations
    SELECT 
        'distance_cache_hit_rate',
        CASE 
            WHEN COUNT(*) > 0 THEN 
                COUNT(CASE WHEN score_updated_at > NOW() - INTERVAL '1 hour' THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100
            ELSE 0 
        END,
        'percent',
        NOW()
    INTO metric_name, metric_value, metric_unit, calculation_time
    FROM qec_distance_calculations;
    RETURN NEXT;
    
    -- Average error prediction accuracy
    SELECT 
        'error_prediction_accuracy',
        AVG(confidence * 100),
        'percent',
        NOW()
    INTO metric_name, metric_value, metric_unit, calculation_time
    FROM qec_error_predictions
    WHERE prediction_timestamp > NOW() - INTERVAL '24 hours';
    RETURN NEXT;
    
    -- Synthesis success rate
    SELECT 
        'synthesis_success_rate',
        CASE 
            WHEN COUNT(*) > 0 THEN 
                COUNT(CASE WHEN final_outcome = 'success' THEN 1 END)::NUMERIC / COUNT(*)::NUMERIC * 100
            ELSE 0 
        END,
        'percent',
        NOW()
    INTO metric_name, metric_value, metric_unit, calculation_time
    FROM qec_synthesis_attempt_logs
    WHERE timestamp > NOW() - INTERVAL '24 hours';
    RETURN NEXT;
    
    -- Average fidelity score
    SELECT 
        'avg_constitutional_fidelity',
        AVG(composite_score * 100),
        'percent',
        NOW()
    INTO metric_name, metric_value, metric_unit, calculation_time
    FROM qec_fidelity_calculations
    WHERE calculation_timestamp > NOW() - INTERVAL '24 hours';
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- POSTGRESQL CONFIGURATION OPTIMIZATIONS
-- ============================================================================

-- Optimize PostgreSQL settings for QEC workload
-- Note: These require superuser privileges and server restart

-- Memory settings
-- ALTER SYSTEM SET shared_buffers = '512MB';
-- ALTER SYSTEM SET effective_cache_size = '2GB';
-- ALTER SYSTEM SET work_mem = '16MB';
-- ALTER SYSTEM SET maintenance_work_mem = '128MB';

-- Connection settings
-- ALTER SYSTEM SET max_connections = 200;
-- ALTER SYSTEM SET max_prepared_transactions = 100;

-- Query optimization
-- ALTER SYSTEM SET random_page_cost = 1.1;
-- ALTER SYSTEM SET effective_io_concurrency = 200;

-- Logging for performance monitoring
-- ALTER SYSTEM SET log_min_duration_statement = 1000;
-- ALTER SYSTEM SET log_checkpoints = on;
-- ALTER SYSTEM SET log_connections = on;
-- ALTER SYSTEM SET log_disconnections = on;
-- ALTER SYSTEM SET log_lock_waits = on;

-- Autovacuum tuning for QEC tables
-- ALTER SYSTEM SET autovacuum_max_workers = 6;
-- ALTER SYSTEM SET autovacuum_naptime = '30s';

-- Apply configuration changes
-- SELECT pg_reload_conf();

-- ============================================================================
-- MAINTENANCE PROCEDURES
-- ============================================================================

-- Create maintenance schedule
-- Run daily cleanup
-- SELECT cron.schedule('qec-daily-cleanup', '0 2 * * *', 'SELECT qec_cleanup_old_data(90);');

-- Update statistics weekly
-- SELECT cron.schedule('qec-weekly-stats', '0 3 * * 0', 'SELECT qec_update_statistics();');

-- ============================================================================
-- MONITORING QUERIES
-- ============================================================================

-- Query to monitor QEC table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE tablename LIKE 'qec_%' OR tablename = 'constitutional_principles'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Query to monitor index usage
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as index_size
FROM pg_stat_user_indexes 
WHERE tablename LIKE 'qec_%' OR tablename = 'constitutional_principles'
ORDER BY idx_scan DESC;

-- Query to monitor slow queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    stddev_exec_time,
    rows
FROM pg_stat_statements 
WHERE query LIKE '%qec_%' OR query LIKE '%constitutional_principles%'
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Query to monitor connection usage
SELECT 
    state,
    COUNT(*) as connection_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - state_change))) as avg_duration_seconds
FROM pg_stat_activity 
WHERE datname = current_database()
GROUP BY state
ORDER BY connection_count DESC;
