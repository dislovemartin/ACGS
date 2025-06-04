-- ACGS-PGP Database Performance Optimization Script
-- Implements strategic indexing for constitutional principles, policy synthesis, and governance operations
-- Targets <200ms API response times and optimizes for high-frequency queries

-- ============================================================================
-- CONSTITUTIONAL PRINCIPLES OPTIMIZATION
-- ============================================================================

-- Primary indexes for constitutional principles
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_principles_category_priority 
ON principles(category, priority_weight DESC) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_principles_scope_jsonb 
ON principles USING GIN(scope) 
WHERE scope IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_principles_keywords_search 
ON principles USING GIN(keywords) 
WHERE keywords IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_principles_updated_recent 
ON principles(updated_at DESC) 
WHERE updated_at > NOW() - INTERVAL '30 days';

-- Constitutional metadata optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_principles_constitutional_metadata 
ON principles USING GIN(constitutional_metadata) 
WHERE constitutional_metadata IS NOT NULL;

-- ============================================================================
-- POLICY SYNTHESIS OPTIMIZATION
-- ============================================================================

-- Policy operations indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policies_status_updated 
ON policies(status, updated_at DESC) 
WHERE status IN ('active', 'pending', 'under_review');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policies_synthesis_type 
ON policies(synthesis_type, created_at DESC) 
WHERE synthesis_type IS NOT NULL;

-- Policy templates optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policy_templates_active 
ON policy_templates(status, name) 
WHERE status = 'active';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policy_templates_parameters 
ON policy_templates USING GIN(parameters_schema) 
WHERE parameters_schema IS NOT NULL;

-- ============================================================================
-- CONSTITUTIONAL COUNCIL OPTIMIZATION
-- ============================================================================

-- AC Amendments indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ac_amendments_status_priority 
ON ac_amendments(status, urgency_level, created_at DESC) 
WHERE status IN ('proposed', 'under_review', 'voting');

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ac_amendments_voting_period 
ON ac_amendments(voting_start_date, voting_end_date) 
WHERE voting_start_date IS NOT NULL;

-- AC Amendment Votes optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ac_amendment_votes_amendment_user 
ON ac_amendment_votes(amendment_id, user_id, vote_timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ac_amendment_votes_recent 
ON ac_amendment_votes(vote_timestamp DESC) 
WHERE vote_timestamp > NOW() - INTERVAL '90 days';

-- AC Amendment Comments optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ac_amendment_comments_amendment_time 
ON ac_amendment_comments(amendment_id, created_at DESC);

-- ============================================================================
-- GOVERNANCE SYNTHESIS OPTIMIZATION
-- ============================================================================

-- Governance rules indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_governance_rules_active_priority 
ON governance_rules(is_active, priority DESC, updated_at DESC) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_governance_rules_category_context 
ON governance_rules(category, context_type) 
WHERE category IS NOT NULL;

-- LLM interactions optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_llm_interactions_recent_success 
ON llm_interactions(created_at DESC, success) 
WHERE created_at > NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_llm_interactions_model_type 
ON llm_interactions(model_name, interaction_type, created_at DESC);

-- ============================================================================
-- FORMAL VERIFICATION OPTIMIZATION
-- ============================================================================

-- Verification results indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verification_results_policy_status 
ON verification_results(policy_id, verification_status, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_verification_results_recent_failed 
ON verification_results(created_at DESC) 
WHERE verification_status = 'failed' AND created_at > NOW() - INTERVAL '24 hours';

-- Bias detection optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_bias_detection_results_recent 
ON bias_detection_results(detection_timestamp DESC, bias_score DESC) 
WHERE detection_timestamp > NOW() - INTERVAL '7 days';

-- ============================================================================
-- CRYPTOGRAPHIC INTEGRITY OPTIMIZATION
-- ============================================================================

-- Audit logs optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_user_action_time 
ON audit_logs(user_id, action, timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_recent_critical 
ON audit_logs(timestamp DESC) 
WHERE severity IN ('high', 'critical') AND timestamp > NOW() - INTERVAL '30 days';

-- PGP signatures optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_pgp_signatures_artifact_valid 
ON pgp_signatures(artifact_type, artifact_id, is_valid) 
WHERE is_valid = true;

-- ============================================================================
-- CROSS-SERVICE COMMUNICATION OPTIMIZATION
-- ============================================================================

-- Service call logs optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_calls_recent_errors 
ON service_call_logs(timestamp DESC) 
WHERE status_code >= 400 AND timestamp > NOW() - INTERVAL '1 hour';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_service_calls_performance 
ON service_call_logs(source_service, target_service, response_time_ms) 
WHERE response_time_ms > 200;

-- ============================================================================
-- USER AND AUTHENTICATION OPTIMIZATION
-- ============================================================================

-- Users optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_active_role 
ON users(is_active, role) 
WHERE is_active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_constitutional_council 
ON users(is_constitutional_council_member, constitutional_council_term_expires) 
WHERE is_constitutional_council_member = true;

-- Sessions optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sessions_active_user 
ON sessions(user_id, is_active, expires_at) 
WHERE is_active = true AND expires_at > NOW();

-- ============================================================================
-- PERFORMANCE MONITORING OPTIMIZATION
-- ============================================================================

-- Environmental factors optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_environmental_factors_recent 
ON environmental_factors(timestamp DESC, factor_type) 
WHERE timestamp > NOW() - INTERVAL '24 hours';

-- QEC enhancements optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_distance_calculations_principle_recent 
ON qec_distance_calculations(principle_id, calculated_at DESC) 
WHERE calculated_at > NOW() - INTERVAL '1 hour';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qec_error_predictions_high_risk 
ON qec_error_predictions(overall_risk_score DESC, prediction_timestamp DESC) 
WHERE overall_risk_score > 0.7;

-- ============================================================================
-- MAINTENANCE AND CLEANUP OPTIMIZATION
-- ============================================================================

-- Partial indexes for common WHERE clauses
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_policies_active_recent 
ON policies(updated_at DESC) 
WHERE status = 'active' AND updated_at > NOW() - INTERVAL '7 days';

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_principles_high_priority 
ON principles(priority_weight DESC, updated_at DESC) 
WHERE priority_weight > 0.8 AND is_active = true;

-- ============================================================================
-- QUERY PERFORMANCE ANALYSIS
-- ============================================================================

-- Enable query statistics collection
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Update table statistics for better query planning
ANALYZE principles;
ANALYZE policies;
ANALYZE policy_templates;
ANALYZE ac_amendments;
ANALYZE ac_amendment_votes;
ANALYZE governance_rules;
ANALYZE verification_results;
ANALYZE audit_logs;
ANALYZE users;

-- ============================================================================
-- CONNECTION POOL OPTIMIZATION SETTINGS
-- ============================================================================

-- These settings should be applied to postgresql.conf
-- Included here for reference

/*
-- Connection and memory settings for ACGS-PGP workload
max_connections = 200
shared_buffers = 512MB
effective_cache_size = 2GB
work_mem = 8MB
maintenance_work_mem = 128MB

-- Checkpoint and WAL settings
checkpoint_completion_target = 0.9
wal_buffers = 32MB
default_statistics_target = 150

-- Query optimization
random_page_cost = 1.1
effective_io_concurrency = 200

-- Logging for performance monitoring
log_min_duration_statement = 200
log_checkpoints = on
log_connections = on
log_disconnections = on
log_lock_waits = on

-- Monitoring
track_activities = on
track_counts = on
track_io_timing = on
track_functions = all
*/
