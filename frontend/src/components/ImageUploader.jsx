/**
 * ImageUploader Component
 * Allows users to upload images for translation via Snap & Translate feature.
 */
import React, { useRef, useState } from 'react';
import { Camera, Upload, X, Loader2 } from 'lucide-react';

const API_KEY = import.meta.env.VITE_API_KEY;

const ImageUploader = ({ onTranslationResult, onClose }) => {
    const [preview, setPreview] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);

    const handleFileSelect = async (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Create preview
        const reader = new FileReader();
        reader.onload = (e) => {
            setPreview(e.target.result);
        };
        reader.readAsDataURL(file);
    };

    const handleTranslate = async () => {
        if (!preview) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/vision/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
                body: JSON.stringify({
                    image_base64: preview,
                    target_language: 'English'
                }),
            });

            if (!response.ok) {
                throw new Error('Translation failed');
            }

            const data = await response.json();
            setResult(data);
            onTranslationResult?.(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAnalyzeMenu = async () => {
        if (!preview) return;

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/vision/menu', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
                body: JSON.stringify({
                    image_base64: preview,
                }),
            });

            if (!response.ok) {
                throw new Error('Menu analysis failed');
            }

            const data = await response.json();
            setResult(data);
            onTranslationResult?.(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl w-full max-w-lg shadow-xl">
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-[#E8E5DE]">
                    <div>
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">
                            Snap & Translate
                        </div>
                        <div className="text-lg font-semibold text-[#1A1915]">
                            Translate Signboards & Menus
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
                    {!preview ? (
                        <div
                            onClick={() => fileInputRef.current?.click()}
                            className="border-2 border-dashed border-[#E8E5DE] rounded-xl p-8 text-center cursor-pointer hover:border-[#DA7756] transition-colors"
                        >
                            <Camera size={48} className="mx-auto text-[#A7A19A] mb-3" />
                            <div className="text-[#4C4842] font-medium">
                                Click to upload an image
                            </div>
                            <div className="text-[13px] text-[#A7A19A] mt-1">
                                Supports signboards, menus, Jawi, Chinese text
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <img
                                src={preview}
                                alt="Preview"
                                className="w-full rounded-xl max-h-64 object-contain bg-[#F5F4F0]"
                            />

                            <div className="flex gap-2">
                                <button
                                    onClick={handleTranslate}
                                    disabled={isLoading}
                                    className="flex-1 flex items-center justify-center gap-2 bg-[#DA7756] text-white py-3 rounded-xl font-medium hover:bg-[#C4654A] disabled:opacity-50"
                                >
                                    {isLoading ? (
                                        <Loader2 size={18} className="animate-spin" />
                                    ) : (
                                        'Translate Text'
                                    )}
                                </button>
                                <button
                                    onClick={handleAnalyzeMenu}
                                    disabled={isLoading}
                                    className="flex-1 flex items-center justify-center gap-2 border border-[#DA7756] text-[#DA7756] py-3 rounded-xl font-medium hover:bg-[#FDF8F6] disabled:opacity-50"
                                >
                                    {isLoading ? (
                                        <Loader2 size={18} className="animate-spin" />
                                    ) : (
                                        'Analyze Menu'
                                    )}
                                </button>
                            </div>

                            <button
                                onClick={() => {
                                    setPreview(null);
                                    setResult(null);
                                }}
                                className="w-full text-[13px] text-[#6F6A63] hover:text-[#3E3A34]"
                            >
                                Choose different image
                            </button>
                        </div>
                    )}

                    {/* Result Display */}
                    {result && (
                        <div className="bg-[#F9F8F6] rounded-xl p-4 space-y-3">
                            {result.original_text && (
                                <div>
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Original ({result.language_detected})
                                    </div>
                                    <div className="text-[#4C4842] mt-1">
                                        {result.original_text}
                                    </div>
                                </div>
                            )}
                            {result.translated_text && (
                                <div>
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Translation
                                    </div>
                                    <div className="text-[#1A1915] font-medium mt-1">
                                        {result.translated_text}
                                    </div>
                                </div>
                            )}
                            {result.context && (
                                <div>
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Cultural Context
                                    </div>
                                    <div className="text-[#6F6A63] text-[13px] mt-1">
                                        {result.context}
                                    </div>
                                </div>
                            )}
                            {result.items && (
                                <div>
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Menu Items
                                    </div>
                                    <div className="mt-2 space-y-2">
                                        {result.items.map((item, idx) => (
                                            <div key={idx} className="flex justify-between items-center">
                                                <span className="text-[#4C4842]">{item.name}</span>
                                                <span className="text-[#DA7756] font-medium">{item.price}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {error && (
                        <div className="bg-red-50 text-red-600 rounded-xl p-4 text-[13px]">
                            {error}
                        </div>
                    )}
                </div>

                <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileSelect}
                    className="hidden"
                />
            </div>
        </div>
    );
};

export default ImageUploader;
