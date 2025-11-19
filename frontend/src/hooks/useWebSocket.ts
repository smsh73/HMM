import { useEffect, useRef, useState } from 'react';

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export const useWebSocket = (url: string) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // 토큰 가져오기
  const getToken = () => {
    return localStorage.getItem('token') || '';
  };

  useEffect(() => {
    const connect = () => {
      try {
        // WebSocket URL 구성
        const wsUrl = url.replace('http://', 'ws://').replace('https://', 'wss://');
        const token = getToken();
        const ws = new WebSocket(`${wsUrl}?token=${token || ''}`);
        
        ws.onopen = () => {
          setIsConnected(true);
          console.log('WebSocket 연결됨');
          
          // 재연결 타이머 초기화
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
            reconnectTimeoutRef.current = null;
          }
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            setLastMessage(message);
          } catch (e) {
            console.error('WebSocket 메시지 파싱 실패:', e);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket 오류:', error);
        };

        ws.onclose = () => {
          setIsConnected(false);
          console.log('WebSocket 연결 종료');
          
          // 재연결 시도 (5초 후)
          if (!reconnectTimeoutRef.current) {
            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectTimeoutRef.current = null;
              connect();
            }, 5000);
          }
        };

        wsRef.current = ws;
      } catch (error) {
        console.error('WebSocket 연결 실패:', error);
      }
    };

        connect();

    return () => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
        }
    };
  }, [url]);

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return { isConnected, lastMessage, sendMessage };
};

