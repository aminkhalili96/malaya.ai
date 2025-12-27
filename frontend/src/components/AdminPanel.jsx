import React, { useEffect, useState } from 'react';
import { X } from 'lucide-react';
import clsx from 'clsx';

const API_KEY = import.meta.env.VITE_API_KEY;

const fetchJson = async (url, options = {}) => {
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
            ...(options.headers || {}),
        },
    });
    if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`);
    }
    return res.json();
};

const AdminPanel = ({ open, onClose }) => {
    const [summary, setSummary] = useState(null);
    const [config, setConfig] = useState(null);
    const [feedback, setFeedback] = useState(null);
    const [error, setError] = useState('');
    const [rateDraft, setRateDraft] = useState({});
    const [keyDraft, setKeyDraft] = useState({ key: '', role: 'admin', limits: {} });

    useEffect(() => {
        if (!open) return;
        const load = async () => {
            try {
                setError('');
                const [summaryData, configData, feedbackData] = await Promise.all([
                    fetchJson('/api/chat/admin/summary'),
                    fetchJson('/api/chat/admin/config'),
                    fetchJson('/api/chat/admin/feedback'),
                ]);
                setSummary(summaryData);
                setConfig(configData);
                setFeedback(feedbackData);
                setRateDraft(configData.rate_limits || {});
            } catch (err) {
                setError(err.message || 'Failed to load admin data.');
            }
        };
        load();
    }, [open]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
            <div className="w-full max-w-3xl rounded-2xl bg-white shadow-xl border border-[#E8E5DE]">
                <div className="flex items-center justify-between border-b border-[#EFEAE2] px-5 py-4">
                    <div>
                        <div className="text-sm uppercase tracking-[0.2em] text-[#A7A19A]">Admin</div>
                        <div className="text-lg font-semibold text-[#1A1915]">Operations Console</div>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-full p-2 text-[#6F6A63] hover:bg-[#F5F4F0]"
                        aria-label="Close admin panel"
                    >
                        <X size={18} />
                    </button>
                </div>

                {error && (
                    <div className="px-5 py-3 text-sm text-[#B54B3D] border-b border-[#F1D6D1] bg-[#FCEDEA]">
                        {error}
                    </div>
                )}

                <div className="grid gap-6 px-5 py-6 md:grid-cols-2">
                    <div className="space-y-4">
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Metrics</div>
                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842] space-y-2">
                            <div className="flex items-center justify-between">
                                <span>Total requests</span>
                                <span className="font-semibold">{summary?.requests_total ?? '-'}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Chat requests</span>
                                <span className="font-semibold">{summary?.chat_requests_total ?? '-'}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Chat errors</span>
                                <span className="font-semibold">{summary?.chat_errors_total ?? '-'}</span>
                            </div>
                        </div>
                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842] space-y-2">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] mb-1">Feedback</div>
                            <div className="flex items-center justify-between">
                                <span>Total</span>
                                <span className="font-semibold">{feedback?.summary?.total ?? '-'}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Helpful</span>
                                <span className="font-semibold">{feedback?.summary?.up ?? '-'}</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span>Not helpful</span>
                                <span className="font-semibold">{feedback?.summary?.down ?? '-'}</span>
                            </div>
                        </div>
                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] mb-2">Recent Feedback</div>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                                {(feedback?.recent || []).length === 0 && (
                                    <div className="text-[#A7A19A] text-[12px]">No feedback yet.</div>
                                )}
                                {(feedback?.recent || []).map((item) => (
                                    <div key={item.feedback_id} className="rounded-lg bg-[#F7F5F0] px-3 py-2 text-[12px]">
                                        <div className="flex items-center justify-between">
                                            <span className={item.rating === 'up' ? 'text-[#2E6B43]' : 'text-[#B54B3D]'}>
                                                {item.rating === 'up' ? 'Helpful' : 'Not helpful'}
                                            </span>
                                            <span className="text-[#A7A19A]">
                                                {item.created_at ? new Date(item.created_at * 1000).toLocaleString() : ''}
                                            </span>
                                        </div>
                                        {item.comment && <div className="mt-1 text-[#6F6A63]">{item.comment}</div>}
                                        <div className="mt-1 text-[#A7A19A]">{item.model_provider}:{item.model_name}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] mb-2">Recent Errors</div>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                                {(summary?.recent_errors || []).length === 0 && (
                                    <div className="text-[#A7A19A] text-[12px]">No recent errors.</div>
                                )}
                                {(summary?.recent_errors || []).slice().reverse().map((item, idx) => (
                                    <div key={`${item.event}-${idx}`} className="rounded-lg bg-[#F7F5F0] px-3 py-2 text-[12px]">
                                        <div className="font-semibold">{item.event}</div>
                                        <div className="text-[#8C867E] truncate">{item.detail || item.error_type}</div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">API Keys</div>
                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842] space-y-2">
                            {(config?.api_keys || []).length === 0 && (
                                <div className="text-[#A7A19A] text-[12px]">No runtime keys.</div>
                            )}
                            {(config?.api_keys || []).map((keyItem) => (
                                <div key={keyItem.key_id || keyItem.key} className="flex items-center justify-between gap-2">
                                    <div className="truncate">{keyItem.key}</div>
                                    <div className="flex items-center gap-2">
                                        <span className="rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[11px] text-[#6F6A63]">
                                            {keyItem.role}
                                        </span>
                                        {keyItem.key_id && (
                                            <button
                                                type="button"
                                                onClick={async () => {
                                                    try {
                                                        await fetchJson(`/api/chat/admin/keys/${keyItem.key_id}`, {
                                                            method: 'DELETE',
                                                        });
                                                        const configData = await fetchJson('/api/chat/admin/config');
                                                        setConfig(configData);
                                                    } catch (err) {
                                                        setError(err.message || 'Failed to delete key.');
                                                    }
                                                }}
                                                className="rounded-full border border-[#F1D6D1] px-2 py-0.5 text-[11px] text-[#B54B3D] hover:bg-[#FCEDEA]"
                                            >
                                                Remove
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842] space-y-3">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Add key</div>
                            <input
                                value={keyDraft.key}
                                onChange={(event) => setKeyDraft((prev) => ({ ...prev, key: event.target.value }))}
                                placeholder="New API key"
                                className="w-full rounded-lg border border-[#E8E5DE] px-2 py-1 text-[13px]"
                            />
                            <select
                                value={keyDraft.role}
                                onChange={(event) => setKeyDraft((prev) => ({ ...prev, role: event.target.value }))}
                                className="w-full rounded-lg border border-[#E8E5DE] px-2 py-1 text-[13px]"
                            >
                                <option value="admin">admin</option>
                                <option value="public">public</option>
                            </select>
                            <div className="space-y-2">
                                {['chat', 'voice', 'tts', 'image', 'analytics', 'feedback'].map((key) => (
                                    <div key={key} className="flex items-center gap-2">
                                        <span className="w-20 text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">{key}</span>
                                        <input
                                            value={keyDraft.limits[key] || ''}
                                            onChange={(event) => setKeyDraft((prev) => ({
                                                ...prev,
                                                limits: { ...(prev.limits || {}), [key]: event.target.value }
                                            }))}
                                            placeholder="10/minute"
                                            className="flex-1 rounded-lg border border-[#E8E5DE] px-2 py-1 text-[12px]"
                                        />
                                    </div>
                                ))}
                            </div>
                            <button
                                type="button"
                                onClick={async () => {
                                    if (!keyDraft.key.trim()) return;
                                    try {
                                        await fetchJson('/api/chat/admin/keys', {
                                            method: 'POST',
                                            body: JSON.stringify(keyDraft),
                                        });
                                        setKeyDraft({ key: '', role: 'admin', limits: {} });
                                        const configData = await fetchJson('/api/chat/admin/config');
                                        setConfig(configData);
                                    } catch (err) {
                                        setError(err.message || 'Failed to add key.');
                                    }
                                }}
                                className="w-full rounded-lg bg-[#DA7756] px-3 py-2 text-white text-[13px] font-medium hover:bg-[#C4654A]"
                            >
                                Save key
                            </button>
                        </div>

                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842] space-y-3">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Rate limits</div>
                            {['chat', 'voice', 'tts', 'image', 'analytics', 'feedback'].map((key) => (
                                <div key={key} className="flex items-center gap-2">
                                    <span className="w-20 text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">{key}</span>
                                    <input
                                        value={rateDraft[key] || ''}
                                        onChange={(event) => setRateDraft((prev) => ({ ...prev, [key]: event.target.value }))}
                                        placeholder="10/minute"
                                        className="flex-1 rounded-lg border border-[#E8E5DE] px-2 py-1 text-[13px]"
                                    />
                                </div>
                            ))}
                            <button
                                type="button"
                                onClick={async () => {
                                    try {
                                        await fetchJson('/api/chat/admin/rate-limits', {
                                            method: 'POST',
                                            body: JSON.stringify(rateDraft),
                                        });
                                    } catch (err) {
                                        setError(err.message || 'Failed to update rate limits.');
                                    }
                                }}
                                className={clsx(
                                    "w-full rounded-lg px-3 py-2 text-[13px] font-medium",
                                    "bg-[#F5F4F0] text-[#3E3A34] hover:bg-[#EFEAE2]"
                                )}
                            >
                                Update rate limits
                            </button>
                        </div>
                        <div className="rounded-xl border border-[#EFEAE2] p-4 text-sm text-[#4C4842] space-y-2">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Project access</div>
                            {Object.keys(config?.project_access || {}).length === 0 && (
                                <div className="text-[#A7A19A] text-[12px]">No project access rules.</div>
                            )}
                            {Object.entries(config?.project_access || {}).map(([projectId, role]) => (
                                <div key={projectId} className="flex items-center justify-between text-[12px]">
                                    <span className="truncate">{projectId}</span>
                                    <span className="rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[11px] text-[#6F6A63]">
                                        {role}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminPanel;
