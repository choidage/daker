'use client';

import { useEffect, useRef, useCallback, useState } from 'react';

type WSMessage = {
  type: string;
  data?: unknown;
  timestamp?: string;
};

type WSHandler = (msg: WSMessage) => void;

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000/ws';
const RECONNECT_DELAY_MS = 3000;

export function useWebSocket(onMessage: WSHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<'connecting' | 'live' | 'reconnecting'>('connecting');

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);

    ws.onopen = () => setStatus('live');

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data) as WSMessage;
        onMessage(msg);
      } catch { /* ignore parse errors */ }
    };

    ws.onclose = () => {
      setStatus('reconnecting');
      setTimeout(connect, RECONNECT_DELAY_MS);
    };

    ws.onerror = () => ws.close();

    wsRef.current = ws;
  }, [onMessage]);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  const send = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  return { status, send };
}
