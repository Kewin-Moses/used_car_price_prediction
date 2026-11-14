import json
from pathlib import Path

import joblib
import pandas as pd
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .forms import RegisterForm, CarPredictionForm
from .models import Prediction

MODEL_PATH = settings.BASE_DIR / "model_artifacts" / "best_model.joblib"
METRICS_PATH = settings.BASE_DIR / "model_artifacts" / "metrics.json"
KNOWLEDGE_PATH = settings.BASE_DIR / "predictor" / "knowledge_base.txt"

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()
    return render(request, "predictor/register.html", {"form": form})

@login_required
def dashboard(request):
    predictions = Prediction.objects.filter(user=request.user).order_by("-created_at")[:5]
    metrics = {}
    if METRICS_PATH.exists():
        metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return render(request, "predictor/dashboard.html", {
        "predictions": predictions,
        "total_predictions": Prediction.objects.filter(user=request.user).count(),
        "metrics": metrics,
    })

@login_required
def predict(request):
    if request.method == "POST":
        form = CarPredictionForm(request.POST)
        if form.is_valid():
            if not MODEL_PATH.exists():
                messages.error(request, "ML model not found. Run the train_model command first.")
                return redirect("predict")

            data = form.cleaned_data
            model = joblib.load(MODEL_PATH)
            input_data = pd.DataFrame([{
                "Car_Name": data["car_name"],
                "Year": data["year"],
                "Present_Price": data["present_price"],
                "Driven_kms": data["driven_kms"],
                "Fuel_Type": data["fuel_type"],
                "Selling_type": data["selling_type"],
                "Transmission": data["transmission"],
                "Owner": int(data["owner"]),
            }])
            predicted_price = max(0.0, float(model.predict(input_data)[0]))

            saved = Prediction.objects.create(
                user=request.user,
                car_name=data["car_name"],
                year=data["year"],
                present_price=data["present_price"],
                driven_kms=data["driven_kms"],
                fuel_type=data["fuel_type"],
                selling_type=data["selling_type"],
                transmission=data["transmission"],
                owner=int(data["owner"]),
                predicted_price=round(predicted_price, 2),
            )
            return render(request, "predictor/predict.html", {
                "form": form, "prediction": saved,
            })
    else:
        form = CarPredictionForm()
    return render(request, "predictor/predict.html", {"form": form})

@login_required
def history(request):
    predictions = Prediction.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "predictor/history.html", {"predictions": predictions})

@login_required
def download_report(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id, user=request.user)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="car_prediction_{prediction.id}.pdf"'
    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 80
    pdf.setTitle("Used Car Price Prediction Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(55, y, "Used Car Price Prediction Report")
    y -= 45
    pdf.setFont("Helvetica", 12)
    details = [
        ("User", request.user.username),
        ("Car name", prediction.car_name),
        ("Manufacturing year", str(prediction.year)),
        ("Present price", f"Rs. {prediction.present_price:.2f} lakhs"),
        ("Kilometres driven", f"{prediction.driven_kms:,}"),
        ("Fuel type", prediction.fuel_type),
        ("Selling type", prediction.selling_type),
        ("Transmission", prediction.transmission),
        ("Previous owners", str(prediction.owner)),
        ("Estimated selling price", f"Rs. {prediction.predicted_price:.2f} lakhs"),
        ("Prediction date", prediction.created_at.strftime("%d-%m-%Y %H:%M")),
    ]
    for label, value in details:
        pdf.drawString(60, y, f"{label}: {value}")
        y -= 27
    pdf.setFont("Helvetica-Oblique", 9)
    pdf.drawString(60, 80, "This is an educational ML estimate, not a guaranteed market price.")
    pdf.save()
    return response

def retrieve_context(question):
    """Small local retrieval step over the supplied project knowledge base."""
    if not KNOWLEDGE_PATH.exists():
        return "No local knowledge base was found."
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    text = KNOWLEDGE_PATH.read_text(encoding="utf-8")
    chunks = [part.strip() for part in text.split("\\n\\n") if part.strip()]
    if not chunks:
        return ""
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(chunks + [question])
    scores = cosine_similarity(matrix[-1], matrix[:-1]).flatten()
    best_indices = scores.argsort()[-3:][::-1]
    return "\\n\\n".join(chunks[i] for i in best_indices if scores[i] > 0)

@login_required
def chatbot(request):
    answer = None
    question = ""
    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        if question:
            context = retrieve_context(question)
            if not context:
                answer = "I could not find relevant information in the project's knowledge base."
            else:
                prompt = (
                    "Answer the user's question using only the context below. "
                    "If the context does not contain the answer, say so.\\n\\n"
                    f"Context:\\n{context}\\n\\nQuestion: {question}"
                )
                try:
                    result = requests.post(
                        settings.OLLAMA_URL,
                        json={"model": settings.OLLAMA_MODEL, "prompt": prompt, "stream": False},
                        timeout=90,
                    )
                    result.raise_for_status()
                    answer = result.json().get("response", "No response returned.")
                except requests.RequestException:
                    answer = (
                        "Relevant information was retrieved, but the local Ollama service could not be reached. "
                        "Install/start Ollama and pull the configured model. Retrieved context:\\n\\n" + context
                    )
    return render(request, "predictor/chatbot.html", {"answer": answer, "question": question})
