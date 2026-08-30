import csv
import matplotlib.pyplot as plt
import duckdb

plt.rcParams["font.size"] = 11

con = duckdb.connect("../dbt/linesight.duckdb")

with open("../data/spc_control_chart_data.csv", newline="") as f:
    spc_rows = list(csv.DictReader(f))

line_a_rows = [r for r in spc_rows if r["line_id"] == "LINE-A"][:80]
fig, ax = plt.subplots(figsize=(10, 5.5))
xs = list(range(len(line_a_rows)))
xbars = [float(r["xbar"]) for r in line_a_rows]
ucl = float(line_a_rows[0]["ucl_xbar"])
lcl = float(line_a_rows[0]["lcl_xbar"])
centerline = float(line_a_rows[0]["centerline_xbar"])
colors = ["#8B3A3A" if int(r["out_of_control"]) else "#2B7A6B" for r in line_a_rows]

ax.plot(xs, xbars, color="#5B6472", linewidth=1, zorder=1)
ax.scatter(xs, xbars, c=colors, s=25, zorder=2)
ax.axhline(ucl, color="#8B3A3A", linestyle="--", linewidth=1.2, label=f"UCL ({ucl:.3f}mm)")
ax.axhline(lcl, color="#8B3A3A", linestyle="--", linewidth=1.2, label=f"LCL ({lcl:.3f}mm)")
ax.axhline(centerline, color="#1E2530", linestyle="-", linewidth=1, label=f"Centerline ({centerline:.3f}mm)")
ax.set_xlabel("Subgroup sequence")
ax.set_ylabel("Part dimension (mm)")
ax.set_title("X-bar Control Chart, LINE-A (first 80 subgroups)")
ax.legend(loc="upper right", fontsize=9)
fig.tight_layout()
fig.savefig("xbar_control_chart.png", dpi=150)
plt.close(fig)

cap = con.execute("select * from raw.process_capability order by cpk").df()
fig, ax = plt.subplots(figsize=(7, 5.5))
colors2 = ["#8B3A3A" if c < 1.0 else "#2B7A6B" for c in cap["cpk"]]
bars = ax.bar(cap["line_id"], cap["cpk"], color=colors2)
ax.axhline(1.33, color="gray", linestyle="--", linewidth=1, label="1.33 = generally acceptable capability")
ax.set_ylabel("Cpk")
ax.set_title("Process Capability (Cpk) by Line")
for bar, c in zip(bars, cap["cpk"]):
    ax.text(bar.get_x() + bar.get_width() / 2, c + 0.02, f"{c:.3f}", ha="center", fontsize=10)
ax.legend(loc="upper right")
fig.tight_layout()
fig.savefig("cpk_by_line.png", dpi=150)
plt.close(fig)

pareto = con.execute("select * from main_marts.fct_downtime_pareto order by total_downtime_hours desc").df()
fig, ax1 = plt.subplots(figsize=(8, 5.5))
bars = ax1.bar(pareto["reason"], pareto["total_downtime_hours"], color="#C97A2B")
ax1.set_ylabel("Total downtime (hours)")
plt.setp(ax1.get_xticklabels(), rotation=30, ha="right")
ax2 = ax1.twinx()
cum_pct = pareto["pct_of_total_downtime"].cumsum() * 100
ax2.plot(pareto["reason"], cum_pct, color="#1E2530", marker="o", linewidth=2)
ax2.set_ylabel("Cumulative % of downtime")
ax2.set_ylim(0, 105)
ax1.set_title("Downtime Reason Pareto")
fig.tight_layout()
fig.savefig("downtime_pareto.png", dpi=150)
plt.close(fig)

print("Charts written: xbar_control_chart.png, cpk_by_line.png, downtime_pareto.png")
