-- LineSight's hybrid architecture: Databricks handles streaming
-- ingestion, the medallion transformation, and the predictive
-- maintenance model. This DDL is the Snowflake side of the bridge,
-- the governed layer analysts and shop-floor dashboards actually
-- query, synced from Databricks gold tables.
--
-- In production, the sync itself runs one of two ways:
--   1. Delta Sharing: Snowflake reads Databricks Delta tables directly
--      via the open Delta Sharing protocol, no data movement required.
--   2. A scheduled job (Fivetran, or a Databricks-to-Snowflake COPY
--      via an external stage) lands the gold Parquet on a schedule.
-- This repo's local verification (dbt/, run against DuckDB) represents
-- the Snowflake side; the upstream gold tables are the real PySpark
-- output in databricks_jobs/.

CREATE TABLE gold.fct_machine_daily_oee (
    machine_id        VARCHAR(8) NOT NULL,
    line_id           VARCHAR(8) NOT NULL,
    production_date   DATE NOT NULL,
    units_measured    INTEGER NOT NULL,
    units_in_spec     INTEGER NOT NULL,
    quality_rate      NUMERIC(6,4) NOT NULL,
    downtime_hours    NUMERIC(6,2) NOT NULL,
    planned_hours     NUMERIC(6,2) NOT NULL,
    availability      NUMERIC(6,4) NOT NULL,
    PRIMARY KEY (machine_id, production_date)
);

CREATE TABLE gold.spc_control_chart_data (
    line_id             VARCHAR(8) NOT NULL,
    subgroup_start_ts   TIMESTAMP NOT NULL,
    xbar                NUMERIC(8,4) NOT NULL,
    range_val           NUMERIC(8,4) NOT NULL,
    ucl_xbar            NUMERIC(8,4) NOT NULL,
    lcl_xbar            NUMERIC(8,4) NOT NULL,
    centerline_xbar     NUMERIC(8,4) NOT NULL,
    out_of_control      BOOLEAN NOT NULL
);

CREATE TABLE gold.process_capability (
    line_id                    VARCHAR(8) PRIMARY KEY,
    n_subgroups                INTEGER NOT NULL,
    cpk                         NUMERIC(6,3) NOT NULL,
    out_of_control_subgroups    INTEGER NOT NULL,
    out_of_control_pct          NUMERIC(6,4) NOT NULL
);

-- KPI view a Snowflake-native dashboard (or Grafana over Snowflake)
-- connects to directly: OEE = availability x performance x quality.
-- Performance ratio assumed 1.0 (no throughput-vs-target data in this
-- synthetic set); a real deployment would join a target-rate table.
CREATE OR REPLACE VIEW gold.vw_line_oee_summary AS
SELECT
    line_id,
    production_date,
    ROUND(AVG(availability), 4) AS availability,
    ROUND(AVG(quality_rate), 4) AS quality_rate,
    1.0 AS performance_assumed,
    ROUND(AVG(availability) * AVG(quality_rate) * 1.0, 4) AS oee
FROM gold.fct_machine_daily_oee
GROUP BY line_id, production_date;
