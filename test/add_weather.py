# cmd command: uvicorn add_weather:app --reload --host 127.0.0.1 --port 8000

from fastapi import FastAPI, HTTPException, Depends
from datetime import datetime
from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi_import.metadata_weather import get_weather_data
from fastapi_import.db import get_db, get_weatherdata
import math

app = FastAPI()

@app.post("/add_weather")
async def add_weather(
    date: datetime,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db)
):
    try:
        # Meteostat에서 날씨 데이터 가져오기
        weather_data = get_weather_data(latitude, longitude, date)
        if not weather_data:
            raise HTTPException(status_code=404, detail="Weather data not found for given location and date.")

        weather_table = get_weatherdata()

        # SQLAlchemy를 통해 DB에 저장
        data_to_insert = {
            "date": date.date(),
            "tavg": weather_data.get("tavg"),
            "tmin": weather_data.get("tmin"),
            "tmax": weather_data.get("tmax"),
            "prcp": weather_data.get("prcp"),
            "snow": 0 if math.isnan(weather_data.get("snow")) else weather_data.get("snow"),
            "wdir": weather_data.get("wdir"),
            "wspd": weather_data.get("wspd"),
            "pres": weather_data.get("pres"),
        }

        # INSERT 실행
        stmt = insert(weather_table).values(data_to_insert)
        result = db.execute(stmt)
        db.commit()

        # 방금 삽입된 ID 가져오기
        new_id = result.lastrowid

        return {
            "message": "Weather data added successfully",
            "data": data_to_insert,
            "inserted_id": new_id
        }
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")