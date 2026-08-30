"""
Synthetic manufacturing telemetry, shaped to mirror what a real
IIoT-monitored production line generates: per-unit quality
measurements (for SPC control charts), sensor readings per machine
(temperature, vibration, pressure, for predictive maintenance), and
downtime events with reason codes (for OEE and Pareto analysis).

Generated with a documented degradation process: each machine has a
latent wear trajectory, sensor readings drift as wear increases, and a
failure event is injected once wear crosses a threshold, so the
predictive-maintenance model downstream has real, physically-motivated
signal to recover, not noise.

No real plant, machine, or production data.

Run: python generate_manufacturing_data.py
Output: machines.csv, quality_measurements.csv, sensor_readings.csv,
        downtime_events.csv, shift_log.csv
"""
import csv
import random
from datetime import datetime, timedelta

random.seed(83)

LINES = ["LINE-A", "LINE-B", "LINE-C", "LINE-D"]
MACHINES_PER_LINE = 3
SHIFTS = ["Day", "Swing", "Night"]

START = datetime(2026, 7, 1)
DAYS_OF_HISTORY = 45
READING_INTERVAL_MINUTES = 10
TARGET_DIMENSION_SPEC = 50.00
SPEC_TOLERANCE = 0.30


def build_machines():
    machines = []
    machine_id = 1
    for line in LINES:
        for _ in range(MACHINES_PER_LINE):
            machines.append({
                "machine_id": f"MCH{machine_id:04d}",
                "line_id": line,
                "machine_type": random.choice(["CNC Mill", "Injection Molder", "Stamping Press"]),
                "install_date": (START - timedelta(days=random.randint(200, 2000))).date().isoformat(),
            })
            machine_id += 1
    return machines


def build_wear_trajectory(n_intervals):
    wear = [0.0]
    failure_intervals = []
    w = 0.0
    increment = random.uniform(0.00025, 0.0009)
    for i in range(1, n_intervals):
        w += increment + random.gauss(0, 0.0003)
        w = max(0, w)
        if w > 1.0:
            failure_intervals.append(i)
            w = random.uniform(0.0, 0.05)
            increment = random.uniform(0.00025, 0.0009)
        wear.append(w)
    return wear, failure_intervals


def main():
    machines = build_machines()
    n_intervals = int(DAYS_OF_HISTORY * 24 * 60 / READING_INTERVAL_MINUTES)

    sensor_readings = []
    quality_measurements = []
    downtime_events = []
    shift_log = []

    for machine in machines:
        wear_trajectory, failure_intervals = build_wear_trajectory(n_intervals)
        failure_set = set(failure_intervals)

        base_temp = random.uniform(58, 68)
        base_vibration = random.uniform(0.8, 1.6)
        base_pressure = random.uniform(95, 115)

        for i in range(n_intervals):
            ts = START + timedelta(minutes=i * READING_INTERVAL_MINUTES)
            wear = wear_trajectory[i]

            temperature = base_temp + wear * 22 + random.gauss(0, 1.2)
            vibration = base_vibration + wear * 3.5 + random.gauss(0, 0.08)
            pressure = base_pressure - wear * 8 + random.gauss(0, 1.5)

            will_fail_soon = int(any(0 <= (fi - i) <= 36 for fi in failure_intervals))

            sensor_readings.append({
                "machine_id": machine["machine_id"],
                "line_id": machine["line_id"],
                "reading_ts": ts.isoformat(),
                "temperature_c": round(temperature, 2),
                "vibration_mm_s": round(vibration, 3),
                "pressure_psi": round(pressure, 2),
                "latent_wear": round(wear, 4),
                "will_fail_within_6h": will_fail_soon,
            })

            if i % 4 == 0:
                dimension = TARGET_DIMENSION_SPEC + wear * 0.6 + random.gauss(0, 0.05)
                quality_measurements.append({
                    "machine_id": machine["machine_id"],
                    "line_id": machine["line_id"],
                    "measured_ts": ts.isoformat(),
                    "part_dimension_mm": round(dimension, 4),
                    "in_spec": int(abs(dimension - TARGET_DIMENSION_SPEC) <= SPEC_TOLERANCE),
                })

            if i in failure_set:
                downtime_hours = round(random.uniform(0.5, 4.0), 2)
                downtime_events.append({
                    "machine_id": machine["machine_id"],
                    "line_id": machine["line_id"],
                    "downtime_start_ts": ts.isoformat(),
                    "downtime_hours": downtime_hours,
                    "reason": random.choice(["Equipment Failure", "Unplanned Maintenance"]),
                })

        for _ in range(random.randint(3, 8)):
            i = random.randint(0, n_intervals - 1)
            ts = START + timedelta(minutes=i * READING_INTERVAL_MINUTES)
            downtime_events.append({
                "machine_id": machine["machine_id"],
                "line_id": machine["line_id"],
                "downtime_start_ts": ts.isoformat(),
                "downtime_hours": round(random.uniform(0.25, 2.0), 2),
                "reason": random.choice(["Changeover", "Material Shortage", "Quality Hold", "Operator Break"]),
            })

    for day in range(DAYS_OF_HISTORY):
        shift_date = (START + timedelta(days=day)).date().isoformat()
        for line in LINES:
            for shift in SHIFTS:
                shift_log.append({
                    "line_id": line,
                    "shift_date": shift_date,
                    "shift": shift,
                    "planned_production_hours": 8.0,
                })

    def write_csv(rows, path):
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(machines, "machines.csv")
    write_csv(sensor_readings, "sensor_readings.csv")
    write_csv(quality_measurements, "quality_measurements.csv")
    write_csv(downtime_events, "downtime_events.csv")
    write_csv(shift_log, "shift_log.csv")

    print(f"machines.csv: {len(machines)} rows")
    print(f"sensor_readings.csv: {len(sensor_readings)} rows")
    print(f"quality_measurements.csv: {len(quality_measurements)} rows")
    print(f"downtime_events.csv: {len(downtime_events)} rows")
    print(f"shift_log.csv: {len(shift_log)} rows")

    fail_rate = sum(r["will_fail_within_6h"] for r in sensor_readings) / len(sensor_readings)
    print(f"Positive rate (will_fail_within_6h): {fail_rate*100:.2f}%")


if __name__ == "__main__":
    main()
