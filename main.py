import socketio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import httpx
import asyncio
import random
from typing import Dict, List

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

# 수학자 구분
HUMAN_MATHEMATICIANS = ["튜링", "오일러", "파스칼"]  # 인간이 사용할 수 있는 수학자
AI_MATHEMATICIANS = ["노이만", "가우스"]  # AI가 자동으로 응답하는 수학자
ALL_MATHEMATICIANS = HUMAN_MATHEMATICIANS + AI_MATHEMATICIANS

# AI API 설정
AI_API_URL = "http://10.150.150.147:8000/api/chat"

# 간단한 상태 관리
users: Dict[str, str] = {}  # session_id -> username
available_human_names = HUMAN_MATHEMATICIANS.copy()
ai_users: Dict[str, str] = {}  # AI 수학자들 (name -> personality)
chat_history: List[Dict] = []  # 채팅 기록 저장

# AI 수학자들 초기화
for ai_name in AI_MATHEMATICIANS:
    ai_users[ai_name] = ai_name


# Socket.IO 이벤트 핸들러들
@sio.event
async def connect(sid, environ):
    """클라이언트 연결 시"""
    logger.info(f"클라이언트 연결: {sid}")

    # 사용 가능한 인간 수학자 이름이 있는지 확인
    if not available_human_names:
        await sio.emit('error', {'message': '채팅방이 가득 찼습니다. (최대 3명의 인간 사용자)'}, room=sid)
        await sio.disconnect(sid)
        return

    # 인간 사용자에게 이름 배정
    username = available_human_names.pop(0)
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
        available_human_names.append(username)
        available_human_names.sort(key=lambda x: HUMAN_MATHEMATICIANS.index(x))

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
        # 채팅 기록에 추가
        chat_entry = {
            'name': username,
            'message': message,
            'timestamp': data.get('timestamp')
        }
        chat_history.append(chat_entry)

        # 최근 20개 메시지만 유지
        if len(chat_history) > 20:
            chat_history.pop(0)

        # 모든 사용자에게 메시지 브로드캐스트 (발신자 제외)
        await sio.emit('chat', chat_entry, skip_sid=sid)

        logger.info(f"채팅 메시지 - {username}: {message}")

        # AI 응답 트리거 (30% 확률로 AI가 응답)
        if random.random() < 0.8:
            await trigger_ai_response()


async def trigger_ai_response():
    """AI 수학자의 자동 응답 트리거"""
    if not chat_history:
        return

    # 랜덤하게 AI 수학자 선택
    ai_name = random.choice(AI_MATHEMATICIANS)

    # AI에게 보낼 채팅 기록 준비
    recent_messages = chat_history[-5:]  # 최근 5개 메시지
    conversation_context = "\n".join(
        [f"{msg['name']}: {msg['message']}" for msg in recent_messages])

    # AI API 호출
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            ai_request = {
                "model": "exaone3.5:7.8b",
                "messages": [
                    {
                        "role": "system",
                        "content": f"당신은 {ai_name}입니다. 인공지능임을 들키지 말것. SNS 말투로 말할 것. 답변은 7자 이내로. 수학자답게 가끔 수학 관련 얘기도 하세요."
                    },
                    {
                        "role": "user",
                        "content": f"다음은 최근 채팅 내용입니다:\n{conversation_context}\n\n자연스럽게 대화에 참여해주세요."
                    }
                ],
                "stream": False
            }

            response = await client.post(AI_API_URL, json=ai_request)
            if response.status_code == 200:
                ai_response = response.json()
                ai_message = ai_response.get(
                    'message', {}).get('content', '...')

                # AI 응답을 채팅에 추가
                ai_chat_entry = {
                    'name': ai_name,
                    'message': ai_message,
                    'timestamp': None
                }
                chat_history.append(ai_chat_entry)

                # 모든 사용자에게 AI 메시지 브로드캐스트
                await sio.emit('chat', ai_chat_entry)

                logger.info(f"AI 응답 - {ai_name}: {ai_message}")
    except Exception as e:
        logger.error(f"AI 응답 생성 실패: {e}")


async def update_user_list():
    """접속자 목록 업데이트"""
    # 인간 사용자 + AI 사용자
    all_active_users = list(users.values()) + list(ai_users.keys())
    await sio.emit('user_list', {
        'users': all_active_users,
        'count': len(all_active_users),
        'human_users': list(users.values()),
        'ai_users': list(ai_users.keys())
    })


@app.get("/api/status")
async def get_status():
    """서버 상태 API"""
    return {
        "status": "running",
        "connected_human_users": len(users),
        "available_human_slots": len(available_human_names),
        "human_users": list(users.values()),
        "ai_users": list(ai_users.keys()),
        "total_active_users": len(users) + len(ai_users)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
