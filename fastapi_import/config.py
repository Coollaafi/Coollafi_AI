import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
REGION = os.getenv("REGION")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")