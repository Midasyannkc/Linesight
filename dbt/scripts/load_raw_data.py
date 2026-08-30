"""
Loads the Databricks gold-layer Parquet (fct_machine_daily_oee) plus
the SPC CSV outputs into DuckDB under a raw schema, representing what
Delta Sharing or a scheduled sync job would land in Snowflake. This is
the actual Databricks-to-Snowflake bridge this project's architecture
is built around.

Run: python load_raw_data.py
"""
import duckdb

DB_PATH = "../linesight.duckdb"


def main():
    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    con.execute("""
        CREATE OR REPLACE TABLE raw.fct_machine_daily_oee AS
        SELECT * FROM parquet_scan('../../data/warehouse/gold/fct_machine_daily_oee/*.parquet')
    """)
    count = con.execute("SELECT COUNT(*) FROM raw.fct_machine_daily_oee").fetchone()[0]
    print(f"raw.fct_machine_daily_oee (synced from Databricks): {count} rows")

    con.execute("CREATE OR REPLACE TABLE raw.spc_control_chart_data AS SELECT * FROM read_csv_auto('../../data/spc_control_chart_data.csv')")
    con.execute("CREATE OR REPLACE TABLE raw.process_capability AS SELECT * FROM read_csv_auto('../../data/process_capability.csv')")
    con.execute("CREATE OR REPLACE TABLE raw.downtime_events AS SELECT * FROM read_csv_auto('../../data/downtime_events.csv')")

    for t in ["spc_control_chart_data", "process_capability", "downtime_events"]:
        count = con.execute(f"SELECT COUNT(*) FROM raw.{t}").fetchone()[0]
        print(f"raw.{t}: {count} rows")

    con.close()


if __name__ == "__main__":
    main()
