-- BenchPilot AI: PostgreSQL-oriented examples for validation engineering.
-- These mirror the access patterns supported by the SQLAlchemy indexes.

-- 1) Signals with the most specification failures in the last 7 days.
SELECT
    signal,
    test_name,
    COUNT(*) AS measurements,
    COUNT(*) FILTER (WHERE computed_status = 'FAIL') AS failures,
    ROUND(100.0 * COUNT(*) FILTER (WHERE computed_status = 'FAIL') / COUNT(*), 2) AS failure_pct
FROM test_runs
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY signal, test_name
HAVING COUNT(*) FILTER (WHERE computed_status = 'FAIL') > 0
ORDER BY failures DESC, failure_pct DESC;

-- 2) Potentially flaky tests: both pass and fail outcomes in the same period.
SELECT
    test_name,
    signal,
    COUNT(*) AS runs,
    COUNT(*) FILTER (WHERE computed_status = 'PASS') AS passes,
    COUNT(*) FILTER (WHERE computed_status = 'FAIL') AS failures
FROM test_runs
WHERE timestamp >= NOW() - INTERVAL '30 days'
GROUP BY test_name, signal
HAVING COUNT(*) FILTER (WHERE computed_status = 'PASS') > 0
   AND COUNT(*) FILTER (WHERE computed_status = 'FAIL') > 0
ORDER BY failures DESC;

-- 3) Inspect the query plan for a common signal-history lookup.
EXPLAIN (ANALYZE, BUFFERS)
SELECT timestamp, value, temperature_c, supply_v, computed_status, anomaly_score
FROM test_runs
WHERE test_name = 'adc_reference'
  AND signal = 'vref'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp;
