/**
 * PodcastPlayer Component
 * Allows users to input a URL and get a podcast summary with audio playback.
 */
import React, { useState, useRef } from 'react';
import { Headphones, Link, Play, Pause, Volume2, Loader2, X } from 'lucide-react';

const API_KEY = import.meta.env.VITE_API_KEY;

const PodcastPlayer = ({ onClose }) => {
    const [url, setUrl] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [error, setError] = useState(null);
    const audioRef = useRef(null);

    const handleCreatePodcast = async () => {
        if (!url.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/podcast/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
                body: JSON.stringify({
                    url: url.trim(),
                    voice: 'malay_female',
                    summarize: true
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create podcast');
            }

            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const togglePlayPause = () => {
        if (audioRef.current) {
            if (isPlaying) {
                audioRef.current.pause();
            } else {
                audioRef.current.play();
            }
            setIsPlaying(!isPlaying);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl w-full max-w-lg shadow-xl">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-[#E8E5DE]">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#DA7756] to-[#E8956E] flex items-center justify-center">
                            <Headphones size={20} className="text-white" />
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-[#1A1915]">
                                Podcast Mode
                            </div>
                            <div className="text-[12px] text-[#A7A19A]">
                                Listen to articles on the go
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
                <div className="p-5 space-y-4">
                    {/* URL Input */}
                    <div className="flex gap-2">
                        <div className="flex-1 relative">
                            <Link size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#A7A19A]" />
                            <input
                                type="url"
                                value={url}
                                onChange={(e) => setUrl(e.target.value)}
                                placeholder="Paste article URL here..."
                                className="w-full pl-10 pr-4 py-3 rounded-xl border border-[#E8E5DE] text-[#1A1915] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                            />
                        </div>
                        <button
                            onClick={handleCreatePodcast}
                            disabled={isLoading || !url.trim()}
                            className="px-5 py-3 bg-[#DA7756] text-white rounded-xl font-medium hover:bg-[#C4654A] disabled:opacity-50 flex items-center gap-2"
                        >
                            {isLoading ? (
                                <Loader2 size={18} className="animate-spin" />
                            ) : (
                                'Create'
                            )}
                        </button>
                    </div>

                    {/* Result */}
                    {result && (
                        <div className="bg-[#F9F8F6] rounded-xl p-4 space-y-4">
                            <div>
                                <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                    Article
                                </div>
                                <div className="text-[#1A1915] font-medium mt-1">
                                    {result.title}
                                </div>
                            </div>

                            <div>
                                <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                    Summary
                                </div>
                                <div className="text-[#4C4842] text-[14px] mt-1 leading-relaxed">
                                    {result.summary}
                                </div>
                            </div>

                            {/* Audio Player */}
                            {result.audio_path && (
                                <div className="flex items-center gap-4 p-3 bg-white rounded-xl border border-[#E8E5DE]">
                                    <button
                                        onClick={togglePlayPause}
                                        className="w-12 h-12 rounded-full bg-[#DA7756] text-white flex items-center justify-center hover:bg-[#C4654A]"
                                    >
                                        {isPlaying ? <Pause size={20} /> : <Play size={20} className="ml-1" />}
                                    </button>
                                    <div className="flex-1">
                                        <div className="text-[13px] text-[#4C4842]">
                                            {isPlaying ? 'Now Playing' : 'Ready to Play'}
                                        </div>
                                        <div className="text-[11px] text-[#A7A19A]">
                                            Malaysian Voice (Yasmin)
                                        </div>
                                    </div>
                                    <Volume2 size={18} className="text-[#A7A19A]" />
                                    <audio
                                        ref={audioRef}
                                        src={`/api/podcast/audio/${result.audio_path.split('/').pop()}`}
                                        onEnded={() => setIsPlaying(false)}
                                    />
                                </div>
                            )}
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-50 text-red-600 rounded-xl p-4 text-[13px]">
                            {error}
                        </div>
                    )}

                    {/* Tips */}
                    <div className="text-[12px] text-[#A7A19A] space-y-1">
                        <div>💡 Works best with news articles and blog posts</div>
                        <div>🎧 Audio is generated in Malaysian English</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PodcastPlayer;
