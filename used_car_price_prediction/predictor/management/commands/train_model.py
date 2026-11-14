import json
from pathlib import Path

import joblib
import pandas as pd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

class Command(BaseCommand):
    help = "Train and compare Linear Regression and Random Forest models."

    def handle(self, *args, **options):
        dataset_path = settings.BASE_DIR / "dataset" / "car data.csv"
        if not dataset_path.exists():
            raise CommandError(f"Dataset not found: {dataset_path}")

        df = pd.read_csv(dataset_path)
        required = [
            "Car_Name", "Year", "Selling_Price", "Present_Price",
            "Driven_kms", "Fuel_Type", "Selling_type", "Transmission", "Owner"
        ]
        missing_columns = [column for column in required if column not in df.columns]
        if missing_columns:
            raise CommandError(f"CSV is missing columns: {missing_columns}")

        df = df[required].drop_duplicates()
        df = df.dropna(subset=["Selling_Price"])
        X = df.drop(columns=["Selling_Price"])
        y = df["Selling_Price"]

        numeric_features = ["Year", "Present_Price", "Driven_kms", "Owner"]
        categorical_features = ["Car_Name", "Fuel_Type", "Selling_type", "Transmission"]

        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median"))
        ])
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore"))
        ])
        preprocessor = ColumnTransformer([
            ("numeric", numeric_pipeline, numeric_features),
            ("categorical", categorical_pipeline, categorical_features),
        ])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )

        algorithms = {
            "Linear Regression": LinearRegression(),
            "Random Forest": RandomForestRegressor(
                n_estimators=250, random_state=42, min_samples_leaf=2
            ),
        }

        metrics = {}
        best_model = None
        best_name = None
        best_mae = float("inf")

        for name, algorithm in algorithms.items():
            pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("regressor", algorithm),
            ])
            pipeline.fit(X_train, y_train)
            predictions = pipeline.predict(X_test)
            mae = mean_absolute_error(y_test, predictions)
            rmse = mean_squared_error(y_test, predictions) ** 0.5
            r2 = r2_score(y_test, predictions)
            metrics[name] = {
                "MAE": round(float(mae), 4),
                "RMSE": round(float(rmse), 4),
                "R2": round(float(r2), 4),
            }
            self.stdout.write(
                f"{name}: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}"
            )
            if mae < best_mae:
                best_mae = mae
                best_model = pipeline
                best_name = name

        artifact_dir = settings.BASE_DIR / "model_artifacts"
        artifact_dir.mkdir(exist_ok=True)
        joblib.dump(best_model, artifact_dir / "best_model.joblib")
        output = {
            "best_model": best_name,
            "dataset_rows": int(len(df)),
            "target": "Selling_Price",
            "metrics": metrics,
        }
        (artifact_dir / "metrics.json").write_text(
            json.dumps(output, indent=4), encoding="utf-8"
        )
        self.stdout.write(self.style.SUCCESS(f"Best model: {best_name}"))
        self.stdout.write(self.style.SUCCESS("Saved model_artifacts/best_model.joblib"))
