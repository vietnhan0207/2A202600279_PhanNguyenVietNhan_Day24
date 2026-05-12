# src/api/main.py
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """Raw patient data — chỉ admin."""
    df = pd.read_csv("data/raw/patients_raw.csv")
    return JSONResponse(content=df.head(10).to_dict(orient="records"))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """Anonymized data — ml_engineer và admin."""
    df = pd.read_csv("data/raw/patients_raw.csv")
    df_anon = anonymizer.anonymize_dataframe(df.head(10))
    return JSONResponse(content=df_anon.to_dict(orient="records"))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Aggregated metrics không có PII — data_analyst, ml_engineer, admin."""
    df = pd.read_csv("data/raw/patients_raw.csv")
    metrics = {
        "benh_distribution": df["benh"].value_counts().to_dict(),
        "avg_ket_qua": round(df["ket_qua_xet_nghiem"].mean(), 2),
        "total_patients": len(df),
    }
    return JSONResponse(content=metrics)

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Chỉ admin được xóa. Các role khác nhận 403."""
    return JSONResponse(
        content={"message": f"Patient {patient_id} deleted", "by": current_user["username"]}
    )

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
