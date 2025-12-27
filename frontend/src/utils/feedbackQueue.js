const FEEDBACK_QUEUE_KEY = 'malaya:feedback-queue';
const MAX_QUEUE = 200;

const loadQueue = () => {
    if (typeof window === 'undefined') return [];
    try {
        const raw = window.localStorage.getItem(FEEDBACK_QUEUE_KEY);
        const parsed = JSON.parse(raw || '[]');
        return Array.isArray(parsed) ? parsed : [];
    } catch {
        return [];
    }
};

const saveQueue = (queue) => {
    if (typeof window === 'undefined') return;
    window.localStorage.setItem(FEEDBACK_QUEUE_KEY, JSON.stringify(queue.slice(0, MAX_QUEUE)));
};

export const enqueueFeedback = (payload) => {
    const queue = loadQueue();
    queue.unshift({ ...payload, queued_at: new Date().toISOString() });
    saveQueue(queue);
};

export const flushFeedbackQueue = async () => {
    if (typeof navigator !== 'undefined' && navigator.onLine === false) return;
    const queue = loadQueue();
    if (queue.length === 0) return;
    const endpoint = '/api/chat/feedback';
    const apiKey = import.meta.env.VITE_API_KEY;
    const remaining = [];
    for (const item of queue) {
        try {
            await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(apiKey ? { 'X-API-Key': apiKey } : {}),
                },
                body: JSON.stringify(item),
            });
        } catch {
            remaining.push(item);
        }
    }
    saveQueue(remaining);
};
