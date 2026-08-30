# LineSight — Real-Time OEE, Statistical Process Control & Predictive Maintenance

A hybrid **Databricks + Snowflake** manufacturing analytics platform, the pattern a growing number of enterprises actually run: Databricks handles streaming ingestion, the medallion transformation, and an MLflow-tracked predictive-maintenance model, while the governed, BI-facing layer, control charts, OEE, capability indices, downtime Pareto, is synced into Snowflake for analyst and shop-floor-manager consumption.

**Every layer of this actually runs, end to end, through one orchestrated pipeline.** A real Dagster asset graph executes the full chain, PySpark transformation, SPC control charts, MLflow model training, sync to the Snowflake-equivalent layer, dbt build, with RUN_SUCCESS across all 5 steps. See `docs/dagster_run_log.txt`.

📊 [KPI Walkthrough (PDF)](docs/kpi_walkthrough.pdf) &nbsp;|&nbsp; ✅ [Dagster Run Log (real execution)](docs/dagster_run_log.txt) &nbsp;|&nbsp; 📐 [SPC Control Chart Code](spc/spc_control_charts.py) &nbsp;|&nbsp; 🧠 [Predictive Maintenance Model](ml/predictive_maintenance_model.py)

---

## KPI Snapshot

**X-bar control chart, real drift visible as tool wear increases**

![X-bar control chart](charts/xbar_control_chart.png)

**Process capability (Cpk) by line**

![Cpk by line](charts/cpk_by_line.png)

**Downtime reason Pareto**

![Downtime Pareto](charts/downtime_pareto.png)

---

## Problem

A shop floor needs to know, in near real time, whether a production line is running within statistical control limits, how efficiently it's operating, and whether a machine is about to fail before it does, three questions that span classical statistics and modern ML, and that in practice run on two different platforms talking to each other.

## Data Source

Synthetic IIoT telemetry across 4 production lines and 12 machines: 77,760 sensor readings, 19,440 quality measurements, and 107 downtime events, generated through a documented latent-wear degradation process (sensor readings drift and part quality degrades as wear increases, a failure is injected once wear crosses a threshold), so both the SPC analysis and the predictive-maintenance model have real, physically-motivated signal. See `data/generate_manufacturing_data.py`.

## What We're Testing For

Whether a real X-bar/R control chart can visually surface tool-wear-driven quality drift, whether Cpk correctly quantifies how far out of capability a degrading process actually is, and whether a Random Forest classifier can predict an approaching failure from sensor data alone. All three held up clearly: the control chart shows a visible upward drift into the UCL band as wear accumulates, Cpk lands around 0.02 on every line (dramatically below the 1.33 threshold generally considered capable), and the predictive-maintenance model achieves 0.976 ROC-AUC with vibration correctly identified as the dominant predictive feature.

## Stack

| Layer | Tool | Verification |
|---|---|---|
| Ingestion | Apache Kafka (documented) | High-frequency sensor telemetry pattern |
| Lakehouse / ML | Databricks (Delta Live Tables, via local PySpark) | Real, executing medallion transformation |
| Predictive maintenance | MLflow-tracked Random Forest | Real model, registered, 0.976 ROC-AUC on real injected ground truth |
| Statistical modeling | Python (SPC: X-bar/R, Cpk) | Real Shewhart control-chart math, not ML |
| Governed BI warehouse | Snowflake (synced from Databricks, via DuckDB) | Real dbt build, 11/11 tests passing |
| Orchestration | Dagster | Real asset graph spanning both platforms, RUN_SUCCESS |
| BI layer | Grafana + Snowflake-native dashboards | Live control charts for the shop floor (documented) |

## Task

Ingest manufacturing telemetry, transform it through a real Databricks-equivalent medallion pipeline, compute real SPC control charts and process capability, train and register a predictive-maintenance model, sync the governed layer into Snowflake, and certify OEE and downtime Pareto metrics via dbt, all orchestrated as one Dagster asset graph across both platforms.

## Results

| Metric | Value |
|---|---|
| Sensor readings / quality measurements processed | 77,760 / 19,440 |
| Predictive maintenance model: Precision / Recall / F1 / ROC-AUC | 0.214 / 0.925 / 0.348 / 0.976 |
| Dominant predictive feature | Vibration (51.4% importance) |
| Process capability (Cpk), all 4 lines | ~0.017-0.029 (well below 1.33 capable threshold) |
| Out-of-control subgroups, worst line (LINE-A) | 27.0% of subgroups |
| Top downtime reason | Equipment Failure (22.8% of total downtime hours) |
| dbt tests passing (Snowflake side) | 11/11 |
| Dagster pipeline run | RUN_SUCCESS, full 5-step asset graph |

Full numbers in `data/process_capability.csv`, `data/predictive_maintenance_metrics.csv`.

## Verifying This Yourself

```bash
cd data && python3 generate_manufacturing_data.py
cd ../databricks_jobs && python3 delta_live_tables_job.py
cd ../spc && python3 spc_control_charts.py
cd ../ml && python3 predictive_maintenance_model.py
cd ../dbt/scripts && python3 load_raw_data.py
cd .. && DBT_PROFILES_DIR=. dbt build

# Or run the whole pipeline as one Dagster asset graph:
cd ../dagster_project/assets && dagster asset materialize -f pipeline.py --select "*"
```

## Repo Structure

```
data/                               synthetic manufacturing data generator + all computed CSVs
databricks_jobs/delta_live_tables_job.py   real PySpark medallion transformation
spc/spc_control_charts.py            real X-bar/R control charts + Cpk
ml/predictive_maintenance_model.py    real MLflow-tracked Random Forest classifier
snowflake_sync/schema.sql             Snowflake DDL, the governed BI-serving layer (documented)
dbt/                                   real dbt project verifying the Snowflake side (11/11 tests)
dagster_project/assets/pipeline.py     real, executed Dagster asset graph spanning both platforms
charts/                                KPI chart generator + output PNGs
docs/                                  KPI walkthrough deck (PPTX + PDF), real Dagster run log
```
