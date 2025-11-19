"""
WebSocket 관리자
실시간 이벤트 브로드캐스팅
"""
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from app.core.logging import logger
import json


class WebSocketManager:
    """WebSocket 연결 관리자"""
    
    def __init__(self):
        """WebSocket 관리자 초기화"""
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> connections
    
    async def connect(self, websocket: WebSocket, user_id: str = None):
        """WebSocket 연결"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        
        logger.info(f"WebSocket 연결: {len(self.active_connections)}개 활성 연결")
    
    def disconnect(self, websocket: WebSocket, user_id: str = None):
        """WebSocket 연결 해제"""
        self.active_connections.discard(websocket)
        
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket 연결 해제: {len(self.active_connections)}개 활성 연결")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """개인 메시지 전송"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"WebSocket 메시지 전송 실패: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """모든 연결에 브로드캐스트"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"브로드캐스트 실패: {e}")
                disconnected.add(connection)
        
        # 연결 해제된 소켓 제거
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_user(self, user_id: str, message: Dict[str, Any]):
        """특정 사용자에게 메시지 전송"""
        if user_id not in self.user_connections:
            return
        
        disconnected = set()
        for connection in self.user_connections[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"사용자 메시지 전송 실패: {e}")
                disconnected.add(connection)
        
        # 연결 해제된 소켓 제거
        for connection in disconnected:
            self.disconnect(connection, user_id)


# 전역 WebSocket 관리자 인스턴스
websocket_manager = WebSocketManager()

