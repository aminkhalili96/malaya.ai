const QUEUE_KEY = 'malaya:analytics-queue';
const MAX_QUEUE = 200;

const loadQueue = () => {
    if (typeof window === 'undefined') return [];
    try {
        const raw = window.localStorage.getItem(QUEUE_KEY);
        const parsed = JSON.parse(raw || '[]');
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
};

const saveQueue = (queue) => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(QUEUE_KEY, JSON.stringify(queue.slice(0, MAX_QUEUE)));
};

const enqueueEvent = (event) => {
    const queue = loadQueue();
    queue.unshift(event);
    saveQueue(queue);
};

const sendEvent = async (event) => {
    const endpoint = '/api/chat/analytics';
    const apiKey = import.meta.env.VITE_API_KEY;
    await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(apiKey ? { 'X-API-Key': apiKey } : {}) },
        body: JSON.stringify(event),
        keepalive: true,
    });
};

export const flushAnalyticsQueue = async () => {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return;
    const queue = loadQueue();
    if (queue.length === 0) return;
    const remaining = [];
    for (const event of queue) {
        try {
            await sendEvent(event);
        } catch {
            remaining.push(event);
        }
    }
    saveQueue(remaining);
};

export const trackEvent = (name, payload = {}) => {
    if (!name) return;
    if (import.meta.env.VITE_ANALYTICS_DISABLED === 'true') return;

    const event = {
        name,
        payload,
        timestamp: new Date().toISOString(),
    };

    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
        enqueueEvent(event);
        return;
    }

    if (navigator.sendBeacon) {
        const body = JSON.stringify(event);
        const blob = new Blob([body], { type: 'application/json' });
        if (import.meta.env.VITE_API_KEY) {
            sendEvent(event).catch(() => enqueueEvent(event));
            return;
        }
        const ok = navigator.sendBeacon('/api/chat/analytics', blob);
        if (!ok) enqueueEvent(event);
        return;
    }

    sendEvent(event).catch(() => enqueueEvent(event));
};
