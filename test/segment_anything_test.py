from segment_anything import sam_model_registry

# 파일 경로 지정
model_checkpoint_path = "C:/Users/user/Desktop/WOT/grounded-sam/weights/sam_vit_h_4b8939.pth"

# 모델 로드
try:
    sam = sam_model_registry["vit_h"](checkpoint=model_checkpoint_path)
    print("Model successfully loaded!")
except Exception as e:
    print(f"Error loading model: {e}")