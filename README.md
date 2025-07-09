# 🧮 DOUBT 채팅 서버

5명의 수학자들이 모이는 실시간 채팅방입니다.

## ✨ 특징

- **최대 5명 동시 접속**: 튜링, 노이만, 가우스, 오일러, 파스칼
- **Socket.IO 기반**: 실시간 양방향 통신
- **자동 이름 배정**: 접속 순서대로 수학자 이름 자동 할당
- **실시간 알림**: 사용자 입장/퇴장, 접속자 목록 업데이트
- **반응형 UI**: 모바일/데스크톱 모두 지원

## 🚀 빠른 시작

### 0. 환경 설정 (우분투/Ubuntu)

```bash
# Python 설치
sudo apt update
sudo apt install python3 python3-pip

# UV 설치 (Python 패키지 매니저)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 또는 pip로 UV 설치
pip install uv
```

### 1. 의존성 설치

### 1. 의존성 설치

```bash
# UV 사용 (권장)
uv sync

# 또는 pip 사용
pip install -r requirements.txt
```

### 2. 서버 실행

```bash
# UV 사용 (권장)
uv run python main.py

# 또는 직접 실행
python3 main.py

# 백그라운드 실행
nohup python3 main.py &
```

### 3. 브라우저에서 접속

```
http://localhost:8000
```

## 🛠 기술 스택

- **백엔드**: FastAPI + Socket.IO
- **프론트엔드**: HTML + CSS + JavaScript (Socket.IO 클라이언트)
- **패키지 관리**: UV

## 📡 API 엔드포인트

- `GET /`: 채팅 페이지
- `GET /api/status`: 서버 상태 확인

## 🎯 Socket.IO 이벤트

### 클라이언트 → 서버

- `chat_message`: 채팅 메시지 전송

### 서버 → 클라이언트

- `connected`: 연결 성공
- `error`: 오류 발생
- `chat`: 채팅 메시지 수신
- `user_joined`: 사용자 입장
- `user_left`: 사용자 퇴장
- `user_list`: 접속자 목록 업데이트

## 📝 라이센스

MIT License
