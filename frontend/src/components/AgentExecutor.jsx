/**
 * AgentExecutor Component
 * Shows step-by-step progress for multi-step task execution.
 */
import React, { useState } from 'react';
import { Zap, CheckCircle, Circle, Loader2, X, Play } from 'lucide-react';

const API_KEY = import.meta.env.VITE_API_KEY;

const EXAMPLE_TASKS = [
    "Find a restaurant in KLCC, then get directions from my location",
    "Search for Nasi Lemak near Bangsar, filter by rating above 4.5",
    "Plan a day trip to Batu Caves, including lunch recommendations nearby",
];

const AgentExecutor = ({ onClose, onResult }) => {
    const [task, setTask] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleExecute = async () => {
        if (!task.trim()) return;

        setIsLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch('/api/agent/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
                body: JSON.stringify({ task: task.trim() }),
            });

            if (!response.ok) {
                throw new Error('Task execution failed');
            }

            const data = await response.json();
            setResult(data);
            onResult?.(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <div className="bg-white rounded-2xl w-full max-w-2xl shadow-xl my-8">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-[#E8E5DE]">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#9C27B0] to-[#E040FB] flex items-center justify-center">
                            <Zap size={20} className="text-white" />
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-[#1A1915]">
                                Agent Mode
                            </div>
                            <div className="text-[12px] text-[#A7A19A]">
                                Execute multi-step tasks automatically
                            </div>
                        </div>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-full text-[#6F6A63] hover:bg-[#F5F4F0]"
                    >
                        <X size={18} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-5 space-y-5">
                    {/* Task Input */}
                    <div>
                        <label className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] block mb-2">
                            What would you like me to do?
                        </label>
                        <textarea
                            value={task}
                            onChange={(e) => setTask(e.target.value)}
                            placeholder="Describe a multi-step task..."
                            rows={3}
                            className="w-full px-4 py-3 rounded-xl border border-[#E8E5DE] text-[#1A1915] focus:outline-none focus:ring-2 focus:ring-[#9C27B0] resize-none"
                        />
                    </div>

                    {/* Example Tasks */}
                    <div>
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] mb-2">
                            Example Tasks
                        </div>
                        <div className="space-y-2">
                            {EXAMPLE_TASKS.map((example, idx) => (
                                <button
                                    key={idx}
                                    onClick={() => setTask(example)}
                                    className="w-full text-left px-4 py-2.5 rounded-xl border border-[#E8E5DE] text-[#6F6A63] text-[13px] hover:border-[#9C27B0] hover:text-[#9C27B0] transition-colors"
                                >
                                    {example}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button
                        onClick={handleExecute}
                        disabled={isLoading || !task.trim()}
                        className="w-full flex items-center justify-center gap-2 bg-[#9C27B0] text-white py-4 rounded-xl font-medium hover:bg-[#8E24AA] disabled:opacity-50"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                Executing...
                            </>
                        ) : (
                            <>
                                <Play size={18} />
                                Execute Task
                            </>
                        )}
                    </button>

                    {/* Steps Progress */}
                    {result?.steps && (
                        <div className="bg-[#F9F8F6] rounded-xl p-5 space-y-4">
                            <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                Execution Steps
                            </div>
                            <div className="space-y-3">
                                {result.steps.map((step, idx) => (
                                    <div key={idx} className="flex gap-3">
                                        <div className="flex-shrink-0 mt-0.5">
                                            <CheckCircle size={18} className="text-[#4CAF50]" />
                                        </div>
                                        <div>
                                            <div className="text-[13px] font-medium text-[#4C4842]">
                                                Step {step.step}: {step.description}
                                            </div>
                                            <div className="text-[12px] text-[#6F6A63] mt-1">
                                                {step.result}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Final Result */}
                    {result?.result && (
                        <div className="bg-gradient-to-br from-[#F3E5F5] to-[#FCE4EC] rounded-xl p-5">
                            <div className="text-[11px] uppercase tracking-[0.2em] text-[#9C27B0] mb-2">
                                Final Result
                            </div>
                            <div className="text-[#1A1915] whitespace-pre-wrap">
                                {result.result}
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-50 text-red-600 rounded-xl p-4 text-[13px]">
                            {error}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AgentExecutor;
