import sys
import os
import random
import boto3
import numpy as np
import torch
import cv2
from segment_anything import sam_model_registry, SamPredictor
from typing import List
from fastapi_import.config import S3_BUCKET_NAME, REGION, ACCESS_KEY, SECRET_KEY

# NameError: _C is not defined 해결방안:
# python setup.py build_ext --inplace

# 선행 코드: cd C:\Users\user\Desktop\WOT\grounded-sam
sys.path.append(os.path.join(os.getcwd(), "GroundingDINO"))
from GroundingDINO.groundingdino.util.inference import Model

# Paths & Device
HOME = os.getcwd()
# DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
DEVICE = torch.device("cpu")

# Model Paths
GROUNDING_DINO_CONFIG = os.path.join(HOME, "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py")
GROUNDING_DINO_CHECKPOINT = os.path.join(HOME, "weights", "groundingdino_swint_ogc.pth")
SAM_CHECKPOINT = os.path.join(HOME, "weights", "sam_vit_h_4b8939.pth")

# Load Models
grounding_dino_model = Model(model_config_path=GROUNDING_DINO_CONFIG, model_checkpoint_path=GROUNDING_DINO_CHECKPOINT)
sam = sam_model_registry["vit_h"](checkpoint=SAM_CHECKPOINT).to(DEVICE)
sam_predictor = SamPredictor(sam)

# AWS S3 Client
s3 = boto3.client('s3',
                  aws_access_key_id = ACCESS_KEY,
                  aws_secret_access_key = SECRET_KEY,
                  region_name = REGION)

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
    
    if not category_masks:
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
    file_name = f"{base_name}{random.randint(0, 10**10)}_{category}{ext}"
    local_path = os.path.join(HOME, file_name)

    # Save the image locally
    cv2.imwrite(local_path, image)

    try:

        # S3 내 저장 경로 정의
        s3_key = f"segmented_img/{file_name}"

        # Content-Type 설정 (이미지 파일에 적합한 타입 설정)
        content_type = "image/jpeg" if ext.lower() in [".jpg", ".jpeg"] else "image/png"

        # 파일을 S3에 업로드하면서 Content-Type 설정
        s3.upload_file(
            Filename=local_path,
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            ExtraArgs={"ContentType": content_type}
        )

        # S3 URL 생성 (퍼블릭 URL 사용, 버킷이 퍼블릭이거나 정책에 따라 다름)
        s3_url = f"https://{S3_BUCKET_NAME}.s3.{REGION}.amazonaws.com/{s3_key}"

        # 로컬 파일 삭제 (클린업)
        os.remove(local_path)

        return s3_url
    
    except Exception as e:
        # 에러 처리
        print(f"Failed to upload {file_name} to S3: {e}")
        if os.path.exists(local_path):
            os.remove(local_path)  # 로컬 파일 정리
        return None