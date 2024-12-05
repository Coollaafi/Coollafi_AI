# Step 1: Base image
FROM wot_ai_server:python3.10

# Step 2: Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV TZ=Asia/Seoul

# Step 3: Set working directory
WORKDIR /app

# Step 4: Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    python3-dev \
    gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Step 5: Copy and install Python dependencies
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install git+https://github.com/facebookresearch/segment-anything.git && \
    pip install pycocotools

# Step 6: Copy application files
COPY . .

# Step 7: Expose the application port
EXPOSE 8000

# step 8: weights 폴더 생성하고, GroundingDINO, sam 모델 path 다운로드
#RUN mkdir -p weights && \
#    curl -L "https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth" -o "weights/groundingdino_swint_ogc.pth" && \
#    curl -L "https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth" -o "weights/sam_vit_h_4b8939.pth"

# Step 9: Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]