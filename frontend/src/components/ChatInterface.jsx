
import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, Clock, SlidersHorizontal, User } from 'lucide-react';
import clsx from 'clsx';

const ChatInterface = ({ mode, onNewChat }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
        }
    }, [input]);

    const handleNewChat = () => {
        setMessages([]);
        setInput('');
        if (onNewChat) onNewChat();
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: input,
                    history: messages.map(m => ({ role: m.role, content: m.content }))
                }),
            });

            if (!res.ok) throw new Error('API Error');
            const data = await res.json();

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.answer
            }]);
            setIsLoading(false);
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "Sorry, I couldn't connect to the server."
            }]);
            setIsLoading(false);
        }
    };

    const isEmptyChat = messages.length === 0;

    return (
        <div className="flex flex-col h-full w-full bg-[#FAF9F7] relative">
            {/* Header - New Chat button (top right) */}
            <div className="absolute top-4 right-6 z-10">
                <button
                    onClick={handleNewChat}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-[#706F6C] hover:text-[#1A1915] transition-colors"
                >
                    <Plus size={16} strokeWidth={1.5} />
                    <span>New chat</span>
                </button>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto flex flex-col">
                {isEmptyChat ? (
                    /* Welcome Screen - Claude.ai Style */
                    <div className="flex-1 flex flex-col items-center justify-center px-4">
                        {/* Title */}
                        <h1 className="text-[28px] font-normal text-[#1A1915] mb-8 tracking-tight">
                            <span className="text-[#DA7756]">✻</span> Malaya is thinking
                        </h1>

                        {/* Input Box - Claude.ai style */}
                        <div className="w-full max-w-[560px]">
                            <div className="bg-white border border-[#D4D2CC] rounded-2xl shadow-sm overflow-hidden">
                                <div className="px-4 pt-4 pb-3">
                                    <textarea
                                        ref={textareaRef}
                                        value={input}
                                        onChange={(e) => setInput(e.target.value)}
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                handleSend();
                                            }
                                        }}
                                        placeholder="How can I help you today?"
                                        className="w-full bg-transparent border-none focus:ring-0 focus:outline-none resize-none min-h-[24px] max-h-[200px] text-[15px] text-[#1A1915] placeholder:text-[#A3A29E]"
                                        rows={1}
                                    />
                                </div>

                                {/* Bottom toolbar */}
                                <div className="flex items-center justify-between px-3 pb-3">
                                    <div className="flex items-center gap-1">
                                        <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                                            <Plus size={18} strokeWidth={1.5} />
                                        </button>
                                        <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                                            <SlidersHorizontal size={18} strokeWidth={1.5} />
                                        </button>
                                        <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                                            <Clock size={18} strokeWidth={1.5} />
                                        </button>
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <span className="text-[13px] text-[#706F6C]">Malaya 1.0</span>
                                        <button
                                            onClick={handleSend}
                                            disabled={isLoading || !input.trim()}
                                            className={clsx(
                                                "p-2 rounded-lg transition-all",
                                                input.trim() && !isLoading
                                                    ? "bg-[#DA7756] text-white hover:bg-[#C4654A]"
                                                    : "bg-[#E8E5DE] text-[#A3A29E] cursor-not-allowed"
                                            )}
                                        >
                                            <Send size={16} strokeWidth={2} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                ) : (
                    /* Chat Messages - LLM Left, User Right */
                    <div className="flex-1 overflow-y-auto">
                        <div className="max-w-[720px] mx-auto px-4 py-8 space-y-6 pb-40">
                            {messages.map((msg, idx) => (
                                <div key={idx} className={clsx(
                                    "flex gap-3",
                                    msg.role === 'user' ? "justify-end" : "justify-start"
                                )}>
                                    {/* Assistant Avatar (Left) */}
                                    {msg.role === 'assistant' && (
                                        <div className="w-8 h-8 rounded-full bg-[#DA7756] flex items-center justify-center shrink-0">
                                            <span className="text-white text-sm font-medium">M</span>
                                        </div>
                                    )}

                                    {/* Message Bubble */}
                                    <div className={clsx(
                                        "max-w-[75%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed",
                                        msg.role === 'user'
                                            ? "bg-[#2563EB] text-white rounded-br-md"
                                            : "bg-white text-[#1A1915] border border-[#E8E5DE] shadow-sm rounded-bl-md"
                                    )}>
                                        <div className="whitespace-pre-wrap">{msg.content}</div>
                                    </div>

                                    {/* User Avatar (Right) */}
                                    {msg.role === 'user' && (
                                        <div className="w-8 h-8 rounded-full bg-[#E8E5DE] flex items-center justify-center shrink-0">
                                            <User size={16} className="text-[#706F6C]" />
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Loading indicator */}
                            {isLoading && (
                                <div className="flex gap-3 justify-start">
                                    <div className="w-8 h-8 rounded-full bg-[#DA7756] flex items-center justify-center shrink-0">
                                        <span className="text-white text-sm font-medium">M</span>
                                    </div>
                                    <div className="bg-white border border-[#E8E5DE] rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                                        <div className="flex items-center gap-1.5">
                                            <div className="w-2 h-2 bg-[#DA7756] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <div className="w-2 h-2 bg-[#DA7756] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <div className="w-2 h-2 bg-[#DA7756] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>
                    </div>
                )}
            </div>

            {/* Fixed Input Area (when chatting) */}
            {!isEmptyChat && (
                <div className="absolute bottom-0 left-0 right-0 px-4 pb-6 pt-4 bg-gradient-to-t from-[#FAF9F7] via-[#FAF9F7] to-transparent">
                    <div className="max-w-[720px] mx-auto">
                        <div className="bg-white border border-[#D4D2CC] rounded-2xl shadow-sm overflow-hidden">
                            <div className="px-4 pt-4 pb-3">
                                <textarea
                                    ref={textareaRef}
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey) {
                                            e.preventDefault();
                                            handleSend();
                                        }
                                    }}
                                    placeholder="Reply to Malaya..."
                                    className="w-full bg-transparent border-none focus:ring-0 focus:outline-none resize-none min-h-[24px] max-h-[200px] text-[15px] text-[#1A1915] placeholder:text-[#A3A29E]"
                                    rows={1}
                                />
                            </div>

                            {/* Bottom toolbar */}
                            <div className="flex items-center justify-between px-3 pb-3">
                                <div className="flex items-center gap-1">
                                    <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                                        <Plus size={18} strokeWidth={1.5} />
                                    </button>
                                    <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                                        <SlidersHorizontal size={18} strokeWidth={1.5} />
                                    </button>
                                </div>

                                <button
                                    onClick={handleSend}
                                    disabled={isLoading || !input.trim()}
                                    className={clsx(
                                        "p-2 rounded-lg transition-all",
                                        input.trim() && !isLoading
                                            ? "bg-[#DA7756] text-white hover:bg-[#C4654A]"
                                            : "bg-[#E8E5DE] text-[#A3A29E] cursor-not-allowed"
                                    )}
                                >
                                    <Send size={16} strokeWidth={2} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatInterface;
