
import React, { useState, useRef, useEffect } from 'react';
import { Send, Plus, Clock, SlidersHorizontal, Camera, Headphones, MapPin, Zap } from 'lucide-react';
import clsx from 'clsx';
import PlaceCard from './PlaceCard';

const API_KEY = import.meta.env.VITE_API_KEY;

// Extract widgets from tool_calls for rendering
// For maps_search_places, split each place into its own widget so each gets a full card
const buildWidgetsFromToolCalls = (toolCalls) => {
    if (!Array.isArray(toolCalls)) return [];
    const widgets = [];
    toolCalls.forEach((tool) => {
        if (tool.name === 'maps_geocode' && tool.content) {
            widgets.push({ type: 'place', data: tool.content });
        } else if (tool.name === 'maps_directions' && tool.content) {
            widgets.push({ type: 'directions', data: tool.content });
        } else if (tool.name === 'maps_search_places' && tool.content) {
            // Parse the content to extract individual places
            let parsed = tool.content;
            if (typeof parsed === 'string') {
                try {
                    parsed = JSON.parse(parsed);
                } catch {
                    parsed = null;
                }
            }
            // If we have a places array, create a widget for each place (up to 5)
            if (parsed?.places && Array.isArray(parsed.places)) {
                const placesToShow = parsed.places.slice(0, 5);
                placesToShow.forEach((place) => {
                    // Wrap each place as a single-place result for PlaceCard
                    widgets.push({
                        type: 'place',
                        data: { places: [place] }
                    });
                });
            } else {
                // Fallback: just pass the whole thing
                widgets.push({ type: 'place', data: tool.content });
            }
        }
    });
    return widgets;
};


const ChatInterface = ({ mode, onNewChat, onFeatureSelect }) => {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [toolsOpen, setToolsOpen] = useState(false);
    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const toolsRef = useRef(null);

    const featureButtons = [
        { id: 'snap', icon: Camera, label: 'Snap & Translate', color: '#DA7756' },
        { id: 'podcast', icon: Headphones, label: 'Podcast Mode', color: '#E8956E' },
        { id: 'tourist', icon: MapPin, label: 'Tourist Mode', color: '#4CAF50' },
        { id: 'agent', icon: Zap, label: 'Agent Mode', color: '#9C27B0' },
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        const handleClick = (event) => {
            if (toolsRef.current && !toolsRef.current.contains(event.target)) {
                setToolsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClick);
        return () => document.removeEventListener('mousedown', handleClick);
    }, []);

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
        setToolsOpen(false);
        if (onNewChat) onNewChat();
    };

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;

        setToolsOpen(false);
        const userMsg = { role: 'user', content: input };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await fetch('/api/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...(API_KEY ? { 'X-API-Key': API_KEY } : {}) },
                body: JSON.stringify({
                    message: input,
                    history: messages.map(m => ({ role: m.role, content: m.content }))
                }),
            });

            if (!res.ok) throw new Error('API Error');
            const data = await res.json();

            // Extract widgets from tool_calls (e.g., maps_search_places)
            const widgets = buildWidgetsFromToolCalls(data.tool_calls || []);

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: data.answer,
                widgets: widgets,
                sources: data.sources || []
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
                                        <div ref={toolsRef} className="relative">
                                            <button
                                                type="button"
                                                onClick={() => setToolsOpen((open) => !open)}
                                                className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors"
                                            >
                                                <SlidersHorizontal size={18} strokeWidth={1.5} />
                                            </button>
                                            {toolsOpen && (
                                                <div className="absolute left-0 bottom-full mb-2 w-52 rounded-xl border border-[#E8E5DE] bg-white shadow-lg py-2 text-sm text-[#1A1915] z-30">
                                                    {featureButtons.map((btn) => (
                                                        <button
                                                            key={btn.id}
                                                            type="button"
                                                            onClick={() => {
                                                                onFeatureSelect?.(btn.id);
                                                                setToolsOpen(false);
                                                            }}
                                                            className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#F5F4F0] transition-colors"
                                                        >
                                                            <btn.icon size={14} style={{ color: btn.color }} />
                                                            <span>{btn.label}</span>
                                                        </button>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
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
                                    "flex flex-col",
                                    msg.role === 'user' ? "items-end" : "items-start"
                                )}>
                                    {/* Message Bubble */}
                                    <div className={clsx(
                                        "max-w-[75%] rounded-2xl px-4 py-3 text-[15px] leading-relaxed",
                                        msg.role === 'user'
                                            ? "bg-[#2563EB] text-white rounded-br-md"
                                            : "bg-white text-[#1A1915] border border-[#E8E5DE] shadow-sm rounded-bl-md"
                                    )}>
                                        <div className="whitespace-pre-wrap">{msg.content}</div>
                                    </div>

                                    {/* Render PlaceCard widgets if present */}
                                    {msg.widgets && msg.widgets.length > 0 && (
                                        <div className="mt-3 w-full max-w-[90%]">
                                            {msg.widgets.map((widget, widx) => (
                                                widget.type === 'place' && (
                                                    <PlaceCard key={widx} data={widget.data} />
                                                )
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Loading indicator */}
                            {isLoading && (
                                <div className="flex justify-start">
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
                                    <div ref={toolsRef} className="relative">
                                        <button
                                            type="button"
                                            onClick={() => setToolsOpen((open) => !open)}
                                            className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors"
                                        >
                                            <SlidersHorizontal size={18} strokeWidth={1.5} />
                                        </button>
                                        {toolsOpen && (
                                            <div className="absolute left-0 bottom-full mb-2 w-52 rounded-xl border border-[#E8E5DE] bg-white shadow-lg py-2 text-sm text-[#1A1915] z-30">
                                                {featureButtons.map((btn) => (
                                                    <button
                                                        key={btn.id}
                                                        type="button"
                                                        onClick={() => {
                                                            onFeatureSelect?.(btn.id);
                                                            setToolsOpen(false);
                                                        }}
                                                        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-[#F5F4F0] transition-colors"
                                                    >
                                                        <btn.icon size={14} style={{ color: btn.color }} />
                                                        <span>{btn.label}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
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
