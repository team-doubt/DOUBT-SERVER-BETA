import socketio
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import logging
from typing import Dict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO 서버 생성
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")

# FastAPI 앱 생성
app = FastAPI(title="DOUBT Chat Server", description="5명의 수학자 채팅방")

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


async def get_chat_page():
    """채팅 페이지 HTML 반환"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DOUBT 채팅방 - 수학자들의 모임</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            width: 90%;
            max-width: 800px;
            height: 80%;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            margin-bottom: 5px;
        }
        
        .user-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        
        .current-user {
            font-weight: bold;
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
        }
        
        .online-count {
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 70%;
            word-wrap: break-word;
        }
        
        .message.own {
            background: #4CAF50;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .message.other {
            background: white;
            border: 1px solid #ddd;
        }
        
        .message.system {
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            text-align: center;
            margin: 10px auto;
            max-width: 80%;
            font-style: italic;
            color: #1976d2;
        }
        
        .message-sender {
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }
        
        .message.own .message-sender {
            color: #e8f5e8;
        }
        
        .message-time {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
            display: flex;
            gap: 10px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input:focus {
            border-color: #4CAF50;
        }
        
        .send-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        
        .send-button:hover {
            background: #45a049;
        }
        
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .status {
            text-align: center;
            padding: 10px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            margin: 10px;
            border-radius: 5px;
        }
        
        .error {
            background: #f8d7da;
            border-color: #f5c6cb;
            color: #721c24;
        }
        
        .success {
            background: #d4edda;
            border-color: #c3e6cb;
            color: #155724;
        }
        
        .user-list {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        .user-list h3 {
            margin-bottom: 5px;
            font-size: 14px;
        }
        
        .users {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .user-tag {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
        }
        
        @media (max-width: 600px) {
            .chat-container {
                width: 100%;
                height: 100%;
                border-radius: 0;
            }
            
            .message {
                max-width: 85%;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🧮 DOUBT 채팅방</h1>
            <p>수학자들의 모임</p>
            <div class="user-info">
                <div class="current-user" id="currentUser">연결 중...</div>
                <div class="online-count" id="onlineCount">접속자: 0명</div>
            </div>
            <div class="user-list" id="userList" style="display: none;">
                <h3>현재 접속자:</h3>
                <div class="users" id="users"></div>
            </div>
        </div>
        
        <div class="chat-messages" id="messages"></div>
        
        <div class="chat-input-container">
            <input type="text" id="messageInput" class="chat-input" placeholder="메시지를 입력하세요..." disabled>
            <button id="sendButton" class="send-button" disabled>전송</button>
        </div>
    </div>

    <script>
        let ws = null;
        let currentUserName = '';
        let isConnected = false;
        
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const currentUserDiv = document.getElementById('currentUser');
        const onlineCountDiv = document.getElementById('onlineCount');
        const userListDiv = document.getElementById('userList');
        const usersDiv = document.getElementById('users');
        
        function connect() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function(event) {
                console.log('WebSocket 연결됨');
                addSystemMessage('서버에 연결 중...');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function(event) {
                console.log('WebSocket 연결 끊어짐');
                isConnected = false;
                messageInput.disabled = true;
                sendButton.disabled = true;
                currentUserDiv.textContent = '연결 끊어짐';
                addSystemMessage('연결이 끊어졌습니다. 새로고침해주세요.');
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket 오류:', error);
                addSystemMessage('연결 오류가 발생했습니다.');
            };
        }
        
        function handleMessage(data) {
            switch(data.type) {
                case 'connected':
                    currentUserName = data.name;
                    currentUserDiv.textContent = `${data.name}으로 접속`;
                    isConnected = true;
                    messageInput.disabled = false;
                    sendButton.disabled = false;
                    messageInput.focus();
                    addSystemMessage(data.message, 'success');
                    break;
                    
                case 'error':
                    addSystemMessage(data.message, 'error');
                    break;
                    
                case 'chat':
                    addChatMessage(data.name, data.message, data.timestamp, false);
                    break;
                    
                case 'user_joined':
                case 'user_left':
                    addSystemMessage(data.message);
                    break;
                    
                case 'user_list':
                    updateUserList(data.users, data.count);
                    break;
            }
        }
        
        function addSystemMessage(message, type = '') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message system ${type}`;
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function addChatMessage(sender, message, timestamp, isOwn) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isOwn ? 'own' : 'other'}`;
            
            const senderDiv = document.createElement('div');
            senderDiv.className = 'message-sender';
            senderDiv.textContent = sender;
            
            const contentDiv = document.createElement('div');
            contentDiv.textContent = message;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date(timestamp * 1000).toLocaleTimeString();
            
            if (!isOwn) {
                messageDiv.appendChild(senderDiv);
            }
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function updateUserList(users, count) {
            onlineCountDiv.textContent = `접속자: ${count}명`;
            
            if (count > 0) {
                userListDiv.style.display = 'block';
                usersDiv.innerHTML = '';
                users.forEach(user => {
                    const userTag = document.createElement('span');
                    userTag.className = 'user-tag';
                    userTag.textContent = user;
                    if (user === currentUserName) {
                        userTag.style.background = 'rgba(255,255,255,0.4)';
                    }
                    usersDiv.appendChild(userTag);
                });
            } else {
                userListDiv.style.display = 'none';
            }
        }
        
        function sendMessage() {
            if (!isConnected || !messageInput.value.trim()) return;
            
            const message = messageInput.value.trim();
            const timestamp = Date.now() / 1000;
            
            // 내 메시지 즉시 표시
            addChatMessage(currentUserName, message, timestamp, true);
            
            // 서버로 전송
            ws.send(JSON.stringify({
                type: 'chat',
                message: message,
                timestamp: timestamp
            }));
            
            messageInput.value = '';
        }
        
        function scrollToBottom() {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 이벤트 리스너
        sendButton.onclick = sendMessage;
        
        messageInput.onkeypress = function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        };
        
        // 페이지 로드 시 연결
        window.onload = function() {
            connect();
        };
        
        // 페이지 언로드 시 연결 종료
        window.onbeforeunload = function() {
            if (ws) {
                ws.close();
            }
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """채팅 페이지 HTML 반환"""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>DOUBT 채팅방 - 수학자들의 모임</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .chat-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            width: 90%;
            max-width: 800px;
            height: 80%;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .chat-header {
            background: linear-gradient(90deg, #4CAF50, #45a049);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .chat-header h1 {
            margin-bottom: 5px;
        }
        
        .user-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }
        
        .current-user {
            font-weight: bold;
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
        }
        
        .online-count {
            background: rgba(255,255,255,0.2);
            padding: 5px 10px;
            border-radius: 15px;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 70%;
            word-wrap: break-word;
        }
        
        .message.own {
            background: #4CAF50;
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .message.other {
            background: white;
            border: 1px solid #ddd;
        }
        
        .message.system {
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            text-align: center;
            margin: 10px auto;
            max-width: 80%;
            font-style: italic;
            color: #1976d2;
        }
        
        .message-sender {
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }
        
        .message.own .message-sender {
            color: #e8f5e8;
        }
        
        .message-time {
            font-size: 0.8em;
            opacity: 0.7;
            margin-top: 5px;
        }
        
        .chat-input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #ddd;
            display: flex;
            gap: 10px;
        }
        
        .chat-input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .chat-input:focus {
            border-color: #4CAF50;
        }
        
        .send-button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s;
        }
        
        .send-button:hover {
            background: #45a049;
        }
        
        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        
        .user-list {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
        }
        
        .user-list h3 {
            margin-bottom: 5px;
            font-size: 14px;
        }
        
        .users {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .user-tag {
            background: rgba(255,255,255,0.2);
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🧮 DOUBT 채팅방</h1>
            <p>수학자들의 모임</p>
            <div class="user-info">
                <div class="current-user" id="currentUser">연결 중...</div>
                <div class="online-count" id="onlineCount">접속자: 0명</div>
            </div>
            <div class="user-list" id="userList" style="display: none;">
                <h3>현재 접속자:</h3>
                <div class="users" id="users"></div>
            </div>
        </div>
        
        <div class="chat-messages" id="messages"></div>
        
        <div class="chat-input-container">
            <input type="text" id="messageInput" class="chat-input" placeholder="메시지를 입력하세요..." disabled>
            <button id="sendButton" class="send-button" disabled>전송</button>
        </div>
    </div>

    <script>
        let socket = io();
        let currentUserName = '';
        let isConnected = false;
        
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const currentUserDiv = document.getElementById('currentUser');
        const onlineCountDiv = document.getElementById('onlineCount');
        const userListDiv = document.getElementById('userList');
        const usersDiv = document.getElementById('users');
        
        // Socket.IO 이벤트 리스너들
        socket.on('connected', function(data) {
            currentUserName = data.name;
            currentUserDiv.textContent = `${data.name}으로 접속`;
            isConnected = true;
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
            addSystemMessage(data.message, 'success');
        });
        
        socket.on('error', function(data) {
            addSystemMessage(data.message, 'error');
        });
        
        socket.on('chat', function(data) {
            addChatMessage(data.name, data.message, data.timestamp, false);
        });
        
        socket.on('user_joined', function(data) {
            addSystemMessage(data.message);
        });
        
        socket.on('user_left', function(data) {
            addSystemMessage(data.message);
        });
        
        socket.on('user_list', function(data) {
            updateUserList(data.users, data.count);
        });
        
        socket.on('disconnect', function() {
            isConnected = false;
            messageInput.disabled = true;
            sendButton.disabled = true;
            currentUserDiv.textContent = '연결 끊어짐';
            addSystemMessage('연결이 끊어졌습니다.');
        });
        
        function addSystemMessage(message, type = '') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message system ${type}`;
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function addChatMessage(sender, message, timestamp, isOwn) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isOwn ? 'own' : 'other'}`;
            
            const senderDiv = document.createElement('div');
            senderDiv.className = 'message-sender';
            senderDiv.textContent = sender;
            
            const contentDiv = document.createElement('div');
            contentDiv.textContent = message;
            
            const timeDiv = document.createElement('div');
            timeDiv.className = 'message-time';
            timeDiv.textContent = new Date(timestamp * 1000).toLocaleTimeString();
            
            if (!isOwn) {
                messageDiv.appendChild(senderDiv);
            }
            messageDiv.appendChild(contentDiv);
            messageDiv.appendChild(timeDiv);
            
            messagesDiv.appendChild(messageDiv);
            scrollToBottom();
        }
        
        function updateUserList(users, count) {
            onlineCountDiv.textContent = `접속자: ${count}명`;
            
            if (count > 0) {
                userListDiv.style.display = 'block';
                usersDiv.innerHTML = '';
                users.forEach(user => {
                    const userTag = document.createElement('span');
                    userTag.className = 'user-tag';
                    userTag.textContent = user;
                    if (user === currentUserName) {
                        userTag.style.background = 'rgba(255,255,255,0.4)';
                    }
                    usersDiv.appendChild(userTag);
                });
            } else {
                userListDiv.style.display = 'none';
            }
        }
        
        function sendMessage() {
            if (!isConnected || !messageInput.value.trim()) return;
            
            const message = messageInput.value.trim();
            const timestamp = Date.now() / 1000;
            
            // 내 메시지 즉시 표시
            addChatMessage(currentUserName, message, timestamp, true);
            
            // 서버로 전송
            socket.emit('chat_message', {
                message: message,
                timestamp: timestamp
            });
            
            messageInput.value = '';
        }
        
        function scrollToBottom() {
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // 이벤트 리스너
        sendButton.onclick = sendMessage;
        
        messageInput.onkeypress = function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        };
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


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
