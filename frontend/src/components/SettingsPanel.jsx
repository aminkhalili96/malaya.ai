import React from 'react';
import { X } from 'lucide-react';

const SettingsPanel = ({
    open,
    onClose,
    settings,
    onUpdateSettings,
    preferences,
    onUpdatePreferences,
    onExportData,
    onClearData,
    sessionId,
    promptVariants,
}) => {
    if (!open) return null;

    const updateSetting = (key, value) => {
        onUpdateSettings?.({ [key]: value });
    };

    const updatePreference = (key, value) => {
        onUpdatePreferences?.({ [key]: value });
    };

    const variantOptions = Array.isArray(promptVariants) && promptVariants.length
        ? promptVariants
        : [{ key: 'default', label: 'Default', description: 'Base system prompt' }];

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
            <div className="w-full max-w-2xl rounded-2xl border border-[#E8E5DE] bg-white shadow-xl">
                <div className="flex items-center justify-between border-b border-[#EFEAE2] px-5 py-4">
                    <div>
                        <div className="text-sm uppercase tracking-[0.2em] text-[#A7A19A]">Settings</div>
                        <div className="text-lg font-semibold text-[#1A1915]">Workspace Preferences</div>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        className="rounded-full p-2 text-[#6F6A63] hover:bg-[#F5F4F0]"
                        aria-label="Close settings"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="flex px-5 py-4 border-b border-[#EFEAE2] gap-4">
                    <button className="text-sm font-medium text-[#DA7756] border-b-2 border-[#DA7756] pb-1">General</button>
                    {/* Future tab: Personalization */}
                </div>

                <div className="grid gap-6 px-5 py-6 md:grid-cols-2 max-h-[70vh] overflow-y-auto">
                    {/* Personalization Section - Full Width */}
                    <div className="col-span-2 space-y-4 rounded-xl bg-[#F9F8F6] p-4 border border-[#EFEAE2]">
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Personalization (Custom Instructions)</div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-[#4C4842]">What would you like Malaya to know about you?</label>
                            <textarea
                                value={preferences?.profile || ''}
                                onChange={(e) => updatePreference('profile', e.target.value)}
                                placeholder="I live in KL, I prefer halal food, I am a developer..."
                                className="w-full rounded-lg border border-[#E8E5DE] bg-white p-3 text-sm text-[#1A1915] min-h-[80px]"
                            />
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-[#4C4842]">How would you like Malaya to respond?</label>
                            <textarea
                                value={preferences?.instructions || ''}
                                onChange={(e) => updatePreference('instructions', e.target.value)}
                                placeholder="Be casual, answer in Manglish, keep it short..."
                                className="w-full rounded-lg border border-[#E8E5DE] bg-white p-3 text-sm text-[#1A1915] min-h-[80px]"
                            />
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Appearance</div>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>High contrast</span>
                            <input
                                type="checkbox"
                                checked={Boolean(settings?.highContrast)}
                                onChange={(event) => updateSetting('highContrast', event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>Reduce motion</span>
                            <input
                                type="checkbox"
                                checked={Boolean(settings?.reduceMotion)}
                                onChange={(event) => updateSetting('reduceMotion', event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Font size</div>
                            <select
                                value={settings?.fontScale || 'md'}
                                onChange={(event) => updateSetting('fontScale', event.target.value)}
                                className="mt-2 w-full rounded-md border border-[#E8E5DE] px-2 py-1 text-[13px]"
                            >
                                <option value="sm">Small</option>
                                <option value="md">Default</option>
                                <option value="lg">Large</option>
                            </select>
                        </div>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Density</div>
                            <select
                                value={settings?.density || 'comfortable'}
                                onChange={(event) => updateSetting('density', event.target.value)}
                                className="mt-2 w-full rounded-md border border-[#E8E5DE] px-2 py-1 text-[13px]"
                            >
                                <option value="comfortable">Comfortable</option>
                                <option value="compact">Compact</option>
                            </select>
                        </div>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Default response mode</div>
                            <select
                                value={settings?.responseMode || 'auto'}
                                onChange={(event) => updateSetting('responseMode', event.target.value)}
                                className="mt-2 w-full rounded-md border border-[#E8E5DE] px-2 py-1 text-[13px]"
                            >
                                <option value="auto">Auto</option>
                                <option value="quality">Quality</option>
                                <option value="fast">Fast</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Experience</div>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>Show thinking steps</span>
                            <input
                                type="checkbox"
                                checked={settings?.showThinking !== false}
                                onChange={(event) => updateSetting('showThinking', event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>Show response timing</span>
                            <input
                                type="checkbox"
                                checked={settings?.showLatency !== false}
                                onChange={(event) => updateSetting('showLatency', event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>Sidebar expanded</span>
                            <input
                                type="checkbox"
                                checked={settings?.sidebarCollapsed === false}
                                onChange={(event) => updateSetting('sidebarCollapsed', !event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>Use project memory</span>
                            <input
                                type="checkbox"
                                checked={settings?.projectMemoryEnabled !== false}
                                onChange={(event) => updateSetting('projectMemoryEnabled', event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Prompt variant</div>
                            <select
                                value={settings?.promptVariant || 'default'}
                                onChange={(event) => updateSetting('promptVariant', event.target.value)}
                                className="mt-2 w-full rounded-md border border-[#E8E5DE] px-2 py-1 text-[13px]"
                            >
                                {variantOptions.map((variant) => (
                                    <option key={variant.key} value={variant.key}>
                                        {variant.label || variant.key}
                                    </option>
                                ))}
                            </select>
                            {variantOptions.find((variant) => variant.key === (settings?.promptVariant || 'default'))?.description && (
                                <div className="mt-2 text-[12px] text-[#8C867E]">
                                    {variantOptions.find((variant) => variant.key === (settings?.promptVariant || 'default'))?.description}
                                </div>
                            )}
                        </div>
                        <label className="flex items-center justify-between rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <span>Redact PII in local storage</span>
                            <input
                                type="checkbox"
                                checked={Boolean(settings?.redactPii)}
                                onChange={(event) => updateSetting('redactPii', event.target.checked)}
                                className="h-4 w-4 accent-[#DA7756]"
                            />
                        </label>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Retention</div>
                            <div className="mt-2 flex items-center gap-3 text-[13px] text-[#6F6A63]">
                                <span>Auto-delete chats after</span>
                                <input
                                    type="number"
                                    min="0"
                                    value={settings?.retentionDays || 0}
                                    onChange={(event) => updateSetting('retentionDays', Number(event.target.value || 0))}
                                    className="w-20 rounded-md border border-[#E8E5DE] px-2 py-1 text-[13px]"
                                />
                                <span>days</span>
                            </div>
                        </div>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Session</div>
                            <div className="mt-2 text-[13px] text-[#6F6A63]">Session ID: {sessionId || 'unknown'}</div>
                        </div>
                        <div className="rounded-lg border border-[#EFEAE2] px-4 py-3 text-sm text-[#4C4842]">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">Shortcuts</div>
                            <div className="mt-2 space-y-1 text-[13px] text-[#6F6A63]">
                                <div>Command palette: ⌘K / Ctrl+K</div>
                                <div>Open settings: ⌘, / Ctrl+,</div>
                                <div>New chat: click New chat</div>
                                <div>Stop streaming: Esc or Stop button</div>
                            </div>
                        </div>
                        <div className="space-y-2">
                            <button
                                type="button"
                                onClick={onExportData}
                                className="w-full rounded-lg border border-[#E8E5DE] px-3 py-2 text-[13px] text-[#3E3A34] hover:bg-[#F7F5F0]"
                            >
                                Export local data
                            </button>
                            <button
                                type="button"
                                onClick={onClearData}
                                className="w-full rounded-lg border border-[#F1D6D1] px-3 py-2 text-[13px] text-[#B54B3D] hover:bg-[#FCEDEA]"
                            >
                                Clear local data
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SettingsPanel;
