from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import sessionmaker
from fastapi_import.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# 환경 변수로부터 데이터베이스 URL 구성
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy 엔진 및 세션 생성
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_weatherdata():
    metadata = MetaData()
    WeatherData = Table("weather_data", metadata, autoload_with=engine)
    return WeatherData

def fetch_weatherdata(db,table,**filters):
    stmt = select(table)
    for column, value in filter.items():
        stmt = stmt.where(getattr(table.c, column)==value)

    result = db.execute(stmt).fetchall()
    return result

# 데이터베이스 세션을 제공하는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()