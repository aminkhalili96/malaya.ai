import React, { useState } from 'react';
import { Navigation, Clock, Car, PersonStanding, Bike, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

const DirectionsWidget = ({ data }) => {
    const [expanded, setExpanded] = useState(false);
    const [selectedMode, setSelectedMode] = useState('driving');

    // Parse tool output if stringified
    let directionsData = null;
    try {
        if (typeof data === 'string') {
            directionsData = JSON.parse(data);
        } else {
            directionsData = data;
        }
    } catch (e) {
        console.error("Failed to parse directions data", e);
        return null;
    }

    if (!directionsData || !directionsData.routes || directionsData.routes.length === 0) {
        console.log('DirectionsWidget: No routes in data', directionsData);
        return null;
    }

    const route = directionsData.routes[0];
    const leg = route.legs?.[0];

    // Handle both formats: legs array or route-level data
    const origin = leg?.start_address || directionsData.origin || route.startAddress || 'Origin';
    const destination = leg?.end_address || directionsData.destination || route.endAddress || 'Destination';
    const duration = leg?.duration?.text || route.duration?.text || route.localizedValues?.duration?.text || 'N/A';
    const distance = leg?.distance?.text || route.distance?.text || route.localizedValues?.distance?.text || 'N/A';
    const steps = leg?.steps || route.legs?.[0]?.steps || [];

    // Build Google Maps directions URL
    const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&travelmode=${selectedMode}`;

    const travelModes = [
        { key: 'driving', icon: Car, label: 'Drive' },
        { key: 'walking', icon: PersonStanding, label: 'Walk' },
        { key: 'bicycling', icon: Bike, label: 'Bike' },
    ];

    return (
        <div className="my-4 w-full max-w-lg bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden hover:shadow-md transition-shadow">
            {/* Header */}
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-white font-medium">
                    <Navigation size={18} />
                    <span>Directions</span>
                </div>
                <span className="text-xs text-blue-100">Google Maps</span>
            </div>

            {/* Route Summary */}
            <div className="p-4 border-b border-gray-100">
                <div className="flex items-start gap-3">
                    <div className="flex flex-col items-center">
                        <div className="w-3 h-3 rounded-full bg-green-500 border-2 border-white shadow"></div>
                        <div className="w-0.5 h-8 bg-gray-300"></div>
                        <div className="w-3 h-3 rounded-full bg-red-500 border-2 border-white shadow"></div>
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-600 truncate">{origin}</p>
                        <div className="h-4"></div>
                        <p className="text-sm font-medium text-gray-900 truncate">{destination}</p>
                    </div>
                </div>

                {/* Duration & Distance */}
                <div className="mt-4 flex items-center gap-4">
                    <div className="flex items-center gap-1.5 text-gray-700">
                        <Clock size={16} className="text-gray-400" />
                        <span className="text-sm font-semibold">{duration}</span>
                    </div>
                    <span className="text-gray-300">|</span>
                    <span className="text-sm text-gray-500">{distance}</span>
                </div>

                {/* Travel Mode Selector */}
                <div className="mt-3 flex gap-2">
                    {travelModes.map(mode => (
                        <button
                            key={mode.key}
                            onClick={() => setSelectedMode(mode.key)}
                            className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${selectedMode === mode.key
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                        >
                            <mode.icon size={14} />
                            {mode.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Turn-by-Turn Directions (Expandable) */}
            {steps.length > 0 && (
                <div className="border-b border-gray-100">
                    <button
                        onClick={() => setExpanded(!expanded)}
                        className="w-full px-4 py-3 flex items-center justify-between text-sm text-gray-600 hover:bg-gray-50 transition-colors"
                    >
                        <span>{expanded ? 'Hide' : 'Show'} turn-by-turn ({steps.length} steps)</span>
                        {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>

                    {expanded && (
                        <div className="px-4 pb-4 max-h-60 overflow-y-auto">
                            <ol className="space-y-3">
                                {steps.map((step, idx) => (
                                    <li key={idx} className="flex gap-3 text-sm">
                                        <span className="flex-shrink-0 w-6 h-6 bg-gray-100 text-gray-600 rounded-full flex items-center justify-center text-xs font-medium">
                                            {idx + 1}
                                        </span>
                                        <div className="flex-1">
                                            <p
                                                className="text-gray-700"
                                                dangerouslySetInnerHTML={{ __html: step.html_instructions || step.instructions || '' }}
                                            />
                                            <p className="text-xs text-gray-400 mt-0.5">
                                                {step.distance?.text} • {step.duration?.text}
                                            </p>
                                        </div>
                                    </li>
                                ))}
                            </ol>
                        </div>
                    )}
                </div>
            )}

            {/* Static Map Preview */}
            <a
                href={mapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="block"
            >
                <div className="w-full h-32 bg-blue-50 relative group">
                    <img
                        src={`https://maps.googleapis.com/maps/api/staticmap?size=600x200&path=color:0x4285F4|weight:5|enc:${route.overview_polyline?.points || ''}&markers=color:green|${encodeURIComponent(origin)}&markers=color:red|${encodeURIComponent(destination)}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`}
                        alt="Route preview"
                        className="w-full h-full object-cover"
                        onError={(e) => {
                            e.target.style.display = 'none';
                        }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/10 transition-colors">
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity bg-white/90 px-3 py-1.5 rounded-full text-sm font-medium text-gray-700 shadow-md">
                            Open in Google Maps
                        </div>
                    </div>
                </div>
            </a>

            {/* Action Button */}
            <div className="p-4">
                <a
                    href={mapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center gap-2 w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                    <Navigation size={16} />
                    <span>Start Navigation</span>
                    <ExternalLink size={14} />
                </a>
            </div>
        </div>
    );
};

export default DirectionsWidget;
