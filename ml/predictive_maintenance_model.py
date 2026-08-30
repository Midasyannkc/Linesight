"""
Predictive maintenance model: a Random Forest classifier predicting
whether a machine will fail within the next 6 hours, trained on sensor
features (temperature, vibration, pressure) and evaluated against real
injected ground truth. Registered in MLflow, the same production-ML
discipline used elsewhere in this portfolio.

Run: python predictive_maintenance_model.py
Reads:  ../data/warehouse/silver/sensor_readings/*/*.parquet
Writes: ../data/predictive_maintenance_metrics.csv, MLflow run + registry
"""
import duckdb
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score


def load_features():
    con = duckdb.connect()
    df = con.execute("""
        SELECT machine_id, temperature_c, vibration_mm_s, pressure_psi, will_fail_within_6h
        FROM parquet_scan('../data/warehouse/silver/sensor_readings/*/*.parquet')
    """).df()
    con.close()
    return df


def main():
    df = load_features()
    print(f"Loaded {len(df)} sensor readings, positive rate: {df['will_fail_within_6h'].mean()*100:.2f}%")

    X = df[["temperature_c", "vibration_mm_s", "pressure_psi"]].values
    y = df["will_fail_within_6h"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment("linesight-predictive-maintenance")

    with mlflow.start_run(run_name="random_forest_v1"):
        model = RandomForestClassifier(
            n_estimators=200, max_depth=8, min_samples_leaf=5,
            class_weight="balanced",
            random_state=42,
        )
        model.fit(X_train, y_train)

        y_proba = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)

        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_proba)

        feature_importance = dict(zip(["temperature_c", "vibration_mm_s", "pressure_psi"], model.feature_importances_))

        mlflow.log_params({
            "model_type": "RandomForestClassifier",
            "n_estimators": 200, "max_depth": 8, "min_samples_leaf": 5,
            "class_weight": "balanced", "test_size": 0.25,
        })
        mlflow.log_metrics({
            "precision": precision, "recall": recall, "f1_score": f1, "roc_auc": auc,
            "n_train": len(X_train), "n_test": len(X_test),
        })
        mlflow.sklearn.log_model(model, "model", registered_model_name="linesight-predictive-maintenance")

        print(f"\nPrecision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}, ROC-AUC: {auc:.3f}")
        print(f"Feature importance: {feature_importance}")

        with open("../data/predictive_maintenance_metrics.csv", "w") as f:
            f.write("metric,value\n")
            f.write(f"precision,{precision:.4f}\n")
            f.write(f"recall,{recall:.4f}\n")
            f.write(f"f1_score,{f1:.4f}\n")
            f.write(f"roc_auc,{auc:.4f}\n")
            for feat, imp in feature_importance.items():
                f.write(f"feature_importance_{feat},{imp:.4f}\n")


if __name__ == "__main__":
    main()
