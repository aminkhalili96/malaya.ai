/**
 * Price Comparison Component
 * Searches Shopee and Lazada for products
 */
import React, { useState } from 'react';
import { X, Search, ShoppingBag, ExternalLink, TrendingDown, Loader2 } from 'lucide-react';

const PriceComparison = ({ onClose }) => {
    const [query, setQuery] = useState('');
    const [maxBudget, setMaxBudget] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSearch = async () => {
        if (!query.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/price/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query.trim(),
                    max_budget: maxBudget ? parseFloat(maxBudget) : null,
                    max_results: 5
                })
            });

            if (!response.ok) throw new Error('Search failed');

            const data = await response.json();
            setResults(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const formatPrice = (price) => `RM ${price?.toFixed(2) || '0.00'}`;

    const popularSearches = [
        'iPhone 15 Pro',
        'MacBook Air M3',
        'Samsung S24',
        'AirPods Pro',
        'Nintendo Switch'
    ];

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div
                className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col"
                style={{ background: 'var(--surface-primary)' }}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b" style={{ borderColor: 'var(--border-primary)' }}>
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ background: '#FF5722' }}>
                            <ShoppingBag size={20} className="text-white" />
                        </div>
                        <div>
                            <h2 className="font-semibold" style={{ color: 'var(--text-primary)' }}>Price Compare</h2>
                            <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>Shopee & Lazada</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100">
                        <X size={20} />
                    </button>
                </div>

                {/* Search */}
                <div className="p-4 space-y-4">
                    <div className="flex gap-2">
                        <div className="flex-1 relative">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                                placeholder="Search for products..."
                                className="w-full px-4 py-3 rounded-lg border"
                                style={{
                                    background: 'var(--input-bg)',
                                    borderColor: 'var(--input-border)',
                                    color: 'var(--text-primary)'
                                }}
                            />
                        </div>
                        <input
                            type="number"
                            value={maxBudget}
                            onChange={(e) => setMaxBudget(e.target.value)}
                            placeholder="Max RM"
                            className="w-24 px-3 py-3 rounded-lg border"
                            style={{
                                background: 'var(--input-bg)',
                                borderColor: 'var(--input-border)',
                                color: 'var(--text-primary)'
                            }}
                        />
                        <button
                            onClick={handleSearch}
                            disabled={loading || !query.trim()}
                            className="px-6 py-3 rounded-lg text-white flex items-center gap-2"
                            style={{ background: '#FF5722' }}
                        >
                            {loading ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} />}
                            Search
                        </button>
                    </div>

                    {/* Popular Searches */}
                    {!results && (
                        <div className="flex flex-wrap gap-2">
                            {popularSearches.map((term) => (
                                <button
                                    key={term}
                                    onClick={() => setQuery(term)}
                                    className="px-3 py-1.5 rounded-full text-xs border"
                                    style={{ borderColor: 'var(--border-primary)', color: 'var(--text-secondary)' }}
                                >
                                    {term}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                {/* Results */}
                <div className="flex-1 overflow-y-auto p-4">
                    {error && (
                        <div className="text-center py-8 text-red-500">
                            {error}
                        </div>
                    )}

                    {results && (
                        <div className="space-y-4">
                            {/* Best Deal */}
                            {results.best_deal && (
                                <div
                                    className="p-4 rounded-lg border-2"
                                    style={{ borderColor: '#4CAF50', background: 'rgba(76, 175, 80, 0.05)' }}
                                >
                                    <div className="flex items-center gap-2 mb-2">
                                        <TrendingDown size={16} className="text-green-500" />
                                        <span className="text-sm font-medium text-green-600">Best Deal</span>
                                    </div>
                                    <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
                                        {results.best_deal.name}
                                    </p>
                                    <p className="text-lg font-bold text-green-600">
                                        {formatPrice(results.best_deal.price)}
                                    </p>
                                    <p className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                        on {results.best_deal.platform}
                                    </p>
                                </div>
                            )}

                            {/* Price Range */}
                            {results.price_range?.min && (
                                <div className="flex justify-between text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    <span>Price range: {formatPrice(results.price_range.min)} - {formatPrice(results.price_range.max)}</span>
                                    <span>{results.total_found} results</span>
                                </div>
                            )}

                            {/* All Results */}
                            <div className="space-y-3">
                                {results.all_results?.map((item, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-start gap-4 p-4 rounded-lg border"
                                        style={{ borderColor: 'var(--border-primary)' }}
                                    >
                                        {item.image && (
                                            <img
                                                src={item.image}
                                                alt={item.name}
                                                className="w-16 h-16 object-cover rounded-lg"
                                            />
                                        )}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-sm truncate" style={{ color: 'var(--text-primary)' }}>
                                                {item.name}
                                            </p>
                                            <p className="text-lg font-bold" style={{ color: '#DA7756' }}>
                                                {formatPrice(item.price)}
                                            </p>
                                            {item.original_price && item.original_price > item.price && (
                                                <p className="text-xs line-through" style={{ color: 'var(--text-tertiary)' }}>
                                                    {formatPrice(item.original_price)}
                                                </p>
                                            )}
                                            <div className="flex items-center gap-2 mt-1">
                                                <span
                                                    className="text-xs px-2 py-0.5 rounded-full"
                                                    style={{
                                                        background: item.platform === 'Shopee' ? '#FF5722' : '#1A0DAB',
                                                        color: 'white'
                                                    }}
                                                >
                                                    {item.platform}
                                                </span>
                                                {item.rating > 0 && (
                                                    <span className="text-xs" style={{ color: 'var(--text-tertiary)' }}>
                                                        ⭐ {item.rating.toFixed(1)}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        {item.url && (
                                            <a
                                                href={item.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-2 rounded-lg hover:bg-gray-100"
                                            >
                                                <ExternalLink size={18} />
                                            </a>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PriceComparison;
