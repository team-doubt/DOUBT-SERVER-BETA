# 🧮 DOUBT 채팅 서버

5명의 수학자들이 모이는 실시간 채팅방입니다.

## ✨ 특징

- **최대 5명 동시 접속**: 튜링, 노이만, 가우스, 오일러, 파스칼
- **Socket.IO 기반**: 실시간 양방향 통신
- **자동 이름 배정**: 접속 순서대로 수학자 이름 자동 할당
- **실시간 알림**: 사용자 입장/퇴장, 접속자 목록 업데이트
- **반응형 UI**: 모바일/데스크톱 모두 지원

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
uv sync
```

### 2. 서버 실행

```bash
# 실행 스크립트 사용
./run.sh

# 또는 직접 실행
python main.py
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
