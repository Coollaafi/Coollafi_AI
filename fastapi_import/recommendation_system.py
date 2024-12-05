import pandas as pd
from datetime import datetime
from fastapi_import.metadata_weather import get_weather_data
from scipy.spatial.distance import euclidean
from sqlalchemy.sql import text
from sqlalchemy.orm import Session

def fetch_weather_data(lat, lon, date):
    """지정된 날짜와 위치에 해당하는 날씨 데이터를 가져옴"""
    return get_weather_data(lat, lon, date)

def fill_nan_with_user_avg(today_weather, user_weather_data):
    """
    today_weather의 NaN 값을 사용자의 과거 데이터에서 동일 열의 평균값으로 대체
    """
    for key in today_weather:
        # 현재 키가 user_weather_data에 있는 열인지 확인
        if key in user_weather_data.columns:
            # today_weather의 값이 NaN인지 확인
            if pd.isna(today_weather[key]):
                # 사용자 과거 데이터의 평균 계산
                column_mean = user_weather_data[key].mean()
                today_weather[key] = column_mean if pd.notna(column_mean) else 0
    return today_weather

def fetch_user_weather_data(member_id: int, db: Session):
    """
    특정 사용자의 과거 날씨 데이터를 가져오는 함수.
    WeatherData와 CollageImage의 관계를 활용하여 사용자의 데이터만 가져옴.
    """
    query = text("""
    SELECT wd.id, wd.date, wd.tavg, wd.tmin, wd.tmax, wd.prcp, wd.snow, wd.wdir, wd.wspd, wd.pres
    FROM weather_data wd
    JOIN collage_image ci ON wd.id = ci.weather_data_id
    WHERE ci.member_id = :member_id
    """)

    # SQL 실행
    result = db.execute(query, {"member_id": member_id}).fetchall()

    if not result:
        return pd.DataFrame()  # 결과가 없으면 빈 DataFrame 반환

    # 결과를 Pandas DataFrame으로 변환
    columns = ["id", "date", "tavg", "tmin", "tmax", "prcp", "snow", "wdir", "wspd", "pres"]
    weather_data = pd.DataFrame(result, columns=columns)

    # NaN 값을 각 열의 평균값으로 대체
    weather_data.fillna(weather_data.mean(), inplace=True)
    weather_data.fillna(0, inplace=True)  # 평균값이 없을 경우 0으로 대체

    return weather_data

def calculate_similarity(row, target_weather):
    """유클리드 거리로 유사도 계산 (날짜는 월 기반으로 계산하여 포함)"""
    features = ["tavg", "tmin", "tmax", "prcp", "snow", "wdir", "wspd", "pres"]

    # row["date"]가 DataFrame에서 올바르게 읽히는지 확인
    row_date = row.get("date")  # 안전한 참조 방법 사용
    if isinstance(row_date, pd.Timestamp):  # Timestamp 형식일 경우 처리
        row_date = row_date.to_pydatetime()

    # Target weather에서 날짜 가져오기
    target_date = target_weather.get("date")  # dict에서 날짜 참조
    if not isinstance(target_date, datetime):  # 날짜 형식 확인
        raise ValueError("Invalid target date format")

    # 월-일 분리
    row_month, row_day = row_date.month, row_date.day
    target_month, target_day = target_date.month, target_date.day

    date_similarity = 0

    # 월-일이 모두 같을 경우 유사성 추가
    if row_month == target_month and row_day == target_day:
        date_similarity -= 0.5  # 매우 유사하므로 유사성 감소

    # 월이 같거나 월 차이가 1 이하인 경우 유사성 추가
    elif abs(row_month - target_month) <= 1:
        date_similarity -= 0.3  # 다소 유사

    # 날씨 값 유사도 계산
    row_weather = [float(x) if x is not None else 0 for x in row[features]]
    target_weather_values = [float(target_weather[feature]) if target_weather[feature] is not None else 0 for feature in features]

    # 최종 유사도 계산 (날씨 값 + 날짜 유사도)
    return euclidean(row_weather, target_weather_values) + date_similarity



def find_similar_weather(df, target_weather, top_n=3):
    """날씨 정보가 가장 유사한 상위 top_n 개의 날짜를 반환"""
    # 유사도 계산
    df["similarity"] = df.apply(lambda row: calculate_similarity(row, target_weather), axis=1)

    # 유사도가 가장 낮은 상위 n개의 행 선택
    similar_rows = df.nsmallest(top_n, "similarity")

    # 원본 date 값 반환 (연도 포함)
    return similar_rows["date"].values


def recommend_similar_dates(member_id:int, lat, lon, date, db:Session):
    """현재 위치와 날짜를 기반으로 유사한 날짜를 추천"""

    try:
        # 1. 사용자의 과거 날씨 데이터 가져오기
        user_weather_data = fetch_user_weather_data(member_id, db)
        print(f"User weather data: {user_weather_data}")  # 디버깅용 출력
        if user_weather_data.empty:
            return {"error": "사용자의 과거 날씨 데이터를 찾을 수 없습니다."}


        # 2. 오늘의 날씨 데이터 가져오기
        today_weather = fetch_weather_data(lat, lon, date)
        print(f"Today weather data: {today_weather}")  # 디버깅용 출력
        if not today_weather:
            return {"error": "날씨 정보를 찾을 수 없습니다."}

        # 3. 사용자의 과거 데이터 평균으로 NaN 값 채우기
        today_weather = fill_nan_with_user_avg(today_weather, user_weather_data)
        today_weather["date"] = date  # date 추가
        print(f"Today weather data after processing: {today_weather}")

        # 3. 유사한 날씨의 상위 3개 날짜 찾기
        similar_dates = find_similar_weather(user_weather_data, today_weather, top_n=3)
        print(f"Similar dates: {similar_dates}")  # 디버깅용 출력
        
        # numpy.datetime64 → str 변환
        similar_dates = [str(date) for date in similar_dates]

        # 4. 유사한 날짜 반환
        return {
            "Similar_Dates": list(similar_dates)  # 연도를 포함한 원래 날짜 반환
        }

    except Exception as e:
        print(f"Error occured: {e}")
        raise