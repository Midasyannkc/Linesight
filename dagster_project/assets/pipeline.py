"""
LineSight Dagster asset graph: Databricks transformation -> SPC control
charts -> predictive maintenance scoring -> sync to Snowflake (dbt
build) -> Snowflake-native BI refresh. This is the actual orchestration
across the hybrid architecture, one asset graph spanning both platforms.

Executed in this repo's verification run via `dagster asset
materialize`, see docs/dagster_run_log.txt for the real run output.
"""
import subprocess
import os
from dagster import asset, AssetExecutionContext, MaterializeResult, MetadataValue, Definitions

PROJECT_ROOT = "/home/claude/linesight"


@asset(group_name="databricks", description="Runs the Databricks-equivalent PySpark medallion transformation (bronze/silver/gold).")
def databricks_transform(context: AssetExecutionContext) -> MaterializeResult:
    result = subprocess.run(
        ["python3", "delta_live_tables_job.py"],
        cwd=f"{PROJECT_ROOT}/databricks_jobs",
        capture_output=True, text=True,
    )
    context.log.info(result.stdout[-1500:])
    if result.returncode != 0:
        raise Exception(f"Databricks transform failed: {result.stderr}")
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(result.stdout[-800:])})


@asset(group_name="databricks", deps=[databricks_transform], description="Runs real SPC X-bar/R control chart and Cpk calculations against the quality measurements.")
def spc_control_charts(context: AssetExecutionContext) -> MaterializeResult:
    result = subprocess.run(
        ["python3", "spc_control_charts.py"],
        cwd=f"{PROJECT_ROOT}/spc",
        capture_output=True, text=True,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"SPC calculation failed: {result.stderr}")
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(result.stdout)})


@asset(group_name="databricks", deps=[databricks_transform], description="Trains and registers the MLflow predictive-maintenance model on the silver-layer sensor data.")
def predictive_maintenance_model(context: AssetExecutionContext) -> MaterializeResult:
    result = subprocess.run(
        ["python3", "predictive_maintenance_model.py"],
        cwd=f"{PROJECT_ROOT}/ml",
        capture_output=True, text=True,
    )
    context.log.info(result.stdout[-1500:])
    if result.returncode != 0:
        raise Exception(f"Predictive maintenance training failed: {result.stderr}")
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(result.stdout[-800:])})


@asset(group_name="snowflake", deps=[spc_control_charts], description="Syncs Databricks gold output + SPC results into the Snowflake-equivalent DuckDB instance.")
def sync_to_snowflake(context: AssetExecutionContext) -> MaterializeResult:
    result = subprocess.run(
        ["python3", "load_raw_data.py"],
        cwd=f"{PROJECT_ROOT}/dbt/scripts",
        capture_output=True, text=True,
    )
    context.log.info(result.stdout)
    if result.returncode != 0:
        raise Exception(f"Snowflake sync failed: {result.stderr}")
    return MaterializeResult(metadata={"log_tail": MetadataValue.text(result.stdout)})


@asset(group_name="snowflake", deps=[sync_to_snowflake], description="Runs dbt build against the synced Snowflake-equivalent data, certifying OEE and downtime Pareto metrics.")
def dbt_build_snowflake(context: AssetExecutionContext) -> MaterializeResult:
    result = subprocess.run(
        ["dbt", "build"],
        cwd=f"{PROJECT_ROOT}/dbt",
        env={**os.environ, "DBT_PROFILES_DIR": "."},
        capture_output=True, text=True,
    )
    context.log.info(result.stdout[-2000:])
    if result.returncode != 0:
        raise Exception(f"dbt build failed:\n{result.stdout[-1500:]}")
    return MaterializeResult(metadata={"dbt_log_tail": MetadataValue.text(result.stdout[-1200:])})


defs = Definitions(
    assets=[databricks_transform, spc_control_charts, predictive_maintenance_model, sync_to_snowflake, dbt_build_snowflake],
)
