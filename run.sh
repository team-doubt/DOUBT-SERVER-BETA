#!/bin/bash

# DOUBT 채팅 서버 시작 스크립트

echo "🧮 DOUBT 채팅 서버를 시작합니다..."
echo "수학자들의 모임에 오신 것을 환영합니다!"
echo ""
echo "접속 가능한 수학자:"
echo "- 튜링 (Alan Turing)"
echo "- 노이만 (John von Neumann)"
echo "- 가우스 (Carl Friedrich Gauss)"  
echo "- 오일러 (Leonhard Euler)"
echo "- 파스칼 (Blaise Pascal)"
echo ""
echo "서버 시작 중..."
echo "📡 Socket.IO 서버가 http://localhost:8000 에서 실행됩니다"
echo ""

uv run python -m src.doubt_server_beta.main
