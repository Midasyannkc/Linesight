"""
The actual Six Sigma / SPC methodology: X-bar and R control charts
(subgroup means and ranges plotted against calculated control limits,
not arbitrary thresholds), plus Cpk process capability. Real
control-chart math against real measurement data, not a classifier.

Run: python spc_control_charts.py
Reads:  ../data/quality_measurements.csv
Writes: ../data/spc_control_chart_data.csv, ../data/process_capability.csv
"""
import csv
import statistics

TARGET = 50.00
USL = TARGET + 0.30
LSL = TARGET - 0.30
SUBGROUP_SIZE = 5

A2 = 0.577
D3 = 0.0
D4 = 2.114
D2 = 2.326


def load_measurements():
    with open("../data/quality_measurements.csv", newline="") as f:
        return list(csv.DictReader(f))


def build_subgroups(measurements, line_id):
    line_measurements = [m for m in measurements if m["line_id"] == line_id]
    line_measurements.sort(key=lambda m: m["measured_ts"])

    subgroups = []
    for i in range(0, len(line_measurements) - SUBGROUP_SIZE + 1, SUBGROUP_SIZE):
        chunk = line_measurements[i:i + SUBGROUP_SIZE]
        values = [float(m["part_dimension_mm"]) for m in chunk]
        subgroups.append({
            "line_id": line_id,
            "subgroup_start_ts": chunk[0]["measured_ts"],
            "xbar": statistics.mean(values),
            "range": max(values) - min(values),
        })
    return subgroups


def compute_control_limits(subgroups):
    xbars = [s["xbar"] for s in subgroups]
    ranges = [s["range"] for s in subgroups]

    xbar_bar = statistics.mean(xbars)
    r_bar = statistics.mean(ranges)

    return {
        "xbar_bar": xbar_bar, "r_bar": r_bar,
        "ucl_xbar": xbar_bar + A2 * r_bar, "lcl_xbar": xbar_bar - A2 * r_bar,
        "ucl_r": D4 * r_bar, "lcl_r": D3 * r_bar,
    }


def compute_capability(xbar_bar, r_bar):
    sigma_hat = r_bar / D2
    cpu = (USL - xbar_bar) / (3 * sigma_hat)
    cpl = (xbar_bar - LSL) / (3 * sigma_hat)
    cpk = min(cpu, cpl)
    return {"sigma_hat": sigma_hat, "cpu": cpu, "cpl": cpl, "cpk": cpk}


def main():
    measurements = load_measurements()
    lines = sorted(set(m["line_id"] for m in measurements))

    chart_rows = []
    capability_rows = []

    for line_id in lines:
        subgroups = build_subgroups(measurements, line_id)
        limits = compute_control_limits(subgroups)
        capability = compute_capability(limits["xbar_bar"], limits["r_bar"])

        out_of_control_count = sum(
            1 for s in subgroups
            if s["xbar"] > limits["ucl_xbar"] or s["xbar"] < limits["lcl_xbar"]
        )

        for s in subgroups:
            chart_rows.append({
                "line_id": line_id,
                "subgroup_start_ts": s["subgroup_start_ts"],
                "xbar": round(s["xbar"], 4),
                "range": round(s["range"], 4),
                "ucl_xbar": round(limits["ucl_xbar"], 4),
                "lcl_xbar": round(limits["lcl_xbar"], 4),
                "centerline_xbar": round(limits["xbar_bar"], 4),
                "out_of_control": int(s["xbar"] > limits["ucl_xbar"] or s["xbar"] < limits["lcl_xbar"]),
            })

        capability_rows.append({
            "line_id": line_id,
            "n_subgroups": len(subgroups),
            "xbar_bar": round(limits["xbar_bar"], 4),
            "r_bar": round(limits["r_bar"], 4),
            "sigma_hat": round(capability["sigma_hat"], 4),
            "cpk": round(capability["cpk"], 3),
            "out_of_control_subgroups": out_of_control_count,
            "out_of_control_pct": round(out_of_control_count / len(subgroups), 4),
        })

    with open("../data/spc_control_chart_data.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(chart_rows[0].keys()))
        writer.writeheader()
        writer.writerows(chart_rows)

    with open("../data/process_capability.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(capability_rows[0].keys()))
        writer.writeheader()
        writer.writerows(capability_rows)

    print("Process capability by line:")
    for r in capability_rows:
        print(f"  {r['line_id']}: Cpk={r['cpk']}, out-of-control subgroups={r['out_of_control_subgroups']}/{r['n_subgroups']} ({r['out_of_control_pct']*100:.1f}%)")


if __name__ == "__main__":
    main()
