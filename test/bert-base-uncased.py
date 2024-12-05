from transformers import BertModel

# 다운로드 경로 설정
local_model_path = "C:/Users/user/Desktop/WOT/grounded-sam/weights"  # 원하는 로컬 디렉토리 경로

# 모델 다운로드 및 저장
model = BertModel.from_pretrained("bert-base-uncased")
model.save_pretrained(local_model_path)

print(f"Model downloaded and saved to {local_model_path}")