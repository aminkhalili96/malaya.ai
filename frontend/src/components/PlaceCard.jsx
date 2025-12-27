import React, { useMemo, useState } from 'react';
import {
    ChevronRight,
    Clock,
    ExternalLink,
    Globe,
    MapPin,
    Navigation,
    Phone,
    Star,
} from 'lucide-react';

const PLACE_TYPE_LABELS = {
    restaurant: 'Restaurant',
    cafe: 'Cafe',
    bar: 'Bar',
    hotel: 'Hotel',
    shopping_mall: 'Shopping Mall',
    tourist_attraction: 'Attraction',
    museum: 'Museum',
    park: 'Park',
    hospital: 'Hospital',
    bank: 'Bank',
};

const priceLabel = (level) => {
    if (!level) return null;
    const priceMap = {
        PRICE_LEVEL_FREE: 'Free',
        PRICE_LEVEL_INEXPENSIVE: '$',
        PRICE_LEVEL_MODERATE: '$$',
        PRICE_LEVEL_EXPENSIVE: '$$$',
        PRICE_LEVEL_VERY_EXPENSIVE: '$$$$',
    };
    if (priceMap[level]) return priceMap[level];
    if (typeof level === 'number') return '$'.repeat(Math.min(level, 4));
    return null;
};

const primaryType = (types = []) => {
    if (!Array.isArray(types) || types.length === 0) return null;
    for (const type of types) {
        if (PLACE_TYPE_LABELS[type]) return PLACE_TYPE_LABELS[type];
    }
    const fallback = types[0];
    if (!fallback) return null;
    return fallback.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

const normalizePayload = (data) => {
    if (!data) return null;
    if (typeof data === 'string') {
        try {
            return JSON.parse(data);
        } catch (error) {
            console.error('Failed to parse place data', error);
            return null;
        }
    }
    return data;
};

const buildMapsUrl = ({ lat, lng, placeId, query, googleMapsUri }) => {
    if (googleMapsUri) return googleMapsUri;
    const baseQuery = query || `${lat},${lng}`;
    const encodedQuery = encodeURIComponent(baseQuery);
    const url = `https://www.google.com/maps/search/?api=1&query=${encodedQuery}`;
    return placeId ? `${url}&query_place_id=${encodeURIComponent(placeId)}` : url;
};

const buildDirectionsUrl = ({ lat, lng, placeId, query }) => {
    const destination = encodeURIComponent(query || `${lat},${lng}`);
    const url = `https://www.google.com/maps/dir/?api=1&destination=${destination}`;
    return placeId ? `${url}&destination_place_id=${encodeURIComponent(placeId)}` : url;
};

const getPhotoUrl = (photo, apiKey, maxWidth = 640) => {
    if (!photo || !apiKey) return null;
    if (photo.name) {
        return `https://places.googleapis.com/v1/${photo.name}/media?maxWidthPx=${maxWidth}&key=${apiKey}`;
    }
    if (photo.photo_reference) {
        return `https://maps.googleapis.com/maps/api/place/photo?maxwidth=${maxWidth}&photo_reference=${photo.photo_reference}&key=${apiKey}`;
    }
    return null;
};

const PlaceCard = ({ data }) => {
    const [showDetails, setShowDetails] = useState(false);
    const [mapFailed, setMapFailed] = useState(false);
    const [photoFailed, setPhotoFailed] = useState(false);

    const placeData = useMemo(() => normalizePayload(data), [data]);
    if (!placeData) return null;

    const placesList = Array.isArray(placeData.places) ? placeData.places : [];
    const place = placesList[0] || placeData;

    const lat = Number(
        place.location?.lat
        ?? place.location?.latitude
        ?? placeData.location?.lat
        ?? placeData.location?.latitude
    );
    const lng = Number(
        place.location?.lng
        ?? place.location?.longitude
        ?? placeData.location?.lng
        ?? placeData.location?.longitude
    );
    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;

    const name = place.displayName?.text
        || place.name
        || placeData.formatted_address?.split(',')[0]
        || 'Location';
    const address = place.formattedAddress || placeData.formatted_address || placeData.address || '';
    const rating = Number.isFinite(place.rating) ? place.rating : null;
    const ratingCount = place.userRatingCount || place.userRatingsTotal;
    const ratingCountValue = Number(ratingCount);
    const ratingCountText = Number.isFinite(ratingCountValue)
        ? ratingCountValue.toLocaleString()
        : null;
    const price = priceLabel(place.priceLevel);
    const placeId = place.id || place.place_id || placeData.place_id;
    const types = place.types || placeData.types || [];
    const businessStatus = place.businessStatus;
    const phone = place.nationalPhoneNumber || place.internationalPhoneNumber;
    const website = place.websiteUri || place.website;
    const openNow = place.currentOpeningHours?.openNow
        ?? place.openingHours?.openNow
        ?? place.regularOpeningHours?.openNow;
    const weekdayText = place.currentOpeningHours?.weekdayDescriptions
        || place.openingHours?.weekdayDescriptions
        || place.regularOpeningHours?.weekdayDescriptions;
    const photos = Array.isArray(place.photos) ? place.photos : [];
    const googleMapsUri = place.googleMapsUri || placeData.googleMapsUri;

    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
    const primaryPhotoUrl = getPhotoUrl(photos[0], apiKey);
    const hasPhoto = Boolean(primaryPhotoUrl) && !photoFailed;
    const statusLabel = businessStatus === 'CLOSED_PERMANENTLY'
        ? 'Permanently closed'
        : businessStatus === 'CLOSED_TEMPORARILY'
            ? 'Temporarily closed'
            : openNow === true
                ? 'Open now'
                : openNow === false
                    ? 'Closed now'
                    : null;
    const statusTone = openNow === true
        ? 'border-[#D4E9DA] bg-[#EEF7F1] text-[#2E6B43]'
        : openNow === false || businessStatus?.startsWith('CLOSED')
            ? 'border-[#F1D6D1] bg-[#FCEDEA] text-[#B54B3D]'
            : 'border-[#E8E5DE] bg-[#F7F5F0] text-[#6F6A63]';

    const typeLabel = primaryType(types);
    const mapsUrl = buildMapsUrl({ lat, lng, placeId, query: address || name, googleMapsUri });
    const directionsUrl = buildDirectionsUrl({ lat, lng, placeId, query: address || name });
    const metaLine = [typeLabel, price].filter(Boolean).join(' • ');
    const showDetailsToggle = Boolean(weekdayText || phone || website || ratingCountText);

    const extraPlaces = placesList.slice(1, 4)
        .map((item) => {
            const extraLat = Number(item.location?.lat ?? item.location?.latitude);
            const extraLng = Number(item.location?.lng ?? item.location?.longitude);
            if (!Number.isFinite(extraLat) || !Number.isFinite(extraLng)) return null;
            return {
                id: item.id || item.place_id || `${extraLat}-${extraLng}`,
                name: item.displayName?.text || item.name || 'Place',
                rating: Number.isFinite(item.rating) ? item.rating.toFixed(1) : null,
                type: primaryType(item.types || []),
                openNow: item.currentOpeningHours?.openNow ?? item.openingHours?.openNow,
                mapsUrl: buildMapsUrl({
                    lat: extraLat,
                    lng: extraLng,
                    placeId: item.id || item.place_id,
                    query: item.formattedAddress || item.name,
                    googleMapsUri: item.googleMapsUri,
                }),
            };
        })
        .filter(Boolean);

    // Extract editorial summary and additional info from Google Places API
    const editorialSummary = place.editorialSummary?.text || place.summary || null;
    const servesVegetarianFood = place.servesVegetarianFood;
    const dineIn = place.dineIn;
    const takeout = place.takeout;
    const delivery = place.delivery;

    // Generate rating tier and description
    const getRatingTier = (r) => {
        if (!r) return null;
        if (r >= 4.5) return { label: 'Excellent', color: 'bg-green-500', textColor: 'text-green-700' };
        if (r >= 4.0) return { label: 'Very Good', color: 'bg-emerald-500', textColor: 'text-emerald-700' };
        if (r >= 3.5) return { label: 'Good', color: 'bg-yellow-500', textColor: 'text-yellow-700' };
        return { label: 'Average', color: 'bg-gray-400', textColor: 'text-gray-600' };
    };
    const ratingTier = getRatingTier(rating);

    // Generate star display (filled stars based on rating)
    const renderStars = (r) => {
        if (!r) return null;
        const fullStars = Math.floor(r);
        const stars = [];
        for (let i = 0; i < 5; i++) {
            stars.push(
                <Star
                    key={i}
                    size={14}
                    className={i < fullStars ? 'fill-amber-400 text-amber-400' : 'fill-gray-200 text-gray-200'}
                />
            );
        }
        return stars;
    };

    return (
        <div className="my-3 w-full max-w-[680px]">
            <div className="bg-white rounded-2xl border border-[#E8E5DE] shadow-sm overflow-hidden">
                {/* Enhanced Header with Prominent Rating */}
                <div className="px-4 py-3 border-b border-[#EFEAE2]">
                    <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                            <h3 className="text-[16px] font-semibold text-[#1A1915]">{name}</h3>

                            {/* Rating Row - More Prominent */}
                            {rating && (
                                <div className="mt-2 flex items-center gap-2 flex-wrap">
                                    <div className="flex items-center gap-1">
                                        {renderStars(rating)}
                                    </div>
                                    <span className="text-[15px] font-bold text-[#1A1915]">{rating.toFixed(1)}</span>
                                    {ratingTier && (
                                        <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${ratingTier.color} text-white`}>
                                            {ratingTier.label}
                                        </span>
                                    )}
                                    {ratingCountText && (
                                        <span className="text-[12px] text-[#8C867E]">({ratingCountText} reviews)</span>
                                    )}
                                </div>
                            )}

                            {/* Type and Price */}
                            {metaLine && (
                                <div className="mt-1 text-[12px] text-[#6F6A63]">{metaLine}</div>
                            )}

                            {/* AI-Generated Signature Description (priority) or Editorial Summary */}
                            {(place.generatedSummary || editorialSummary) && (
                                <p className="mt-2 text-[13px] text-[#4C4842] leading-snug">
                                    <span className="font-medium text-[#DA7756]">✦</span>{' '}
                                    {place.generatedSummary || editorialSummary}
                                </p>
                            )}

                            {/* Services badges */}
                            <div className="mt-2 flex flex-wrap gap-1">
                                {dineIn && <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-600">Dine-in</span>}
                                {takeout && <span className="text-[10px] px-2 py-0.5 rounded-full bg-orange-50 text-orange-600">Takeout</span>}
                                {delivery && <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-50 text-green-600">Delivery</span>}
                                {servesVegetarianFood && <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-600">🥬 Vegetarian options</span>}
                            </div>
                        </div>
                        <span className="text-[11px] text-[#A7A19A] shrink-0">Google Maps</span>
                    </div>
                    {statusLabel && (
                        <div className={`mt-2 inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] ${statusTone}`}>
                            {statusLabel}
                        </div>
                    )}
                </div>

                <div className={hasPhoto ? 'grid gap-0 md:grid-cols-2' : 'grid'}>
                    <a
                        href={mapsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={hasPhoto ? 'relative block md:col-span-1' : 'relative block md:col-span-2'}
                    >
                        <div className="aspect-[4/3] w-full bg-[#F5F4F0]">
                            {apiKey && !mapFailed ? (
                                <img
                                    src={`https://maps.googleapis.com/maps/api/staticmap?center=${lat},${lng}&zoom=15&size=640x480&scale=2&maptype=roadmap&markers=color:red%7C${lat},${lng}&key=${apiKey}`}
                                    alt="Map preview"
                                    className="h-full w-full object-cover"
                                    loading="lazy"
                                    onError={() => setMapFailed(true)}
                                />
                            ) : (
                                <div className="flex h-full w-full items-center justify-center text-[#B9B3AA]">
                                    <div className="flex flex-col items-center gap-2 text-xs">
                                        <MapPin size={20} />
                                        Map preview unavailable
                                    </div>
                                </div>
                            )}
                        </div>
                        <div className="absolute inset-0 flex items-end justify-start bg-gradient-to-t from-black/40 via-black/0 to-transparent p-3">
                            <span className="inline-flex items-center gap-1 rounded-full bg-white/90 px-3 py-1 text-[12px] text-[#3E3A34] shadow-sm">
                                Open map
                                <ExternalLink size={12} />
                            </span>
                        </div>
                    </a>

                    {hasPhoto ? (
                        <a
                            href={mapsUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="relative block border-t border-[#EFEAE2] md:border-l md:border-t-0"
                        >
                            <div className="aspect-[4/3] w-full bg-[#F5F4F0]">
                                <img
                                    src={primaryPhotoUrl}
                                    alt={name}
                                    className="h-full w-full object-cover"
                                    loading="lazy"
                                    onError={() => setPhotoFailed(true)}
                                />
                            </div>
                            <div className="absolute inset-0 flex items-end bg-gradient-to-t from-black/30 via-black/0 to-transparent p-3">
                                <span className="text-[12px] text-white/90">Photo</span>
                            </div>
                        </a>
                    ) : null}
                </div>

                <div className="p-4 space-y-3">
                    <div className="flex flex-wrap gap-2">
                        <a
                            href={directionsUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 rounded-full bg-[#DA7756] px-4 py-2 text-[13px] font-medium text-white hover:bg-[#C4654A] transition-colors"
                        >
                            <Navigation size={14} />
                            Directions
                        </a>
                        {website && (
                            <a
                                href={website}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-2 rounded-full bg-[#F5F4F0] px-4 py-2 text-[13px] font-medium text-[#4C4842] hover:bg-[#EFEAE2] transition-colors"
                            >
                                <Globe size={14} />
                                Website
                            </a>
                        )}
                        {phone && (
                            <a
                                href={`tel:${phone}`}
                                className="inline-flex items-center gap-2 rounded-full bg-[#F5F4F0] px-4 py-2 text-[13px] font-medium text-[#4C4842] hover:bg-[#EFEAE2] transition-colors"
                            >
                                <Phone size={14} />
                                Call
                            </a>
                        )}
                        <a
                            href={mapsUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 rounded-full border border-[#E8E5DE] px-4 py-2 text-[13px] font-medium text-[#6F6A63] hover:bg-[#F7F5F0] transition-colors"
                        >
                            <MapPin size={14} />
                            Open in Maps
                        </a>
                    </div>

                    {address && (
                        <div className="flex items-start gap-2 text-[13px] text-[#6F6A63]">
                            <MapPin size={15} className="mt-0.5 text-[#B0AAA2]" />
                            <span className="line-clamp-2">{address}</span>
                        </div>
                    )}

                    {showDetailsToggle && (
                        <button
                            type="button"
                            onClick={() => setShowDetails((prev) => !prev)}
                            className="flex items-center gap-2 text-[12px] font-medium text-[#6F6A63] hover:text-[#3E3A34]"
                        >
                            <span>{showDetails ? 'Hide details' : 'Show details'}</span>
                            <span className={`transform transition-transform ${showDetails ? 'rotate-90' : 'rotate-0'}`}>
                                <ChevronRight size={12} />
                            </span>
                        </button>
                    )}
                </div>

                {showDetails && (
                    <div className="border-t border-[#EFEAE2] px-4 py-3 space-y-3 text-[13px] text-[#6F6A63]">
                        {phone && (
                            <div className="flex items-center gap-2">
                                <Phone size={14} className="text-[#B0AAA2]" />
                                <a href={`tel:${phone}`} className="hover:text-[#3E3A34]">
                                    {phone}
                                </a>
                            </div>
                        )}
                        {website && (
                            <div className="flex items-center gap-2">
                                <Globe size={14} className="text-[#B0AAA2]" />
                                <a
                                    href={website}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="truncate hover:text-[#3E3A34]"
                                >
                                    {website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                                </a>
                            </div>
                        )}
                        {weekdayText && weekdayText.length > 0 && (
                            <div className="flex items-start gap-2">
                                <Clock size={14} className="mt-0.5 text-[#B0AAA2]" />
                                <div className="space-y-1">
                                    {weekdayText.map((day) => (
                                        <div key={day}>{day}</div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {extraPlaces.length > 0 && (
                    <div className="border-t border-[#EFEAE2] px-4 py-3">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                            More places
                        </div>
                        <div className="mt-2 space-y-2">
                            {extraPlaces.map((item) => (
                                <a
                                    key={item.id}
                                    href={item.mapsUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center justify-between gap-3 rounded-lg border border-[#E8E5DE] px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F7F5F0]"
                                >
                                    <div className="min-w-0">
                                        <div className="truncate font-medium">{item.name}</div>
                                        <div className="mt-0.5 text-[11px] text-[#8C867E]">
                                            {[item.rating, item.type].filter(Boolean).join(' • ')}
                                        </div>
                                    </div>
                                    {item.openNow !== undefined && (
                                        <span className={`text-[11px] ${item.openNow ? 'text-[#2E6B43]' : 'text-[#B54B3D]'}`}>
                                            {item.openNow === true ? 'Open' : 'Closed'}
                                        </span>
                                    )}
                                </a>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PlaceCard;
