from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def generate(path: Path, seed: int = 42, runs: int = 80) -> None:
    rng = np.random.default_rng(seed)
    now = datetime.now(timezone.utc) - timedelta(hours=runs)
    definitions = [
        ("adc_reference", "vref", 3.20, 3.40, 3.30, 0.025),
        ("pll_lock_time", "lock_ms", 0.0, 8.0, 4.4, 0.65),
        ("spi_high_level", "voh", 2.60, 3.45, 3.12, 0.06),
    ]
    rows = []
    for i in range(runs):
        temp = float(rng.choice([-40, 25, 85, 125], p=[0.1, 0.55, 0.25, 0.10]))
        supply = float(rng.choice([3.0, 3.3, 3.6], p=[0.2, 0.6, 0.2]))
        for test_name, signal, lower, upper, center, noise in definitions:
            drift = 0.0
            if test_name == "adc_reference":
                drift = (temp - 25) * 0.00035 + (supply - 3.3) * 0.05
            elif test_name == "pll_lock_time":
                drift = max(0.0, temp - 85) * 0.025 + (3.3 - supply) * 1.4
            elif test_name == "spi_high_level":
                drift = (supply - 3.3) * 0.7 - max(0.0, temp - 85) * 0.001
            value = center + drift + rng.normal(0, noise)
            # Inject realistic intermittent issues to make the ML/closed-loop path visible.
            if test_name == "pll_lock_time" and i in {17, 31, 58}:
                value += rng.uniform(4.0, 5.5)
            if test_name == "adc_reference" and i in {22, 61}:
                value -= 0.16
            duration = max(0.5, rng.normal(18 if test_name != "pll_lock_time" else 35, 4))
            if i == 45 and test_name == "spi_high_level":
                duration *= 3.5
            rows.append(
                {
                    "run_id": f"R{i:04d}",
                    "timestamp": (now + timedelta(hours=i)).isoformat(),
                    "bench": "hil-bench-a" if i % 2 == 0 else "hil-bench-b",
                    "device": f"dut-{1 + i % 4}",
                    "test_name": test_name,
                    "signal": signal,
                    "value": round(float(value), 6),
                    "lower_bound": lower,
                    "upper_bound": upper,
                    "duration_ms": round(float(duration), 3),
                    "temperature_c": temp,
                    "supply_v": supply,
                }
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f"Wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/demo_measurements.csv")
    parser.add_argument("--runs", type=int, default=80)
    args = parser.parse_args()
    generate(Path(args.output), runs=args.runs)
