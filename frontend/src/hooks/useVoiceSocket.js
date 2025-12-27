import { useRef, useEffect, useCallback } from 'react';
import useStore from '../store/useStore';

const WS_URL = 'ws://localhost:8000/ws/voice'; // TODO: Make env var

export const useVoiceSocket = (clientId) => {
    const socketRef = useRef(null);
    const { addMessage, isVoiceMode, setListening } = useStore();

    const connect = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) return;

        const ws = new WebSocket(`${WS_URL}/${clientId}`);

        ws.onopen = () => {
            console.log('Voice Socket connected');
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === 'responded') {
                // Add AI response to chat
                addMessage({
                    role: 'assistant',
                    content: data.text,
                    isVoice: true
                });
                // TODO: Play audio_base64 here
                setListening(true); // Ready for next input
            }
        };

        ws.onclose = () => {
            console.log('Voice Socket disconnected');
        };

        socketRef.current = ws;
    }, [clientId, addMessage, setListening]);

    const sendVoiceMessage = useCallback((text) => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
            setListening(false); // Processing...
            socketRef.current.send(text); // In real app, send blob
        }
    }, [setListening]);

    useEffect(() => {
        if (isVoiceMode) {
            connect();
        } else {
            socketRef.current?.close();
        }
        return () => socketRef.current?.close();
    }, [isVoiceMode, connect]);

    return { sendVoiceMessage };
};
