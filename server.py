# uvicorn server:app --reload --host 127.0.0.1 --port 8000
# dotenv error: python -m uvicorn server:app --reload --host 127.0.0.1 --port 8000
# http://127.0.0.1:8000/docs

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends

# segmentation
import numpy as np
import cv2
from fastapi_import.segmentation import enhance_class_name, segment_image, get_class_masks, combine_masks_by_category, save_and_upload_image
from fastapi_import.segmentation import grounding_dino_model, CATEGORIES

# add weather
from datetime import datetime
from sqlalchemy import insert
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi_import.metadata_weather import get_weather_data
from fastapi_import.db import get_db, get_weatherdata
import math

# recommend weather
from datetime import datetime
import pandas as pd
from fastapi_import.recommendation_system import recommend_similar_dates
from fastapi_import.db import get_db



# fastapi
app = FastAPI()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# FastAPI 애플리케이션 초기화
app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*"는 모든 도메인에서 접근 가능. 특정 도메인을 명시하려면 ["http://example.com"] 형태로 작성.
    allow_methods=["*"],  # 허용할 HTTP 메서드. ["GET", "POST"] 등으로 제한 가능.
    allow_headers=["*"],  # 허용할 HTTP 헤더. ["Authorization", "Content-Type"] 등으로 제한 가능.
    allow_credentials=True,  # 쿠키 등을 포함한 인증 정보 허용 여부.
)

# /segment
@app.post("/segment")
async def segment_and_upload(
    image: UploadFile = File(...), 
    classes: str = Form(...),
    box_threshold: float = Form(0.35), 
    text_threshold: float = Form(0.25)
):
    print(f"Received file: {image.filename}")
    print(f"Received classes: {classes}")

    # 이미지 로드 및 전처리
    try:
        image_data = await image.read()
        print(f"Image data size: {len(image_data)} bytes")
    except Exception as e:
        print(f"Error reading image: {str(e)}")
        return {"error": "Invalid image"}

    np_image = np.frombuffer(image_data, np.uint8)
    image_np = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

    if image_np is None:
        return {"error": "Failed to decode image"}

    # GroundingDINO 탐지
    print(enhance_class_name(classes.split(',')))
    detections = grounding_dino_model.predict_with_classes(
        image=image_np, 
        classes=enhance_class_name(classes.split(',')), 
        box_threshold=box_threshold, 
        text_threshold=text_threshold
    )
    print(detections.class_id)

    # SAM으로 객체 분할
    masks = segment_image(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB), detections.xyxy)
    titles = [classes.split(',')[class_id] for class_id in detections.class_id]
    print("Detected classes and titles:", titles)  # 디버깅: 감지된 클래스와 이름 확인

    # 클래스별로 마스크 저장
    class_masks = get_class_masks(titles, masks)

    # S3에 각 카테고리별로 이미지를 업로드하고 URL을 반환
    s3_urls = []
    for category in CATEGORIES:
        combined_image = combine_masks_by_category(category, class_masks, image_np)
        if combined_image is not None:
            s3_url = save_and_upload_image(category, image.filename, combined_image)
            print(f"Uploaded image for category '{category}' to S3:", s3_url)  # 디버깅: S3 업로드된 URL 확인
            s3_urls.append(s3_url)

    return {"message": "Image segmented and processed", "urls": s3_urls}



# /add_weather
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
    


# /recommend_outfit
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