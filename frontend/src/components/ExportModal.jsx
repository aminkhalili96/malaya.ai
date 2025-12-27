/**
 * Export Modal Component
 * Exports chat history to PDF or Word document
 */
import React, { useState } from 'react';
import { X, FileText, Download, Check } from 'lucide-react';

const ExportModal = ({ conversation, onClose }) => {
    const [format, setFormat] = useState('pdf');
    const [includeTimestamps, setIncludeTimestamps] = useState(true);
    const [includeMetadata, setIncludeMetadata] = useState(true);
    const [isExporting, setIsExporting] = useState(false);
    const [exportSuccess, setExportSuccess] = useState(false);

    const handleExport = async () => {
        setIsExporting(true);

        try {
            // Prepare content
            const content = formatConversation(conversation, includeTimestamps, includeMetadata);

            if (format === 'pdf') {
                await exportToPDF(content, conversation.title);
            } else if (format === 'docx') {
                await exportToWord(content, conversation.title);
            } else {
                await exportToMarkdown(content, conversation.title);
            }

            setExportSuccess(true);
            setTimeout(() => onClose(), 1500);
        } catch (error) {
            console.error('Export failed:', error);
        } finally {
            setIsExporting(false);
        }
    };

    const formatConversation = (conv, timestamps, metadata) => {
        let content = `# ${conv.title || 'Conversation'}\n\n`;

        if (metadata) {
            content += `**Created:** ${new Date(conv.createdAt).toLocaleString()}\n`;
            content += `**Messages:** ${conv.messages?.length || 0}\n\n`;
            content += '---\n\n';
        }

        (conv.messages || []).forEach((msg, idx) => {
            const role = msg.role === 'user' ? '👤 User' : '🤖 Assistant';
            content += `### ${role}\n\n`;

            if (timestamps && msg.timestamp) {
                content += `*${new Date(msg.timestamp).toLocaleString()}*\n\n`;
            }

            content += `${msg.content}\n\n`;

            if (idx < conv.messages.length - 1) {
                content += '---\n\n';
            }
        });

        return content;
    };

    const exportToPDF = async (content, title) => {
        // Using jsPDF (would need to be installed)
        // For now, create a printable HTML and use browser print
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>${title}</title>
                <style>
                    body { font-family: system-ui, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
                    h1 { color: #1a1a1a; }
                    h3 { color: #4a4a4a; margin-top: 24px; }
                    hr { border: none; border-top: 1px solid #e0e0e0; margin: 16px 0; }
                    pre { background: #f5f5f5; padding: 12px; border-radius: 8px; overflow-x: auto; }
                </style>
            </head>
            <body>
                ${content.replace(/\n/g, '<br>').replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')}
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    };

    const exportToWord = async (content, title) => {
        // Create a simple HTML blob that Word can open
        const html = `
            <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word'>
            <head><meta charset="utf-8"><title>${title}</title></head>
            <body>${content.replace(/\n/g, '<br>')}</body>
            </html>
        `;

        const blob = new Blob([html], { type: 'application/msword' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title}.doc`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const exportToMarkdown = async (content, title) => {
        const blob = new Blob([content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${title}.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div
                className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6"
                style={{ background: 'var(--surface-primary)' }}
            >
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
                        Export Conversation
                    </h2>
                    <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100">
                        <X size={20} />
                    </button>
                </div>

                {exportSuccess ? (
                    <div className="text-center py-8">
                        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Check size={32} className="text-green-500" />
                        </div>
                        <p className="text-lg font-medium">Export Complete!</p>
                    </div>
                ) : (
                    <>
                        {/* Format Selection */}
                        <div className="mb-6">
                            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--text-secondary)' }}>
                                Export Format
                            </label>
                            <div className="grid grid-cols-3 gap-2">
                                {[
                                    { id: 'pdf', label: 'PDF', icon: FileText },
                                    { id: 'docx', label: 'Word', icon: FileText },
                                    { id: 'md', label: 'Markdown', icon: FileText },
                                ].map((opt) => (
                                    <button
                                        key={opt.id}
                                        onClick={() => setFormat(opt.id)}
                                        className={`p-3 rounded-lg border-2 flex flex-col items-center gap-1 transition-all ${format === opt.id
                                                ? 'border-[#DA7756] bg-[#DA7756]/10'
                                                : 'border-gray-200 hover:border-gray-300'
                                            }`}
                                    >
                                        <opt.icon size={20} style={{ color: format === opt.id ? '#DA7756' : 'var(--text-tertiary)' }} />
                                        <span className="text-sm">{opt.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Options */}
                        <div className="space-y-3 mb-6">
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={includeTimestamps}
                                    onChange={(e) => setIncludeTimestamps(e.target.checked)}
                                    className="w-4 h-4 rounded accent-[#DA7756]"
                                />
                                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    Include timestamps
                                </span>
                            </label>
                            <label className="flex items-center gap-3 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={includeMetadata}
                                    onChange={(e) => setIncludeMetadata(e.target.checked)}
                                    className="w-4 h-4 rounded accent-[#DA7756]"
                                />
                                <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                                    Include metadata
                                </span>
                            </label>
                        </div>

                        {/* Export Button */}
                        <button
                            onClick={handleExport}
                            disabled={isExporting}
                            className="w-full py-3 rounded-lg text-white font-medium flex items-center justify-center gap-2"
                            style={{ background: '#DA7756' }}
                        >
                            {isExporting ? (
                                'Exporting...'
                            ) : (
                                <>
                                    <Download size={18} />
                                    Export as {format.toUpperCase()}
                                </>
                            )}
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};

export default ExportModal;
