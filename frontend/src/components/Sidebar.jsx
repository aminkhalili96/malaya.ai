
import React from 'react';
import { MessageSquare, Database, FileText, Search } from 'lucide-react';
import clsx from 'clsx';

const Sidebar = ({ mode, setMode }) => {
    const modes = [
        { id: 'chat', icon: MessageSquare },
        { id: 'rag', icon: Database },
        { id: 'summary', icon: FileText },
    ];

    return (
        <div className="w-14 bg-[#FAF9F7] border-r border-[#E8E5DE] flex flex-col h-full py-4">
            {/* Top icons */}
            <div className="flex flex-col items-center gap-2 px-2">
                {/* Sidebar toggle - just decorative */}
                <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                        <rect x="3" y="3" width="18" height="18" rx="2" />
                        <path d="M9 3v18" />
                    </svg>
                </button>

                {/* Mode icons */}
                {modes.map((m) => (
                    <button
                        key={m.id}
                        onClick={() => setMode(m.id)}
                        className={clsx(
                            "p-2 rounded-lg transition-colors",
                            mode === m.id
                                ? "bg-[#DA7756] text-white"
                                : "text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0]"
                        )}
                    >
                        <m.icon size={18} strokeWidth={1.5} />
                    </button>
                ))}

                {/* Search */}
                <button className="p-2 text-[#706F6C] hover:text-[#1A1915] hover:bg-[#F5F4F0] rounded-lg transition-colors">
                    <Search size={18} strokeWidth={1.5} />
                </button>
            </div>

            {/* Spacer */}
            <div className="flex-1" />

            {/* Bottom - User avatar */}
            <div className="flex flex-col items-center px-2">
                <div className="w-8 h-8 rounded-full bg-[#DA7756] flex items-center justify-center text-white text-sm font-medium">
                    A
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
