# 개인화된 AI를 통해, 날씨에 맞는 맞춤형 옷을 추천해주는 소셜 네트워크 서비스, WOT 👔
날씨가 생각보다 더워서, 혹은 추워서 입은 옷을 후회한 적이 있지 않나요?<br />
매일 OOTD를 기록하고 싶은데, SNS에 올리기엔 부담스럽지 않나요?<br />
<br />
이에, 저희는 개인화된 AI를 통해, 오늘의 날씨에 맞는 여러분의 옷을 추천하고,<br />
친한 친구 20명과 함께하는 SNS를 제공하는 서비스, <b>왓(wot)</b>을 기획하였습니다.<br />
###### 배포사이트: https://coollaafi-frontend.vercel.app/
###### 데모 영상: https://www.youtube.com/watch?v=RDpbWE1proI&t=5s
<hr/>
<div align="center"><img src="https://github.com/user-attachments/assets/a32cacb5-bb23-4893-bc99-3189098ba3b3" width="100%"></div>
<hr/>

### ⚙️기술 스택
<b>[Frontend]</b><br/>
<img src="https://img.shields.io/badge/html5-E34F26?style=for-the-badge&logo=html5&logoColor=white"><img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=React&logoColor=white"><img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=TypeScript&logoColor=white"><img src="https://img.shields.io/badge/CSS-1572B6?style=for-the-badge&logo=CSS&logoColor=white">
<br/><br/><b>[Backend]</b><br>
<img src="https://img.shields.io/badge/springboot-6DB33F?style=for-the-badge&logo=springboot&logoColor=white"><img src="https://img.shields.io/badge/Amazon%20EC2-FF9900?style=for-the-badge&logo=Amazon%20EC2&logoColor=white"><img src="https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white"><img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=MySQL&logoColor=white">
<br><br><b>[AI]</b><br/>
<img src="https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=TensorFlow&logoColor=white"><img src="https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=PyTorch&logoColor=white"><img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=Flask&logoColor=white">

<hr/>

### ⚙️실행 방법
### How to install
1. **Python 3.10** 설치
    - 3.9와 3.10의 버전만 유효합니다.

2. **MySQL 데이터베이스**
    - MySQL 8.0 이상이 설치되어있어야 합니다.
    - 사용할 DB를 생성하여 DB에 접근하기 위한 정보들을 환경변수에 저장합니다.

3. **AWS S3 설정**
    - 이미지 저장을 위해 S3 버킷이 필요합니다.
    - AWS Access Key와 Secret Key를 발급받아 환경변수에 저장합니다.

### How to build
**1. Repository Clone**
   ```bash
   git clone <repository-url>
   cd <project-directory>
```
**2. Add Environment Variables**
<br>**.env 파일**을 프로젝트 루트 디렉토리에 추가한 후, 아래 내용을 작성합니다.
   ```bash
   DB_HOST=(sql host 이름)
   DB_PORT=(sql port 번호)
   DB_NAME=(sql 데이터베이스 이름)
   DB_USER=(sql 유저 이름)
   DB_PASSWORD=(sql에서 발급받은 패스워드)

   S3_BUCKET_NAME=(s3 bucket 이름)
   REGION=(s3 bucket의 region)
   ACCESS_KEY=(aws s3에서 발급받은 access key)
   SECRET_KEY=(aws s3에서 발급받은 secret key)
```
### How to run in local
1. 프로젝트 루트 디렉토리에 있는 server.py
   - cmd 또는 터미널에서 server.py 파일이 저장되어 있는 위치로 이동합니다.
   ```bash
   cmd <server.py-directory>
   ```
2. 로컬에서 FastAPI 서버를 여는 uvicorn 명령어를 실행합니다.
   ```bash
   uvicorn server:app --reload --host 127.0.0.1 --port 8000
   ```
   - uvicorn 명령어를 실행하기 전 각 환경변수에 맞는 값을 입력해야 합니다.

3. MySQL 데이터베이스 시작

5. swagger 문서 페이지에 접근
   - 브라우저를 열어 url 주소창에 http://127.0.0.1:8000/docs 를 입력합니다.
   - 이 페이지에서는 모든 API 엔드포인트를 확인하고, 직접 요청을 테스트해볼 수 있습니다.
   
### 사용한 오픈소스 정보
- Grounded-SAM: [자연어 기반 이미지 세그먼트 모델](https://axios-http.com/kr/docs/intro)
- Impaint Anything: [자연어 기반 특정 부분 채워넣는 이미지 보정 모델](https://tanstack.com/query/v5/docs/framework/react/overview)

<hr/>
  
### 👩‍💻팀원 소개
  <table >
    <tr>
      <td align="center"><b>Frontend</b></td>
      <td align="center"><b>Backend</b></td>
      <td align="center"><b>AI</b></td>
    </tr>
    <tr>
      <td align="center"><img src="https://avatars.githubusercontent.com/u/88073842?s=400&u=bc39f4c6820808f5c034dc5e210f7ea279bff43c&v=4" width="130"></td>
      <td align="center"><img src="https://avatars.githubusercontent.com/u/52813483?v=4" width="130"></td>
      <td align="center" ><img src="https://avatars.githubusercontent.com/u/137473567?v=4" width="130" borderRadius="100%"></td>
    </tr>
    <tr>
      <td align="center"><a href="https://github.com/sujinRo" target="_blank" width="160">sujinRo</a></td>
      <td align="center"><a href="https://github.com/ujiiin" target="_blank">ujiiin</a></td>
      <td align="center"><a href="https://github.com/Choi-Hanui" target="_blank">Choi-Hanui</a></td>
    </tr>
  </table>
