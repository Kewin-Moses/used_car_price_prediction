# Used Car Price Prediction — Django + uv

A beginner-friendly Django project built around the supplied `car data.csv`.

## Dataset details

The supplied CSV contains 301 rows and these exact columns:

- `Car_Name`
- `Year`
- `Selling_Price` (prediction target)
- `Present_Price`
- `Driven_kms`
- `Fuel_Type`
- `Selling_type`
- `Transmission`
- `Owner`

The application predicts `Selling_Price` from the other eight columns. Prices are displayed in lakh rupees, matching the source dataset.

## Features

- User registration, login and logout (Django authentication)
- Login-protected dashboard
- Car prediction form using the dataset's car names and categories
- Linear Regression and Random Forest model training/comparison
- MAE, RMSE and R² metrics
- Saved prediction history per user
- PDF prediction report
- Chart.js model comparison chart
- Basic RAG chatbot using local TF-IDF retrieval + Ollama generation

## 1. Install uv

Windows PowerShell:

```powershell
winget install --id astral-sh.uv -e
```

Or use the official installation instructions: https://docs.astral.sh/uv/getting-started/installation/

Close and reopen the terminal after installation. Check:

```powershell
uv --version
```

## 2. Open the project

Extract the ZIP file. Open the extracted `used_car_price_prediction` folder in VS Code.

The CSV must be located at:

```text
dataset/car data.csv
```

It is included in this project ZIP.

## 3. Create the environment and install dependencies

From the folder containing `pyproject.toml`:

```powershell
uv python install 3.11
uv sync
```

`uv sync` creates `.venv` and installs dependencies from `pyproject.toml`. Do not run `pip install`.

## 4. Train the ML models

```powershell
uv run python manage.py train_model
```

This command:
1. Reads `dataset/car data.csv`.
2. Separates `Selling_Price` from the eight input columns.
3. Splits data into training and test sets.
4. Preprocesses numeric and categorical columns.
5. Trains Linear Regression and Random Forest.
6. Prints MAE, RMSE and R².
7. Saves the best model to `model_artifacts/best_model.joblib`.
8. Saves comparison metrics to `model_artifacts/metrics.json`.

The model is selected using the lower test-set MAE. The test set is used for comparison, so treat the score as an initial estimate; a larger dataset and cross-validation would give a more stable evaluation.

## 5. Create database tables

```powershell
uv run python manage.py makemigrations
uv run python manage.py migrate
```

This starter uses SQLite so you can run it without configuring a database server. The database file `db.sqlite3` is created automatically.

## 6. Start Django

```powershell
uv run python manage.py runserver
```

Open http://127.0.0.1:8000/

Register a user, log in, open Predict, enter car details and submit.

## 7. Optional Django admin

Create an admin account:

```powershell
uv run python manage.py createsuperuser
```

Open http://127.0.0.1:8000/admin/

## 8. Optional RAG chatbot with Ollama

The chatbot page is included. It retrieves relevant paragraphs from `predictor/knowledge_base.txt` using TF-IDF and sends those paragraphs to a local Ollama model.

1. Install Ollama from https://ollama.com/
2. In a separate terminal, download a model:

```powershell
ollama pull llama3.2
```

3. Start Ollama (the Windows app normally runs its local service).
4. Keep `OLLAMA_URL` and `OLLAMA_MODEL` in `carprice_project/settings.py` aligned with your Ollama setup.
5. Log in and open the Car Assistant page.

Without Ollama, retrieval still runs, and the page reports that generation is unavailable.

## Common commands

```powershell
uv sync
uv run python manage.py train_model
uv run python manage.py makemigrations
uv run python manage.py migrate
uv run python manage.py runserver
```

If you change the CSV, retrain the model:

```powershell
uv run python manage.py train_model
```

## Important notes

- This dataset has only 301 rows, so the model may not generalize well to every car.
- Car names are one-hot encoded. An unseen car name can be entered, but its encoded category will be all zeros because the encoder ignores unknown categories.
- The form limits manufacturing year to 2000–2026 and uses categories found in the supplied CSV.
- Predictions are educational estimates, not guaranteed resale prices.
- SQLite is selected to make the first run easy. MySQL can be configured later if your submission requires it.
- Before deployment, set a secure secret key, `DEBUG=False`, configure allowed hosts, and use production database settings.
