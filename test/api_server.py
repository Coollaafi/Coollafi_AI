# cmd command: uvicorn api_server:app --reload --host 127.0.0.1 --port 8000

import sys
import os
import torch
import boto3
import numpy as np
import cv2
from fastapi import FastAPI, File, UploadFile, Form
from segment_anything import sam_model_registry, SamPredictor
from typing import List

# NameError: _C is not defined 해결방안:
# python setup.py build_ext --inplace

# 선행 코드: cd C:\Users\user\Desktop\WOT\grounded-sam
sys.path.append(os.path.join(os.getcwd(), "GroundingDINO"))
from GroundingDINO.groundingdino.util.inference import Model

# Paths & Device
HOME = os.getcwd()
# DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DEVICE = "cpu"
S3_BUCKET_NAME = "hanihanibucket"

# Model Paths
GROUNDING_DINO_CONFIG = os.path.join(HOME, "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py")
GROUNDING_DINO_CHECKPOINT = os.path.join(HOME, "weights", "groundingdino_swint_ogc.pth")
SAM_CHECKPOINT = os.path.join(HOME, "weights", "sam_vit_h_4b8939.pth")

# Load Models
grounding_dino_model = Model(model_config_path=GROUNDING_DINO_CONFIG, model_checkpoint_path=GROUNDING_DINO_CHECKPOINT)
sam = sam_model_registry["vit_h"](checkpoint=SAM_CHECKPOINT).to(DEVICE)
sam_predictor = SamPredictor(sam)

# Initialize FastAPI app
app = FastAPI()

# AWS S3 Client
s3 = boto3.client('s3')

# Categories
CATEGORIES = {
    'top': ['blouse', 'shirts', 'jacket','hoodie', 'coat'],
    'bottom': ['pants', 'skirt', 'dress', 'jean'],
    'shoes': ['shoes']
}

# Enhance class names for detection
def enhance_class_name(classes: List[str]) -> List[str]:
    return [f"all shoes" if cls == "shoes" else f"{cls}" for cls in classes]

# Segment items using SAM
def segment_image(image: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    sam_predictor.set_image(image)
    masks = []
    for box in boxes:
        mask, score, _ = sam_predictor.predict(box=box, multimask_output=True)
        masks.append(mask[np.argmax(score)])
    return np.array(masks)

# 카테고리 딕셔너리에 따라 각 클래스별로 마스크를 생성하고 결합하는 함수
def get_class_masks(titles: List[str], masks: np.ndarray) -> dict:
    # 각 클래스별로 마스크를 저장하는 딕셔너리 생성
    class_masks = {}
    for title, mask in zip(titles, masks):
        class_masks[title] = mask
    print("class_masks:", class_masks.keys())  # 디버깅: 저장된 클래스 이름 확인
    return class_masks

# 카테고리별로 마스크를 결합하는 함수
def combine_masks_by_category(
    category: str, class_masks: dict, image: np.ndarray
) -> np.ndarray:
    white_background = np.ones_like(image) * 255
    # 해당 카테고리에 속하는 클래스들의 마스크만 선택
    category_masks = [
        class_masks[cls] for cls in CATEGORIES[category] if cls in class_masks
    ]
    
    print(f"Combining masks for category '{category}':", [cls for cls in CATEGORIES[category] if cls in class_masks])  # 디버깅: 카테고리별 클래스 확인
    
    if not category_masks:
        print(f"No masks found for category '{category}'.")  # 디버깅: 카테고리에 해당하는 마스크가 없을 경우
        return None

    # 선택된 마스크들을 결합
    combined_mask = np.logical_or.reduce(category_masks)
    combined_image = np.where(combined_mask[..., None], image, white_background)

    # 결합된 마스크 영역을 기준으로 이미지 크롭
    mask_indices = np.where(combined_mask)
    min_y, max_y = mask_indices[0].min(), mask_indices[0].max()
    min_x, max_x = mask_indices[1].min(), mask_indices[1].max()
    cropped_image = combined_image[min_y:max_y+1, min_x:max_x+1, :]
    
    return cropped_image


# Save segmented image and upload to S3
def save_and_upload_image(category: str, original_filename: str, image: np.ndarray) -> str:
    # Extract original file name without extension
    base_name, ext = os.path.splitext(original_filename)
    file_name = f"{base_name}_{category}{ext}"
    local_path = os.path.join(HOME, file_name)

    # Save the image locally
    cv2.imwrite(local_path, image)

    # Upload to S3 under segmented_img folder
    s3_key = f"segmented_img/{file_name}"
    s3.upload_file(local_path, S3_BUCKET_NAME, s3_key)

    # Generate the S3 URL
    s3_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_key}"
    os.remove(local_path)  # Clean up local storage
    return s3_url

from fastapi import Depends
# API Endpoint to process image
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