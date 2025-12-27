import React, { useEffect, useMemo, useState } from 'react';
import { Command, Search } from 'lucide-react';
import clsx from 'clsx';

const CommandPalette = ({ open, onClose, items = [] }) => {
    const [query, setQuery] = useState('');
    const normalized = query.trim().toLowerCase();

    useEffect(() => {
        if (open) {
            setQuery('');
        }
    }, [open]);

    useEffect(() => {
        if (!open) return;
        const handleKeyDown = (event) => {
            if (event.key === 'Escape') {
                onClose?.();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [open, onClose]);

    const filteredItems = useMemo(() => {
        if (!normalized) return items;
        return items.filter((item) => {
            const haystack = `${item.label} ${item.description || ''} ${item.keywords || ''}`.toLowerCase();
            return haystack.includes(normalized);
        });
    }, [items, normalized]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 px-4 pt-20">
            <div className="w-full max-w-xl rounded-2xl border border-[#E8E5DE] bg-white shadow-xl">
                <div className="flex items-center gap-2 border-b border-[#EFEAE2] px-4 py-3 text-[#6F6A63]">
                    <Command size={16} />
                    <Search size={16} />
                    <input
                        autoFocus
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        placeholder="Search commands, chats, projects"
                        className="w-full bg-transparent text-[14px] text-[#1A1915] focus:outline-none"
                    />
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-full px-2 py-1 text-[12px] text-[#6F6A63] hover:bg-[#F5F4F0]"
                        aria-label="Close command palette"
                    >
                        Esc
                    </button>
                </div>
                <div className="max-h-[360px] overflow-y-auto py-2">
                    {filteredItems.length === 0 && (
                        <div className="px-4 py-3 text-[13px] text-[#A7A19A]">No matches.</div>
                    )}
                    {filteredItems.map((item) => (
                        <button
                            key={item.id}
                            type="button"
                            onClick={() => {
                                item.onSelect?.();
                                onClose();
                            }}
                            className={clsx(
                                "flex w-full items-start justify-between gap-3 px-4 py-2 text-left text-[14px] text-[#3E3A34] hover:bg-[#F7F5F0]"
                            )}
                        >
                            <div>
                                <div className="font-medium">{item.label}</div>
                                {item.description && (
                                    <div className="text-[12px] text-[#8C867E]">{item.description}</div>
                                )}
                            </div>
                            {item.shortcut && (
                                <span className="rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[11px] text-[#6F6A63]">
                                    {item.shortcut}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default CommandPalette;
