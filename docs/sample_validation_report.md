# BenchPilot Validation Report

Generated: `2026-08-29T01:46:21.747372+00:00`

## Executive summary
- Measurements: **240**
- Pass rate: **97.9%**
- Failures: **5**
- ML anomalies: **12**
- Generated test cases: **22**

## Recommendations
- Prioritize boundary and environmental regressions for signals with repeated range failures.
- Re-run ML-flagged measurements with controlled temperature and supply voltage to separate DUT faults from bench noise.

## Highest-priority test cases
### P100 — PLL lock time — environmental corner 1
Validate the requirement under the specified operating context (temperature=-40 °C, supply=3 V).

1. Condition the setup to temperature=-40 °C, supply=3 V.
1. Wait for stabilization and record the condition.
1. Repeat nominal and boundary checks for lock_ms.
Expected: lock_ms remains between 0 and 8 ms at temperature=-40 °C, supply=3 V.

### P100 — PLL lock time — environmental corner 2
Validate the requirement under the specified operating context (temperature=125 °C, supply=3 V).

1. Condition the setup to temperature=125 °C, supply=3 V.
1. Wait for stabilization and record the condition.
1. Repeat nominal and boundary checks for lock_ms.
Expected: lock_ms remains between 0 and 8 ms at temperature=125 °C, supply=3 V.

### P100 — PLL lock time — fault injection 1
Exercise diagnostic coverage for the declared fault: interrupted reference clock for 2 ms.

1. Inject or simulate fault: interrupted reference clock for 2 ms.
1. Capture DUT response, timing, and recovery behavior.
1. Remove the fault and verify the system returns to the baseline state.
Expected: The fault is detected or safely contained, with deterministic recovery and traceable evidence.

### P100 — PLL lock time — lower specification boundary
Boundary-value testing finds quantization, calibration, and comparator errors that nominal tests miss.

1. Sweep lock_ms toward the lower limit from inside the valid range.
1. Hold at 0.16 ms, then at 0 ms.
1. Repeat across three independent runs.
Expected: Values at or above 0 ms pass; measurement uncertainty is recorded.

### P100 — PLL lock time — nominal operating point
Establish a clean reference result before stressing the requirement.

1. Configure the DUT and bench for lock_ms measurement.
1. Drive the target near 4 ms.
1. Capture at least 20 repeated samples and timestamps.
Expected: Every stable sample remains between 0 and 8 ms.

### P100 — PLL lock time — out-of-range fault detection
A validation flow should verify that invalid behavior is detected rather than silently accepted.

1. Inject one sample below 0 ms and one above 8 ms using a safe simulator or mocked source.
1. Run the same parser and validation pipeline used for normal data.
1. Confirm failure classification and report traceability.
Expected: Both injected violations are marked FAIL and appear in the generated report.

### P100 — PLL lock time — upper specification boundary
Upper-edge behavior can reveal saturation, thermal drift, or arithmetic overflow.

1. Sweep lock_ms toward the upper limit from inside the valid range.
1. Hold at 7.84 ms, then at 8 ms.
1. Repeat across three independent runs.
Expected: Values at or below 8 ms pass; measurement uncertainty is recorded.

### P95 — ADC reference voltage accuracy — fault injection 1
Exercise diagnostic coverage for the declared fault: simulated reference-divider drift.

1. Inject or simulate fault: simulated reference-divider drift.
1. Capture DUT response, timing, and recovery behavior.
1. Remove the fault and verify the system returns to the baseline state.
Expected: The fault is detected or safely contained, with deterministic recovery and traceable evidence.

### P92 — ADC reference voltage accuracy — out-of-range fault detection
A validation flow should verify that invalid behavior is detected rather than silently accepted.

1. Inject one sample below 3.2 V and one above 3.4 V using a safe simulator or mocked source.
1. Run the same parser and validation pipeline used for normal data.
1. Confirm failure classification and report traceability.
Expected: Both injected violations are marked FAIL and appear in the generated report.

### P90 — ADC reference voltage accuracy — environmental corner 1
Validate the requirement under the specified operating context (temperature=-40 °C, supply=3 V).

1. Condition the setup to temperature=-40 °C, supply=3 V.
1. Wait for stabilization and record the condition.
1. Repeat nominal and boundary checks for vref.
Expected: vref remains between 3.2 and 3.4 V at temperature=-40 °C, supply=3 V.

### P90 — ADC reference voltage accuracy — environmental corner 2
Validate the requirement under the specified operating context (temperature=125 °C, supply=3.6 V).

1. Condition the setup to temperature=125 °C, supply=3.6 V.
1. Wait for stabilization and record the condition.
1. Repeat nominal and boundary checks for vref.
Expected: vref remains between 3.2 and 3.4 V at temperature=125 °C, supply=3.6 V.

### P88 — ADC reference voltage accuracy — lower specification boundary
Boundary-value testing finds quantization, calibration, and comparator errors that nominal tests miss.

1. Sweep vref toward the lower limit from inside the valid range.
1. Hold at 3.204 V, then at 3.2 V.
1. Repeat across three independent runs.
Expected: Values at or above 3.2 V pass; measurement uncertainty is recorded.

## Database maintenance

```json
{
  "dialect": "sqlite",
  "table_counts": {
    "test_runs": 240,
    "test_plans": 22,
    "agent_events": 2
  },
  "duplicate_measurement_groups": 0,
  "missing_indexes": {},
  "oldest_measurement": "2026-08-25T17:45:09.003612",
  "newest_measurement": "2026-08-29T00:45:09.003612",
  "suggestions": [
    "Schema health looks good; keep retention and query-plan checks in the CI/operations loop."
  ]
}
```
