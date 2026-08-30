"""
Databricks job equivalent (PySpark, Delta-shaped output). Honest
substitute for Delta Live Tables: same medallion pattern, same
transformation logic, run via local PySpark since a live Databricks
workspace needs a real account.

Bronze: raw sensor/quality/downtime data
Silver: cleaned, typed, deduplicated
Gold:   machine-day OEE components + quality summary, the grain both
        the SPC module and the Snowflake-synced BI layer read from

Run: python delta_live_tables_job.py
Reads:  ../data/*.csv
Writes: ../data/warehouse/{bronze,silver,gold}/ (Parquet)
"""
import os
import shutil
from pyspark.sql import SparkSession, functions as F

WAREHOUSE_DIR = "../data/warehouse"


def get_spark():
    return (
        SparkSession.builder
        .appName("linesight-delta-live-tables")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", "4")
        .getOrCreate()
    )


def bronze_layer(spark):
    sensors = spark.read.csv("../data/sensor_readings.csv", header=True, inferSchema=True)
    quality = spark.read.csv("../data/quality_measurements.csv", header=True, inferSchema=True)
    downtime = spark.read.csv("../data/downtime_events.csv", header=True, inferSchema=True)
    shifts = spark.read.csv("../data/shift_log.csv", header=True, inferSchema=True)

    bronze_path = f"{WAREHOUSE_DIR}/bronze"
    sensors.write.mode("overwrite").parquet(f"{bronze_path}/sensor_readings")
    quality.write.mode("overwrite").parquet(f"{bronze_path}/quality_measurements")
    downtime.write.mode("overwrite").parquet(f"{bronze_path}/downtime_events")
    shifts.write.mode("overwrite").parquet(f"{bronze_path}/shift_log")
    return sensors, quality, downtime, shifts


def silver_layer(spark, sensors, quality, downtime, shifts):
    sensors_clean = (
        sensors.withColumn("reading_ts", F.to_timestamp("reading_ts"))
        .withColumn("reading_date", F.to_date("reading_ts"))
        .dropDuplicates(["machine_id", "reading_ts"])
    )
    quality_clean = (
        quality.withColumn("measured_ts", F.to_timestamp("measured_ts"))
        .withColumn("measured_date", F.to_date("measured_ts"))
        .dropDuplicates(["machine_id", "measured_ts"])
    )
    downtime_clean = (
        downtime.withColumn("downtime_start_ts", F.to_timestamp("downtime_start_ts"))
        .withColumn("downtime_date", F.to_date("downtime_start_ts"))
    )
    shifts_clean = shifts.withColumn("shift_date", F.to_date("shift_date"))

    silver_path = f"{WAREHOUSE_DIR}/silver"
    sensors_clean.write.mode("overwrite").partitionBy("reading_date").parquet(f"{silver_path}/sensor_readings")
    quality_clean.write.mode("overwrite").partitionBy("measured_date").parquet(f"{silver_path}/quality_measurements")
    downtime_clean.write.mode("overwrite").parquet(f"{silver_path}/downtime_events")
    shifts_clean.write.mode("overwrite").parquet(f"{silver_path}/shift_log")
    return sensors_clean, quality_clean, downtime_clean, shifts_clean


def gold_layer(spark, sensors, quality, downtime, shifts):
    daily_downtime = (
        downtime.groupBy("machine_id", "line_id", "downtime_date")
        .agg(F.sum("downtime_hours").alias("downtime_hours"))
    )

    daily_quality = (
        quality.groupBy("machine_id", "line_id", "measured_date")
        .agg(
            F.count("*").alias("units_measured"),
            F.sum("in_spec").alias("units_in_spec"),
        )
        .withColumn("quality_rate", F.round(F.col("units_in_spec") / F.col("units_measured"), 4))
    )

    gold_oee = (
        daily_quality.withColumnRenamed("measured_date", "production_date")
        .join(
            daily_downtime.withColumnRenamed("downtime_date", "production_date"),
            ["machine_id", "line_id", "production_date"], "left"
        )
        .fillna({"downtime_hours": 0.0})
        .withColumn("planned_hours", F.lit(24.0))
        .withColumn("availability", F.round((F.col("planned_hours") - F.col("downtime_hours")) / F.col("planned_hours"), 4))
    )

    gold_path = f"{WAREHOUSE_DIR}/gold"
    gold_oee.write.mode("overwrite").parquet(f"{gold_path}/fct_machine_daily_oee")

    return gold_oee


def main():
    if os.path.exists(WAREHOUSE_DIR):
        shutil.rmtree(WAREHOUSE_DIR)

    spark = get_spark()
    spark.sparkContext.setLogLevel("WARN")

    print("=== Bronze layer ===")
    sensors, quality, downtime, shifts = bronze_layer(spark)
    print(f"sensors: {sensors.count()}, quality: {quality.count()}, downtime: {downtime.count()}, shifts: {shifts.count()}")

    print("=== Silver layer ===")
    sensors_s, quality_s, downtime_s, shifts_s = silver_layer(spark, sensors, quality, downtime, shifts)

    print("=== Gold layer ===")
    gold = gold_layer(spark, sensors_s, quality_s, downtime_s, shifts_s)
    print(f"gold fct_machine_daily_oee rows: {gold.count()}")
    gold.groupBy("line_id").agg(
        F.round(F.avg("availability"), 4).alias("avg_availability"),
        F.round(F.avg("quality_rate"), 4).alias("avg_quality_rate"),
    ).orderBy("line_id").show()

    spark.stop()
    print("\nTransformation complete. Gold table ready for SPC (spc/) and Snowflake sync (snowflake_sync/).")


if __name__ == "__main__":
    main()
