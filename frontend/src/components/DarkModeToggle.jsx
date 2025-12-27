/**
 * Dark Mode Toggle Component
 * Switches between light and dark (Claude) themes
 */
import React from 'react';
import { Moon, Sun } from 'lucide-react';
import useStore from '../store/useStore';

const DarkModeToggle = () => {
    const { settings, updateSettings } = useStore();
    const isDark = settings?.theme === 'dark';

    const toggleTheme = () => {
        const newTheme = isDark ? 'light' : 'dark';
        updateSettings({ theme: newTheme });
        document.documentElement.setAttribute('data-theme', newTheme);
    };

    // Initialize theme on mount
    React.useEffect(() => {
        const theme = settings?.theme || 'light';
        document.documentElement.setAttribute('data-theme', theme);
    }, [settings?.theme]);

    return (
        <button
            onClick={toggleTheme}
            className="p-2 rounded-lg transition-colors"
            style={{
                background: isDark ? 'var(--bg-hover)' : 'var(--bg-tertiary)',
            }}
            title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
            {isDark ? (
                <Sun size={18} style={{ color: 'var(--accent-primary)' }} />
            ) : (
                <Moon size={18} style={{ color: 'var(--text-tertiary)' }} />
            )}
        </button>
    );
};

export default DarkModeToggle;
