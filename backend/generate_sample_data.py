"""
generate_sample_data.py
Generates a realistic synthetic satellite telemetry dataset with injected anomalies.
Run once from the backend/ directory: python generate_sample_data.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

SEED = 42
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
N_ROWS = 600          # total telemetry readings
INTERVAL_SECONDS = 30  # one reading every 30 seconds
START_TIME = datetime(2026, 1, 15, 8, 0, 0)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def orbital_sine(n: int, period: int, amplitude: float, offset: float) -> np.ndarray:
    """Simulate a smooth orbital oscillation."""
    x = np.arange(n)
    return amplitude * np.sin(2 * np.pi * x / period) + offset


def add_noise(arr: np.ndarray, sigma: float) -> np.ndarray:
    return arr + rng.normal(0, sigma, size=len(arr))


# ---------------------------------------------------------------------------
# Base signal generation (realistic orbital patterns)
# ---------------------------------------------------------------------------

timestamps = [START_TIME + timedelta(seconds=i * INTERVAL_SECONDS) for i in range(N_ROWS)]

# Temperature: oscillates with orbital period (~90 min = 180 samples at 30s)
temperature = add_noise(orbital_sine(N_ROWS, 180, 18.0, 22.0), 1.5)

# Radiation: higher on sun-facing side, low noise
radiation = add_noise(orbital_sine(N_ROWS, 180, 1.2, 2.8), 0.15)
radiation = np.clip(radiation, 0.0, None)

# Pressure: very stable with tiny drift downward over time
pressure = add_noise(np.linspace(101.2, 100.8, N_ROWS), 0.08)

# Battery level: charges on sunlit side, discharges on dark side
battery_level = add_noise(orbital_sine(N_ROWS, 180, 12.0, 75.0), 1.0)
battery_level = np.clip(battery_level, 0.0, 100.0)

# Signal strength: degrades on far orbital arc
signal_strength = add_noise(orbital_sine(N_ROWS, 180, 8.0, -72.0), 1.2)

# Velocity: near-circular orbit with tiny eccentricity variation
velocity = add_noise(orbital_sine(N_ROWS, 180, 0.08, 7.66), 0.02)

# Altitude: slight orbital decay with periodic correction burns
altitude_base = np.linspace(408.0, 406.5, N_ROWS)
altitude = add_noise(altitude_base + orbital_sine(N_ROWS, 180, 1.5, 0.0), 0.3)

# ---------------------------------------------------------------------------
# Inject realistic anomalies
# ---------------------------------------------------------------------------

# --- Anomaly 1: Solar flare — sudden radiation spike at row 80 (3 rows)
for i in range(80, 83):
    radiation[i] = rng.uniform(9.5, 12.0)      # Critical: ~4x normal max
    temperature[i] += rng.uniform(8.0, 12.0)   # thermal effect

# --- Anomaly 2: Thermal runaway — sustained high temperature at rows 140-155
for i in range(140, 156):
    temperature[i] = rng.uniform(62.0, 78.0)   # Critical: well above normal max ~45°C

# --- Anomaly 3: Battery drain event at rows 200-215
for i in range(200, 216):
    battery_level[i] = rng.uniform(8.0, 18.0)  # Critical: near depletion

# --- Anomaly 4: Signal loss — weak signal at rows 260-268
for i in range(260, 269):
    signal_strength[i] = rng.uniform(-105.0, -98.0)  # Warning: very weak

# --- Anomaly 5: Pressure drop at rows 310-313
for i in range(310, 314):
    pressure[i] = rng.uniform(85.0, 91.0)      # Critical: hull pressure drop

# --- Anomaly 6: Velocity spike at rows 370-372 (micrometeorite impact?)
for i in range(370, 373):
    velocity[i] = rng.uniform(8.8, 9.4)        # Critical: +16% velocity

# --- Anomaly 7: Altitude drop at rows 420-425 (orbital decay episode)
for i in range(420, 426):
    altitude[i] = rng.uniform(378.0, 388.0)    # Warning: ~25 km below normal

# --- Anomaly 8: Combined sensor anomaly at rows 480-483 (Warning level)
for i in range(480, 484):
    temperature[i] = rng.uniform(48.0, 55.0)   # Warning
    radiation[i] = rng.uniform(5.5, 7.0)       # Warning
    signal_strength[i] = rng.uniform(-92.0, -88.0)  # Warning

# --- Anomaly 9: Single critical temperature spike at row 530
temperature[530] = rng.uniform(85.0, 92.0)     # Critical isolated spike

# --- Anomaly 10: Battery critical single point at row 560
battery_level[560] = rng.uniform(4.0, 7.0)     # Critical isolated point

# ---------------------------------------------------------------------------
# Assemble DataFrame
# ---------------------------------------------------------------------------

df = pd.DataFrame({
    "timestamp": timestamps,
    "temperature": np.round(temperature, 2),
    "radiation": np.round(radiation, 4),
    "pressure": np.round(pressure, 3),
    "battery_level": np.round(battery_level, 2),
    "signal_strength": np.round(signal_strength, 2),
    "velocity": np.round(velocity, 4),
    "altitude": np.round(altitude, 2),
})

# Format timestamp as ISO 8601 string
df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
output_path = "data/sample_satellite.csv"
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} rows → {output_path}")
print(f"Injected anomaly windows:")
print(f"  Rows 80-82   : Solar flare (radiation Critical)")
print(f"  Rows 140-155 : Thermal runaway (temperature Critical)")
print(f"  Rows 200-215 : Battery drain (battery_level Critical)")
print(f"  Rows 260-268 : Signal loss (signal_strength Warning)")
print(f"  Rows 310-313 : Pressure drop (pressure Critical)")
print(f"  Rows 370-372 : Velocity spike (velocity Critical)")
print(f"  Rows 420-425 : Altitude drop (altitude Warning)")
print(f"  Rows 480-483 : Combined sensor anomaly (Warning)")
print(f"  Row  530     : Isolated temperature spike (Critical)")
print(f"  Row  560     : Isolated battery critical (Critical)")
print(f"\nColumn stats:")
print(df.describe().round(3).to_string())
