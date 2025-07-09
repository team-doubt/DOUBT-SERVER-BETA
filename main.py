import socketio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from typing import Dict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO 서버 생성
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# FastAPI 앱 생성
app = FastAPI(title="DOUBT Chat Server", description="5명의 수학자 채팅방")

# CORS 전체 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO와 FastAPI 결합
socket_app = socketio.ASGIApp(sio, app)

# 수학자 이름들
MATHEMATICIAN_NAMES = ["튜링", "노이만", "가우스", "오일러", "파스칼"]

# 간단한 상태 관리
users: Dict[str, str] = {}  # session_id -> username
available_names = MATHEMATICIAN_NAMES.copy()


# Socket.IO 이벤트 핸들러들
@sio.event
async def connect(sid, environ):
    """클라이언트 연결 시"""
    logger.info(f"클라이언트 연결: {sid}")

    # 사용 가능한 이름이 있는지 확인
    if not available_names:
        await sio.emit('error', {'message': '채팅방이 가득 찼습니다. (최대 5명)'}, room=sid)
        await sio.disconnect(sid)
        return

    # 이름 배정
    username = available_names.pop(0)
    users[sid] = username

    # 연결 성공 알림
    await sio.emit('connected', {
        'name': username,
        'message': f'{username}으로 연결되었습니다!'
    }, room=sid)

    # 다른 사용자들에게 입장 알림
    await sio.emit('user_joined', {
        'name': username,
        'message': f'{username}님이 채팅방에 입장했습니다.'
    }, skip_sid=sid)

    # 모든 사용자에게 접속자 목록 업데이트
    await update_user_list()

    logger.info(f"사용자 {username} 연결됨")


@sio.event
async def disconnect(sid):
    """클라이언트 연결 해제 시"""
    if sid in users:
        username = users[sid]
        del users[sid]
        available_names.append(username)
        available_names.sort(key=lambda x: MATHEMATICIAN_NAMES.index(x))

        # 퇴장 알림
        await sio.emit('user_left', {
            'name': username,
            'message': f'{username}님이 채팅방을 나갔습니다.'
        })

        # 접속자 목록 업데이트
        await update_user_list()

        logger.info(f"사용자 {username} 연결 해제됨")


@sio.event
async def chat_message(sid, data):
    """채팅 메시지 처리"""
    if sid not in users:
        return

    username = users[sid]
    message = data.get('message', '')

    if message.strip():
        # 모든 사용자에게 메시지 브로드캐스트 (발신자 제외)
        await sio.emit('chat', {
            'name': username,
            'message': message,
            'timestamp': data.get('timestamp')
        }, skip_sid=sid)

        logger.info(f"채팅 메시지 - {username}: {message}")


async def update_user_list():
    """접속자 목록 업데이트"""
    user_list = list(users.values())
    await sio.emit('user_list', {
        'users': user_list,
        'count': len(user_list)
    })


@app.get("/api/status")
async def get_status():
    """서버 상태 API"""
    return {
        "status": "running",
        "connected_users": len(users),
        "available_slots": len(available_names),
        "users": list(users.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
