
# cmd command
# 1: cd C:\Users\user\Desktop\WOT\grounded-sam
# 2: uvicorn fastapi_server:app --reload --host 127.0.0.1 --port 8000

# local page
# http://127.0.0.1:8000/docs


####################################################################
########################  Import libraires  ########################
####################################################################

# segment libraries
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi_import.segmentation import segment_image, enhance_class_name, grounding_dino_model, combine_masks_by_category, save_and_upload_image, get_class_masks
from datetime import datetime
import numpy as np
import cv2
import pandas as pd

# weather df libraries
from fastapi import HTTPException
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from fastapi_import.metadata_weather import get_weather_data
from fastapi_import.db import get_db

# recommendation libraries
from fastapi import Depends
from fastapi_import.recommendation_system import recommend_similar_outfit



#######################################################################
##########################  Additional code  ##########################
#######################################################################

# Categories
CATEGORIES = {
    'top': ['blouse', 'shirts', 'jacket','hoodie', 'coat'],
    'bottom': ['pants', 'skirt', 'dress', 'jean'],
    'shoes': ['shoes']
}

# 리플렉션을 사용하여 기존 테이블 가져오기
metadata = MetaData()
WeatherData = Table("weather_data", metadata, autoload_with=engine)

####################################################################
##########################  Fastapi code  ##########################
####################################################################

app = FastAPI()


@app.post("/segment")
async def segment_and_upload(
    image: UploadFile = File(...), 
    classes: str = Form(...),
    box_threshold: float = Form(0.35), 
    text_threshold: float = Form(0.25)
):
    try:
        image_data = await image.read()
        np_image = np.frombuffer(image_data, np.uint8)
        image_np = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
        if image_np is None:
            raise HTTPException(status_code=400, detail="Failed to decode image")
        
        detections = grounding_dino_model.predict_with_classes(
            image=image_np, 
            classes=enhance_class_name(classes.split(',')), 
            box_threshold=box_threshold, 
            text_threshold=text_threshold
        )
        
        masks = segment_image(cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB), detections.xyxy)
        titles = [classes.split(',')[class_id] for class_id in detections.class_id]
        class_masks = get_class_masks(titles, masks)

        s3_urls = []
        for category in CATEGORIES:
            combined_image = combine_masks_by_category(category, class_masks, image_np)
            if combined_image is not None:
                s3_url = save_and_upload_image(category, image.filename, combined_image)
                s3_urls.append(s3_url)

        return {"message": "Image segmented and processed", "urls": s3_urls}
    
    except Exception as e:
        print(f"Error in segment_and_upload: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.post("/add_weather")
async def add_weather(
    date: datetime,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db)
):
    # Meteostat에서 날씨 데이터 가져오기
    weather_data = get_weather_data(latitude, longitude, date)
    if not weather_data:
        raise HTTPException(status_code=404, detail="Weather data not found for given location and date.")

    # SQLAlchemy를 통해 DB에 저장
    db_data = WeatherData(
        date=date.date(),
        latitude=latitude,
        longitude=longitude,
        tavg=weather_data.get("tavg"),
        tmin=weather_data.get("tmin"),
        tmax=weather_data.get("tmax"),
        prcp=weather_data.get("prcp"),
        snow=weather_data.get("snow"),
        wdir=weather_data.get("wdir"),
        wspd=weather_data.get("wspd"),
        wpgt=weather_data.get("wpgt"),
        pres=weather_data.get("pres"),
        tsun=weather_data.get("tsun")
    )

    db.add(db_data)
    db.commit()
    db.refresh(db_data)

    return {"message": "Weather data added successfully", "data": db_data}



@app.post("/recommend_outfit")
async def recommend_outfit(
    date: datetime,
    latitude: float,
    longitude: float,
    db: Session = Depends(get_db)
):
    # 1. 데이터베이스에서 날씨 정보를 불러와 데이터프레임으로 변환
    weather_data = db.query(WeatherData).all()
    if not weather_data:
        raise HTTPException(status_code=404, detail="No weather data found in the database")

    # SQLAlchemy 객체를 DataFrame으로 변환
    df = pd.DataFrame([{
        "Filename": d.filename,
        "date": d.date,
        "tavg": d.tavg,
        "tmin": d.tmin,
        "tmax": d.tmax,
        "prcp": d.prcp,
        "snow": d.snow,
        "wdir": d.wdir,
        "wspd": d.wspd,
        "pres": d.pres
    } for d in weather_data])

    # 2. 추천 시스템을 사용하여 유사한 날씨의 추천 경로 생성
    recommendations = recommend_similar_outfit(latitude, longitude, date, df)

    # 3. 추천 결과 반환
    if "error" in recommendations:
        raise HTTPException(status_code=400, detail=recommendations["error"])

    return recommendations