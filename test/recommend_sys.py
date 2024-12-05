# cmd command: uvicorn recommend_sys:app --reload --host 127.0.0.1 --port 8000

# recommendation libraries
from datetime import datetime
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi_import.recommendation_system import recommend_similar_dates
from fastapi_import.db import get_db

app = FastAPI()

@app.post("/recommend_outfit")
async def recommend_outfit(
    member_id: int,
    date: datetime,
    lat: float,
    lon: float,
    db: Session = Depends(get_db)
):
    # 1. 데이터베이스에서 날씨 정보를 불러옴
    try:
        recommendations = recommend_similar_dates(member_id, lat, lon, date, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    if "error" in recommendations:
        raise HTTPException(status_code=400, detail=recommendations["error"])

    return recommendations