import piexif
import pillow_heif
from PIL import Image
from PIL.ExifTags import TAGS
from geopy.geocoders import Nominatim
from meteostat import Point, Daily
from datetime import datetime

# HEIC 포맷을 JPG로 변환하고 메타데이터를 유지: back에서 받아서 필요 없어짐
def heic_to_jpg(heic_path):
    pillow_heif.register_heif_opener()
    heic_image = Image.open(heic_path)
    metadata = heic_image.info.get('exif')
    jpeg_path = heic_path.replace('.HEIC', '.jpg')
    heic_image.convert('RGB').save(jpeg_path, 'JPEG', exif=metadata)
    return jpeg_path

# 이미지 메타데이터에서 GPS와 날짜 정보를 추출: back에서 받아서 필요 없어짐
def extract_metadata(image_path):
    try:
        img_path = heic_to_jpg(image_path) if image_path.lower().endswith('.heic') else image_path
        image = Image.open(img_path)
        info = image._getexif()
        if not info:
            return None

        gps_info = {TAGS.get(tag, tag): value for tag, value in info.items() if TAGS.get(tag, tag) == 'GPSInfo'}
        date_info = {TAGS.get(tag, tag): value for tag, value in info.items() if TAGS.get(tag, tag) in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']}
        lat, lon = parse_gps(gps_info)
        date = date_info.get('DateTimeOriginal', None)
        if lat and lon and date:
            return {"lat": lat, "lon": lon, "date": date}
    except Exception as e:
        print(f"메타데이터 추출 오류: {e}")
    return None

# GPS 정보 파싱: back에서 받아서 필요 없어짐
def parse_gps(gps_info):
    gps_lat = gps_info.get(2)
    gps_lon = gps_info.get(4)
    if gps_lat and gps_lon:
        lat = gps_lat[0] + gps_lat[1] / 60 + gps_lat[2] / 3600
        lon = gps_lon[0] + gps_lon[1] / 60 + gps_lon[2] / 3600
        return lat, lon
    return None, None

# 날짜에 해당하는 날씨 정보 가져오기
def get_weather_data(lat, lon, date):
    location = Point(lat, lon)
    data = Daily(location, date, date)
    data = data.fetch()
    if not data.empty:
        return data.iloc[0].to_dict()
    return {}
