/**
 * TouristPlanner Component
 * Helps tourists plan their trip with curated itineraries.
 */
import React, { useState } from 'react';
import { MapPin, Calendar, Sparkles, Loader2, X, Heart } from 'lucide-react';

const API_KEY = import.meta.env.VITE_API_KEY;

const POPULAR_DESTINATIONS = [
    { name: 'Penang', emoji: '🍜' },
    { name: 'Langkawi', emoji: '🏝️' },
    { name: 'Kuala Lumpur', emoji: '🏙️' },
    { name: 'Melaka', emoji: '🏛️' },
    { name: 'Cameron Highlands', emoji: '🌿' },
    { name: 'Ipoh', emoji: '☕' },
];

const TouristPlanner = ({ onClose, onItineraryGenerated }) => {
    const [location, setLocation] = useState('');
    const [days, setDays] = useState(2);
    const [interests, setInterests] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleGenerate = async () => {
        if (!location.trim()) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/tourist/itinerary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
                body: JSON.stringify({
                    location: location.trim(),
                    days,
                    interests: interests.trim() || null
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to generate itinerary');
            }

            const data = await response.json();
            setResult(data);
            onItineraryGenerated?.(data);
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
                        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#4CAF50] to-[#8BC34A] flex items-center justify-center">
                            <MapPin size={20} className="text-white" />
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-[#1A1915]">
                                Tourist Mode
                            </div>
                            <div className="text-[12px] text-[#A7A19A]">
                                Get curated local experiences
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
                    {/* Quick Select */}
                    <div>
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] mb-2">
                            Popular Destinations
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {POPULAR_DESTINATIONS.map((dest) => (
                                <button
                                    key={dest.name}
                                    onClick={() => setLocation(dest.name)}
                                    className={`px-3 py-1.5 rounded-full text-[13px] border transition-colors ${location === dest.name
                                            ? 'border-[#4CAF50] bg-[#E8F5E9] text-[#2E7D32]'
                                            : 'border-[#E8E5DE] text-[#6F6A63] hover:border-[#4CAF50]'
                                        }`}
                                >
                                    {dest.emoji} {dest.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Form */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] block mb-2">
                                Destination
                            </label>
                            <input
                                type="text"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="e.g., Penang, Ipoh, KL..."
                                className="w-full px-4 py-3 rounded-xl border border-[#E8E5DE] text-[#1A1915] focus:outline-none focus:ring-2 focus:ring-[#4CAF50]"
                            />
                        </div>
                        <div>
                            <label className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] block mb-2">
                                Duration
                            </label>
                            <div className="flex items-center gap-2">
                                <input
                                    type="number"
                                    min={1}
                                    max={14}
                                    value={days}
                                    onChange={(e) => setDays(parseInt(e.target.value) || 1)}
                                    className="w-20 px-4 py-3 rounded-xl border border-[#E8E5DE] text-[#1A1915] focus:outline-none focus:ring-2 focus:ring-[#4CAF50]"
                                />
                                <span className="text-[#6F6A63]">days</span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <label className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] block mb-2">
                            Special Interests (Optional)
                        </label>
                        <input
                            type="text"
                            value={interests}
                            onChange={(e) => setInterests(e.target.value)}
                            placeholder="e.g., street food, temples, beaches, photography..."
                            className="w-full px-4 py-3 rounded-xl border border-[#E8E5DE] text-[#1A1915] focus:outline-none focus:ring-2 focus:ring-[#4CAF50]"
                        />
                    </div>

                    <button
                        onClick={handleGenerate}
                        disabled={isLoading || !location.trim()}
                        className="w-full flex items-center justify-center gap-2 bg-[#4CAF50] text-white py-4 rounded-xl font-medium hover:bg-[#43A047] disabled:opacity-50"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 size={18} className="animate-spin" />
                                Generating...
                            </>
                        ) : (
                            <>
                                <Sparkles size={18} />
                                Generate Itinerary
                            </>
                        )}
                    </button>

                    {/* Result */}
                    {result && (
                        <div className="bg-[#F9F8F6] rounded-xl p-5 space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Your Itinerary
                                    </div>
                                    <div className="text-lg font-semibold text-[#1A1915]">
                                        {result.days} Days in {result.location}
                                    </div>
                                </div>
                                <button className="p-2 rounded-full text-[#E91E63] hover:bg-[#FCE4EC]">
                                    <Heart size={20} />
                                </button>
                            </div>

                            <div className="prose prose-sm max-w-none text-[#4C4842] whitespace-pre-wrap">
                                {result.itinerary}
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

export default TouristPlanner;
