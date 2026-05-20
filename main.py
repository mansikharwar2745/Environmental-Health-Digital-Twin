import numpy as np
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler

app = FastAPI(title="Environmental Health Digital Twin Core")

# Enable CORS so your frontend can communicate seamlessly with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock historical data to pre-train our predictive engine on startup
def pre_train_engine():
    np.random.seed(42)
    X = np.random.rand(200, 4) * 100  # Features: AQI, Traffic, Waste, Water
    # Outcome: Risk or case count driven by variables with a bit of random noise
    y = (X[:, 0] * 0.4) + (X[:, 1] * 0.1) + (X[:, 2] * 0.2) + (X[:, 3] * 0.3) + np.random.normal(0, 5, 200)
    
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_scaled, y)
    return model, scaler

ml_model, data_scaler = pre_train_engine()

class TelemetryInput(BaseModel):
    aqi: float
    traffic: float
    waste_complaints: float
    water_contamination: float

@app.post("/api/predict-risk")
async def predict_risk(data: TelemetryInput):
    # Prepare vector for prediction
    input_vector = np.array([[data.aqi, data.traffic, data.waste_complaints, data.water_contamination]])
    scaled_vector = data_scaler.transform(input_vector)
    
    # Generate prediction
    raw_prediction = ml_model.predict(scaled_vector)[0]
    
    # Normalize outcomes securely between 0 and 100
    risk_score = min(max(float(raw_prediction), 5.0), 95.0)
    respiratory_factor = min(max(float(data.aqi * 0.6 + data.traffic * 0.4), 0.0), 100.0)
    waterborne_factor = min(max(float(data.water_contamination * 0.7 + data.waste_complaints * 0.3), 0.0), 100.0)
    
    return {
        "status": "success",
        "composite_health_risk": round(risk_score, 2),
        "vectors": {
            "respiratory_outbreak_probability": round(respiratory_factor, 2),
            "waterborne_disease_index": round(waterborne_factor, 2)
        }
    }

# Entrypoint to serve index.html directly from root URL
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("index.html", "r") as f:
        return f.read()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)