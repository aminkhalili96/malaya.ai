
import React, { useEffect, useMemo, useState } from 'react';
import {
    Archive,
    Check,
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    Code,
    ExternalLink,
    FileText,
    Folder,
    FolderPlus,
    FolderOpen,
    Inbox,
    MessageSquare,
    MoreHorizontal,
    Plus,
    Pin,
    Search,
    Settings,
    Tag,
    Trash2,
    Edit3,
    CheckSquare,
    Square,
    Sparkles,
    X,
} from 'lucide-react';
import clsx from 'clsx';
import { embedText, cosineSimilarity } from '../utils/semanticSearch';

const API_KEY = import.meta.env.VITE_API_KEY;

const Sidebar = ({
    conversations,
    activeId,
    onSelectConversation,
    onNewChat,
    onArchiveConversation,
    onDeleteConversation,
    onAssignProject,
    onCreateProject,
    onSaveArtifact,
    onSaveCode,
    onRenameConversation,
    onTogglePinConversation,
    onUpdateTags,
    folders,
    onCreateFolder,
    onRenameFolder,
    onDeleteFolder,
    onAssignFolder,
    onBulkAction,
    projects,
    artifacts,
    codeSnippets,
    onUpdateProject,
    onAddProjectFiles,
    onRemoveProjectFile,
    onOpenAdmin,
    onOpenSettings,
    collapsed,
    onToggleCollapse,
    width,
    onResizeStart,
    semanticSearch,
    onToggleSemanticSearch,
    promptVariants,
}) => {
    const [menuOpenId, setMenuOpenId] = useState(null);
    const [projectMenuOpenId, setProjectMenuOpenId] = useState(null);
    const [projectDraft, setProjectDraft] = useState('');
    const [projectDraftId, setProjectDraftId] = useState(null);
    const [projectComposerOpen, setProjectComposerOpen] = useState(false);
    const [projectComposerDraft, setProjectComposerDraft] = useState('');
    const [activeSection, setActiveSection] = useState('chats');
    const [recentsOpen, setRecentsOpen] = useState(true);
    const [recentsLimit, setRecentsLimit] = useState(60);
    const [searchQuery, setSearchQuery] = useState('');
    const [projectViewId, setProjectViewId] = useState(null);
    const [folderDraft, setFolderDraft] = useState('');
    const [activeFolderId, setActiveFolderId] = useState(null);
    const [bulkMode, setBulkMode] = useState(false);
    const [selectedIds, setSelectedIds] = useState([]);
    const [renameId, setRenameId] = useState(null);
    const [renameDraft, setRenameDraft] = useState('');
    const [tagEditorId, setTagEditorId] = useState(null);
    const [tagDraft, setTagDraft] = useState('');
    const [folderMenuOpenId, setFolderMenuOpenId] = useState(null);
    const [activeTag, setActiveTag] = useState('');
    const [projectMemory, setProjectMemory] = useState({});
    const safeProjects = Array.isArray(projects) ? projects : [];
    const safeFolders = Array.isArray(folders) ? folders : [];
    const safeArtifacts = Array.isArray(artifacts) ? artifacts : [];
    const safeCodeSnippets = Array.isArray(codeSnippets) ? codeSnippets : [];
    const isCollapsed = Boolean(collapsed);
    const semanticEnabled = Boolean(semanticSearch);
    const activeConversations = conversations.filter((conv) => !conv.archived);
    const archivedConversations = conversations.filter((conv) => conv.archived);
    const showConversations = activeSection === 'chats' || activeSection === 'archive';
    const baseConversations = activeSection === 'archive' ? archivedConversations : activeConversations;
    const filteredByFolder = activeFolderId
        ? baseConversations.filter((conv) => conv.folderId === activeFolderId)
        : baseConversations;
    const filteredByTag = activeTag
        ? filteredByFolder.filter((conv) => (conv.tags || []).includes(activeTag))
        : filteredByFolder;
    const visibleConversations = useMemo(() => {
        return [...filteredByTag].sort((a, b) => {
            if (a.pinned && !b.pinned) return -1;
            if (!a.pinned && b.pinned) return 1;
            const aTime = new Date(a.updatedAt || a.createdAt || 0).getTime();
            const bTime = new Date(b.updatedAt || b.createdAt || 0).getTime();
            return bTime - aTime;
        });
    }, [filteredByTag]);
    const normalizedSearch = searchQuery.trim().toLowerCase();
    const filteredConversations = useMemo(() => {
        if (!normalizedSearch) return visibleConversations;

        const keywordFilter = (conv) => {
            const title = (conv.title || '').toLowerCase();
            const tags = (conv.tags || []).join(' ').toLowerCase();
            const folderLabel = conv.folderId
                ? (safeFolders.find((folder) => folder.id === conv.folderId)?.name || '').toLowerCase()
                : '';
            if (title.includes(normalizedSearch)) return true;
            if (tags.includes(normalizedSearch)) return true;
            if (folderLabel.includes(normalizedSearch)) return true;
            return (conv.messages || []).some((msg) => (
                (msg.content || '').toLowerCase().includes(normalizedSearch)
            ));
        };

        if (!semanticEnabled) {
            return visibleConversations.filter(keywordFilter);
        }

        const queryVec = embedText(normalizedSearch);
        const scored = visibleConversations.map((conv) => {
            const recentMessages = (conv.messages || [])
                .slice(-6)
                .map((msg) => msg.content || '')
                .join(' ');
            const tagText = (conv.tags || []).join(' ');
            const text = `${conv.title || ''} ${tagText} ${recentMessages}`.trim();
            return {
                conv,
                score: cosineSimilarity(queryVec, embedText(text)),
            };
        });

        const semanticMatches = scored
            .filter((item) => item.score >= 0.12)
            .sort((a, b) => b.score - a.score)
            .map((item) => item.conv);

        return semanticMatches.length ? semanticMatches : visibleConversations.filter(keywordFilter);
    }, [visibleConversations, normalizedSearch, safeFolders, semanticEnabled]);
    const limitedConversations = filteredConversations.slice(0, recentsLimit);
    const hasMoreRecents = filteredConversations.length > recentsLimit;
    const sectionTitle = activeSection === 'archive' ? 'Archived' : 'Recents';
    const emptyMessage = normalizedSearch
        ? 'No chats match your search.'
        : (activeSection === 'archive' ? 'No archived chats yet.' : 'No conversations yet.');
    const navItems = [
        { key: 'chats', label: 'Chats', icon: MessageSquare },
        { key: 'archive', label: 'Archive', icon: Archive, badge: archivedConversations.length },
        { key: 'projects', label: 'Projects', icon: Folder },
        { key: 'artifacts', label: 'Artifacts', icon: FileText },
        { key: 'code', label: 'Code', icon: Code },
    ];
    const projectLookup = useMemo(() => new Map(safeProjects.map((project) => [project.id, project])), [safeProjects]);
    const projectCounts = useMemo(() => {
        const counts = new Map(safeProjects.map((project) => [project.id, 0]));
        conversations.forEach((conv) => {
            if (!conv.projectId) return;
            const current = counts.get(conv.projectId);
            if (current !== undefined) {
                counts.set(conv.projectId, current + 1);
            }
        });
        return counts;
    }, [safeProjects, conversations]);
    const sortedArtifacts = useMemo(() => (
        [...safeArtifacts].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    ), [safeArtifacts]);
    const sortedCode = useMemo(() => (
        [...safeCodeSnippets].sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    ), [safeCodeSnippets]);
    const promptVariantOptions = Array.isArray(promptVariants) && promptVariants.length
        ? promptVariants
        : [{ key: 'default', label: 'Default', description: 'Base system prompt' }];
    const allTags = useMemo(() => {
        const tagSet = new Set();
        conversations.forEach((conv) => {
            (conv.tags || []).forEach((tag) => tagSet.add(tag));
        });
        return Array.from(tagSet).sort();
    }, [conversations]);

    useEffect(() => {
        const handleWindowClick = (event) => {
            if (!event.target.closest('[data-menu-root]')) {
                setMenuOpenId(null);
                setProjectMenuOpenId(null);
                setProjectDraft('');
                setProjectDraftId(null);
                setFolderMenuOpenId(null);
                setTagEditorId(null);
            }
        };
        window.addEventListener('click', handleWindowClick);
        return () => window.removeEventListener('click', handleWindowClick);
    }, []);

    const downloadFile = (filename, content, type = 'application/json') => {
        const blob = new Blob([content], { type });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    };

    const toMarkdown = (conv) => {
        const lines = [`# ${conv.title || 'New chat'}`, ''];
        (conv.messages || []).forEach((msg) => {
            const role = msg.role === 'assistant' ? 'Assistant' : 'User';
            lines.push(`**${role}:**`);
            lines.push(msg.content || '');
            lines.push('');
        });
        return lines.join('\n');
    };

    const handleShare = async (payload, type) => {
        try {
            const res = await fetch('/api/chat/share', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
                body: JSON.stringify({ type, payload }),
            });
            if (!res.ok) throw new Error('Failed to create share link');
            const data = await res.json();
            const url = `${window.location.origin}/api/chat/share/${data.share_id}`;
            await navigator.clipboard.writeText(url);
            return url;
        } catch (error) {
            console.error(error);
            return null;
        }
    };

    useEffect(() => {
        if (activeSection !== 'projects') {
            setProjectViewId(null);
        }
    }, [activeSection]);

    useEffect(() => {
        if (!projectViewId) return;
        const fetchMemory = async () => {
            try {
                const res = await fetch(`/api/chat/projects/${projectViewId}/memory`, {
                    headers: {
                        ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                    },
                });
                if (!res.ok) return;
                const data = await res.json();
                setProjectMemory((prev) => ({ ...prev, [projectViewId]: data }));
            } catch (error) {
                console.error(error);
            }
        };
        fetchMemory();
    }, [projectViewId]);

    useEffect(() => {
        if (!showConversations) {
            setActiveFolderId(null);
            setActiveTag('');
        }
    }, [showConversations]);

    useEffect(() => {
        if (showConversations) {
            setRecentsLimit(60);
        }
    }, [showConversations, activeSection]);

    useEffect(() => {
        if (!showConversations) {
            setSearchQuery('');
        }
    }, [showConversations]);

    useEffect(() => {
        setSelectedIds([]);
        setBulkMode(false);
    }, [activeSection]);

    useEffect(() => {
        if (!menuOpenId) {
            setProjectMenuOpenId(null);
            setProjectDraft('');
            setProjectDraftId(null);
            setFolderMenuOpenId(null);
            setTagEditorId(null);
        } else if (projectMenuOpenId && projectMenuOpenId !== menuOpenId) {
            setProjectMenuOpenId(null);
            setProjectDraft('');
            setProjectDraftId(null);
        }
    }, [menuOpenId, projectMenuOpenId]);

    const handleRowKeyDown = (event, conversationId) => {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            setMenuOpenId(null);
            onSelectConversation(conversationId);
        }
    };

    const handleAssignProject = (conversationId, projectId) => {
        if (onAssignProject) {
            onAssignProject(conversationId, projectId);
        }
        setProjectMenuOpenId(null);
        setProjectDraft('');
        setProjectDraftId(null);
        setMenuOpenId(null);
    };

    const toggleSelected = (conversationId) => {
        setSelectedIds((prev) => (
            prev.includes(conversationId)
                ? prev.filter((id) => id !== conversationId)
                : [...prev, conversationId]
        ));
    };

    const clearSelection = () => {
        setSelectedIds([]);
        setBulkMode(false);
    };

    const handleCreateProject = (name, conversationId) => {
        if (!onCreateProject) return null;
        const projectId = onCreateProject(name);
        if (projectId && conversationId) {
            handleAssignProject(conversationId, projectId);
        }
        return projectId;
    };

    const handleCreateFolder = () => {
        if (!onCreateFolder || !folderDraft.trim()) return;
        const folderId = onCreateFolder(folderDraft);
        if (folderId) {
            setActiveFolderId(folderId);
        }
        setFolderDraft('');
    };

    const handleRenameConversationLocal = (conversationId, title) => {
        onRenameConversation?.(conversationId, title);
        setRenameId(null);
        setRenameDraft('');
        setMenuOpenId(null);
    };

    const handleUpdateTagsLocal = (conversationId) => {
        const tags = tagDraft.split(',').map((tag) => tag.trim()).filter(Boolean);
        onUpdateTags?.(conversationId, tags);
        setTagEditorId(null);
        setTagDraft('');
    };

    const runBulkAction = (action, folderId = null) => {
        if (!onBulkAction) return;
        onBulkAction({ action, ids: selectedIds, folderId });
        clearSelection();
    };

    const readFileAsText = (file) => new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = () => reject(reader.error);
        reader.readAsText(file);
    });

    const handleProjectFiles = async (event, projectId) => {
        const files = Array.from(event.target.files || []);
        if (!files.length) return;
        const payload = [];
        for (const file of files) {
            if (!file.type.startsWith('text/') && !file.type.includes('json') && !file.type.includes('csv')) {
                continue;
            }
            try {
                let content = await readFileAsText(file);
                if (content.length > 12000) {
                    content = content.slice(0, 12000);
                }
                payload.push({
                    id: `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
                    name: file.name,
                    content,
                    mimeType: file.type,
                    size: file.size,
                });
            } catch (error) {
                console.error(error);
            }
        }
        onAddProjectFiles?.(projectId, payload);
        event.target.value = '';
    };

    const handleClearProjectMemory = async (projectId) => {
        try {
            await fetch(`/api/chat/projects/${projectId}/memory`, {
                method: 'DELETE',
                headers: {
                    ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
                },
            });
            setProjectMemory((prev) => ({
                ...prev,
                [projectId]: { summary: '', message_count: 0 },
            }));
        } catch (error) {
            console.error(error);
        }
    };

    const renderProjectPicker = (conv) => {
        if (projectMenuOpenId !== conv.id) return null;
        const selectedProjectId = conv.projectId || null;
        const hasProjects = safeProjects.length > 0;

        return (
            <div className="border-t border-[#EFEAE2] px-3 py-2">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[#B0AAA2]">
                    Projects
                </div>
                <div className="mt-2 space-y-1">
                    <button
                        type="button"
                        onClick={() => handleAssignProject(conv.id, null)}
                        className={clsx(
                            "flex w-full items-center justify-between rounded-md px-2 py-1.5 text-[12px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors",
                            !selectedProjectId && "text-[#DA7756]"
                        )}
                    >
                        <span>None</span>
                        {!selectedProjectId && <Check size={14} strokeWidth={2} />}
                    </button>
                    {hasProjects ? safeProjects.map((project) => {
                        const isSelected = project.id === selectedProjectId;
                        return (
                            <button
                                key={project.id}
                                type="button"
                                onClick={() => handleAssignProject(conv.id, project.id)}
                                className={clsx(
                                    "flex w-full items-center justify-between rounded-md px-2 py-1.5 text-[12px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors",
                                    isSelected && "text-[#DA7756]"
                                )}
                            >
                                <span className="truncate">{project.name}</span>
                                {isSelected && <Check size={14} strokeWidth={2} />}
                            </button>
                        );
                    }) : (
                        <div className="px-2 py-1 text-[12px] text-[#A7A19A]">
                            No projects yet.
                        </div>
                    )}
                </div>
                <div className="mt-3">
                    <label className="block text-[11px] uppercase tracking-[0.2em] text-[#B0AAA2]">
                        New project
                    </label>
                    <div className="mt-2 flex items-center gap-2">
                        <input
                            value={projectDraftId === conv.id ? projectDraft : ''}
                            onChange={(event) => {
                                setProjectDraftId(conv.id);
                                setProjectDraft(event.target.value);
                            }}
                            onKeyDown={(event) => {
                                if (event.key === 'Enter') {
                                    event.preventDefault();
                                    if (!projectDraft.trim()) return;
                                    handleCreateProject(projectDraft, conv.id);
                                    setProjectDraft('');
                                }
                            }}
                            placeholder="Project name"
                            className="w-full rounded-md border border-[#E6E1D7] bg-white px-2 py-1 text-[12px] text-[#3E3A34] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                        />
                        <button
                            type="button"
                            onClick={() => {
                                if (!projectDraft.trim()) return;
                                handleCreateProject(projectDraft, conv.id);
                                setProjectDraft('');
                            }}
                            className="rounded-md bg-[#DA7756] px-2 py-1 text-[11px] text-white hover:bg-[#C4654A] transition-colors"
                        >
                            Add
                        </button>
                    </div>
                </div>
            </div>
        );
    };

    const renderFolderPicker = (conv) => {
        if (folderMenuOpenId !== conv.id) return null;
        const selectedFolderId = conv.folderId || null;
        const hasFolders = safeFolders.length > 0;

        return (
            <div className="border-t border-[#EFEAE2] px-3 py-2">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[#B0AAA2]">
                    Folders
                </div>
                <div className="mt-2 space-y-1">
                    <button
                        type="button"
                        onClick={() => {
                            onAssignFolder?.(conv.id, null);
                            setFolderMenuOpenId(null);
                        }}
                        className={clsx(
                            "flex w-full items-center justify-between rounded-md px-2 py-1.5 text-[12px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors",
                            !selectedFolderId && "text-[#DA7756]"
                        )}
                    >
                        <span>None</span>
                        {!selectedFolderId && <Check size={14} strokeWidth={2} />}
                    </button>
                    {hasFolders ? safeFolders.map((folder) => {
                        const isSelected = folder.id === selectedFolderId;
                        return (
                            <button
                                key={folder.id}
                                type="button"
                                onClick={() => {
                                    onAssignFolder?.(conv.id, folder.id);
                                    setFolderMenuOpenId(null);
                                }}
                                className={clsx(
                                    "flex w-full items-center justify-between rounded-md px-2 py-1.5 text-[12px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors",
                                    isSelected && "text-[#DA7756]"
                                )}
                            >
                                <span className="truncate">{folder.name}</span>
                                {isSelected && <Check size={14} strokeWidth={2} />}
                            </button>
                        );
                    }) : (
                        <div className="px-2 py-1 text-[12px] text-[#A7A19A]">
                            No folders yet.
                        </div>
                    )}
                </div>
            </div>
        );
    };

    const renderTagEditor = (conv) => {
        if (tagEditorId !== conv.id) return null;
        return (
            <div className="border-t border-[#EFEAE2] px-3 py-2">
                <div className="text-[11px] uppercase tracking-[0.2em] text-[#B0AAA2]">
                    Tags
                </div>
                <div className="mt-2 flex items-center gap-2">
                    <input
                        value={tagDraft}
                        onChange={(event) => setTagDraft(event.target.value)}
                        placeholder="comma separated"
                        className="w-full rounded-md border border-[#E6E1D7] bg-white px-2 py-1 text-[12px] text-[#3E3A34] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                    />
                    <button
                        type="button"
                        onClick={() => handleUpdateTagsLocal(conv.id)}
                        className="rounded-md bg-[#DA7756] px-2 py-1 text-[11px] text-white hover:bg-[#C4654A]"
                    >
                        Save
                    </button>
                </div>
            </div>
        );
    };

    const renderConversationRow = (conv) => {
        const isActive = conv.id === activeId;
        const isMenuOpen = menuOpenId === conv.id;
        const ArchiveIcon = conv.archived ? Inbox : Archive;
        const archiveLabel = conv.archived ? 'Unarchive' : 'Archive';
        const projectName = conv.projectId ? (projectLookup.get(conv.projectId)?.name || 'Project') : null;
        const folderName = conv.folderId ? (safeFolders.find((folder) => folder.id === conv.folderId)?.name || 'Folder') : null;
        const tagList = Array.isArray(conv.tags) ? conv.tags : [];
        const isRenaming = renameId === conv.id;
        const isSelected = selectedIds.includes(conv.id);
        const hasAssistant = (conv.messages || []).some((msg) => msg.role === 'assistant' && msg.content?.trim());
        const hasCode = (conv.messages || []).some((msg) => msg.role === 'assistant' && /```/.test(msg.content || ''));

        return (
            <div
                key={conv.id}
                data-menu-root
                role="button"
                tabIndex={0}
                onClick={() => {
                    if (bulkMode) {
                        toggleSelected(conv.id);
                        return;
                    }
                    setMenuOpenId(null);
                    onSelectConversation(conv.id);
                }}
                onKeyDown={(event) => handleRowKeyDown(event, conv.id)}
                className={clsx(
                    "group w-full rounded-lg px-3 py-2 text-left transition-colors flex items-center gap-2 cursor-pointer",
                    isActive
                        ? "bg-[#EFEAE2] text-[#2E2B26]"
                        : "text-[#4C4842] hover:bg-[#F2EEE6]"
                )}
            >
                {bulkMode && (
                    <button
                        type="button"
                        onClick={(event) => {
                            event.stopPropagation();
                            toggleSelected(conv.id);
                        }}
                        className="text-[#A7A19A] hover:text-[#3E3A34]"
                        aria-label="Select conversation"
                    >
                        {isSelected ? <CheckSquare size={16} /> : <Square size={16} />}
                    </button>
                )}
                <div className="flex min-w-0 flex-1 flex-col">
                    {isRenaming ? (
                        <div className="flex items-center gap-2">
                            <input
                                value={renameDraft}
                                onChange={(event) => setRenameDraft(event.target.value)}
                                onKeyDown={(event) => {
                                    if (event.key === 'Enter') {
                                        event.preventDefault();
                                        handleRenameConversationLocal(conv.id, renameDraft);
                                    }
                                }}
                                className="w-full rounded-md border border-[#E6E1D7] bg-white px-2 py-1 text-[12px] text-[#3E3A34] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                            />
                            <button
                                type="button"
                                onClick={() => handleRenameConversationLocal(conv.id, renameDraft)}
                                className="rounded-md bg-[#DA7756] px-2 py-1 text-[11px] text-white hover:bg-[#C4654A]"
                            >
                                Save
                            </button>
                        </div>
                    ) : (
                        <span className="truncate text-[14px] leading-tight">
                            {conv.title || 'New chat'}
                        </span>
                    )}
                    {projectName && (
                        <span className="mt-1 inline-flex w-fit items-center rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#6F6A63]">
                            {projectName}
                        </span>
                    )}
                    {folderName && (
                        <span className="mt-1 inline-flex w-fit items-center rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[10px] uppercase tracking-[0.15em] text-[#6F6A63]">
                            {folderName}
                        </span>
                    )}
                    {tagList.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-1 text-[10px] text-[#6F6A63]">
                            {tagList.slice(0, 3).map((tag) => (
                                <span key={tag} className="rounded-full bg-[#F1EDE6] px-2 py-0.5">
                                    {tag}
                                </span>
                            ))}
                            {tagList.length > 3 && (
                                <span className="rounded-full bg-[#F1EDE6] px-2 py-0.5">+{tagList.length - 3}</span>
                            )}
                        </div>
                    )}
                </div>
                {conv.pinned && <Pin size={14} className="text-[#DA7756]" />}
                <div className="ml-auto relative flex items-center">
                    <button
                        type="button"
                        aria-label="Conversation actions"
                        onClick={(event) => {
                            event.stopPropagation();
                            setMenuOpenId((prev) => (prev === conv.id ? null : conv.id));
                            setProjectMenuOpenId(null);
                            setProjectDraft('');
                            setProjectDraftId(null);
                        }}
                        className={clsx(
                            "p-1.5 rounded-md text-[#9A958D] hover:text-[#3C3832] hover:bg-[#ECE6DD] transition-colors",
                            isMenuOpen ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                        )}
                    >
                        <MoreHorizontal size={16} strokeWidth={1.8} />
                    </button>
                    {isMenuOpen && (
                        <div
                            className="absolute right-0 top-8 z-20 w-44 rounded-lg border border-[#E6E1D7] bg-white shadow-sm"
                            onClick={(event) => event.stopPropagation()}
                        >
                            <button
                                type="button"
                                onClick={async () => {
                                    await handleShare({ conversation: conv }, 'conversation');
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <ExternalLink size={14} strokeWidth={1.8} />
                                Share link
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    downloadFile(`${conv.title || 'chat'}.json`, JSON.stringify(conv, null, 2));
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <FileText size={14} strokeWidth={1.8} />
                                Export JSON
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    downloadFile(`${conv.title || 'chat'}.md`, toMarkdown(conv), 'text/markdown');
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <FileText size={14} strokeWidth={1.8} />
                                Export MD
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setRenameId(conv.id);
                                    setRenameDraft(conv.title || '');
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <Edit3 size={14} strokeWidth={1.8} />
                                Rename
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    onTogglePinConversation?.(conv.id);
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <Pin size={14} strokeWidth={1.8} />
                                {conv.pinned ? 'Unpin' : 'Pin'}
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setTagEditorId((prev) => (prev === conv.id ? null : conv.id));
                                    setTagDraft((conv.tags || []).join(', '));
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <Tag size={14} strokeWidth={1.8} />
                                Tags
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setProjectMenuOpenId((prev) => (prev === conv.id ? null : conv.id));
                                    setProjectDraft('');
                                    setProjectDraftId(conv.id);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <FolderPlus size={14} strokeWidth={1.8} />
                                Add to project
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setFolderMenuOpenId((prev) => (prev === conv.id ? null : conv.id));
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <FolderOpen size={14} strokeWidth={1.8} />
                                Move to folder
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    onArchiveConversation(conv.id, !conv.archived);
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#4C4842] hover:bg-[#F6F2EA] transition-colors"
                            >
                                <ArchiveIcon size={14} strokeWidth={1.8} />
                                {archiveLabel}
                            </button>
                            <button
                                type="button"
                                disabled={!hasAssistant}
                                onClick={() => {
                                    if (!hasAssistant) return;
                                    if (onSaveArtifact) {
                                        onSaveArtifact(conv.id);
                                    }
                                    setMenuOpenId(null);
                                }}
                                className={clsx(
                                    "flex w-full items-center gap-2 px-3 py-2 text-[13px] transition-colors",
                                    hasAssistant
                                        ? "text-[#4C4842] hover:bg-[#F6F2EA]"
                                        : "text-[#B9B3AA] cursor-not-allowed"
                                )}
                            >
                                <FileText size={14} strokeWidth={1.8} />
                                Save to artifacts
                            </button>
                            <button
                                type="button"
                                disabled={!hasCode}
                                onClick={() => {
                                    if (!hasCode) return;
                                    if (onSaveCode) {
                                        onSaveCode(conv.id);
                                    }
                                    setMenuOpenId(null);
                                }}
                                className={clsx(
                                    "flex w-full items-center gap-2 px-3 py-2 text-[13px] transition-colors",
                                    hasCode
                                        ? "text-[#4C4842] hover:bg-[#F6F2EA]"
                                        : "text-[#B9B3AA] cursor-not-allowed"
                                )}
                            >
                                <Code size={14} strokeWidth={1.8} />
                                Save to code
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    onDeleteConversation(conv.id);
                                    setMenuOpenId(null);
                                }}
                                className="flex w-full items-center gap-2 px-3 py-2 text-[13px] text-[#B54B3D] hover:bg-[#FBEDEA] transition-colors"
                            >
                                <Trash2 size={14} strokeWidth={1.8} />
                                Delete
                            </button>
                            {renderTagEditor(conv)}
                            {renderFolderPicker(conv)}
                            {renderProjectPicker(conv)}
                        </div>
                    )}
                </div>
            </div>
        );
    };

    return (
        <aside
            className="relative bg-[#F9F7F2] text-[#5E5A52] border-r border-[#E6E1D7] flex flex-col h-full"
            style={{ width }}
        >
            <div className="px-4 pt-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-full bg-[#FF5F57]" />
                        <span className="h-3 w-3 rounded-full bg-[#FFBD2E]" />
                        <span className="h-3 w-3 rounded-full bg-[#28C840]" />
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={onToggleCollapse}
                            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                            className="p-1.5 text-[#9C978F] hover:text-[#3C3832] transition-colors"
                        >
                            {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                        </button>
                        <button
                            onClick={onOpenSettings}
                            aria-label="Open settings"
                            className="p-1.5 text-[#9C978F] hover:text-[#3C3832] transition-colors"
                        >
                            <Settings size={16} />
                        </button>
                        <button
                            onClick={onOpenAdmin}
                            aria-label="Open admin console"
                            className="p-1.5 text-[#9C978F] hover:text-[#3C3832] transition-colors"
                        >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                <rect x="3.5" y="4" width="17" height="16" rx="2" />
                                <path d="M9 4v16" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <div className="px-4 pt-6">
                <button
                    onClick={onNewChat}
                    className="flex items-center gap-3 rounded-lg px-2 py-1.5 text-[16px] text-[#3E3A34] hover:bg-[#F0EBE3] transition-colors"
                >
                    <span className="h-9 w-9 rounded-full bg-[#DA7756] text-white flex items-center justify-center">
                        <Plus size={18} strokeWidth={2} />
                    </span>
                    {!isCollapsed && <span>New chat</span>}
                </button>
            </div>

            <div className="px-4 pt-6 space-y-2 text-[15px]">
                {navItems.map((item) => {
                    const isActive = activeSection === item.key;
                    return (
                        <button
                            key={item.key}
                            onClick={() => setActiveSection(item.key)}
                            className={clsx(
                                "flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left transition-colors",
                                isActive
                                    ? "bg-[#EFEAE2] text-[#3E3A34]"
                                    : "text-[#6F6A63] hover:bg-[#F2EEE6]"
                            )}
                        >
                            <item.icon size={18} strokeWidth={1.6} />
                            {!isCollapsed && <span>{item.label}</span>}
                            {!isCollapsed && item.badge > 0 && (
                                <span className="ml-auto rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[11px] text-[#6F6A63]">
                                    {item.badge}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>

            {!isCollapsed && (
                <div className="flex-1 overflow-y-auto px-4 pt-6 pb-8">
                    {showConversations ? (
                    <>
                        <div className="flex items-center justify-between">
                            <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                {sectionTitle}
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={() => setBulkMode((prev) => !prev)}
                                    className={clsx(
                                        "rounded-md px-2 py-1 text-[11px] uppercase tracking-[0.2em]",
                                        bulkMode ? "bg-[#EFEAE2] text-[#3E3A34]" : "text-[#A7A19A] hover:bg-[#F2EEE6] hover:text-[#3E3A34]"
                                    )}
                                >
                                    {bulkMode ? 'Done' : 'Select'}
                                </button>
                                <button
                                    onClick={() => setRecentsOpen((open) => !open)}
                                    className="rounded-md p-1 text-[#A7A19A] hover:bg-[#F2EEE6] hover:text-[#3E3A34] transition-colors"
                                    aria-label={recentsOpen ? 'Collapse recents' : 'Expand recents'}
                                >
                                    {recentsOpen ? (
                                        <ChevronDown size={16} strokeWidth={1.6} />
                                    ) : (
                                        <ChevronRight size={16} strokeWidth={1.6} />
                                    )}
                                </button>
                            </div>
                        </div>
                        {recentsOpen && (
                            <>
                                {bulkMode && (
                                    <div className="mt-3 flex flex-wrap items-center gap-2 rounded-lg border border-[#E8E5DE] bg-white px-3 py-2 text-[12px] text-[#6F6A63]">
                                        <span>{selectedIds.length} selected</span>
                                        <button
                                            type="button"
                                            onClick={() => runBulkAction(activeSection === 'archive' ? 'unarchive' : 'archive')}
                                            className="rounded-full border border-[#E8E5DE] px-3 py-1 hover:bg-[#F7F5F0]"
                                        >
                                            {activeSection === 'archive' ? 'Unarchive' : 'Archive'}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => runBulkAction('pin')}
                                            className="rounded-full border border-[#E8E5DE] px-3 py-1 hover:bg-[#F7F5F0]"
                                        >
                                            Pin
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => runBulkAction('unpin')}
                                            className="rounded-full border border-[#E8E5DE] px-3 py-1 hover:bg-[#F7F5F0]"
                                        >
                                            Unpin
                                        </button>
                                        {safeFolders.length > 0 && (
                                            <button
                                                type="button"
                                                onClick={() => runBulkAction('move-folder', safeFolders[0]?.id)}
                                                className="rounded-full border border-[#E8E5DE] px-3 py-1 hover:bg-[#F7F5F0]"
                                            >
                                                Move to {safeFolders[0]?.name}
                                            </button>
                                        )}
                                        <button
                                            type="button"
                                            onClick={() => runBulkAction('delete')}
                                            className="rounded-full border border-[#F1D6D1] px-3 py-1 text-[#B54B3D] hover:bg-[#FCEDEA]"
                                        >
                                            Delete
                                        </button>
                                        <button
                                            type="button"
                                            onClick={clearSelection}
                                            className="ml-auto rounded-full border border-[#E8E5DE] px-3 py-1 hover:bg-[#F7F5F0]"
                                        >
                                            Clear
                                        </button>
                                    </div>
                                )}
                                <div className="mt-3 flex items-center gap-2 rounded-lg border border-[#E8E5DE] bg-white px-2 py-1.5 text-[13px] text-[#6F6A63]">
                                    <Search size={14} />
                                    <input
                                        value={searchQuery}
                                        onChange={(event) => setSearchQuery(event.target.value)}
                                        placeholder="Search chats"
                                        className="w-full bg-transparent focus:outline-none"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => onToggleSemanticSearch?.(!semanticEnabled)}
                                        className={clsx(
                                            "rounded-full p-1 transition-colors",
                                            semanticEnabled
                                                ? "text-[#DA7756]"
                                                : "text-[#A7A19A] hover:bg-[#F2EEE6] hover:text-[#3E3A34]"
                                        )}
                                        aria-label={semanticEnabled ? 'Disable semantic search' : 'Enable semantic search'}
                                    >
                                        <Sparkles size={12} />
                                    </button>
                                    {searchQuery && (
                                        <button
                                            type="button"
                                            onClick={() => setSearchQuery('')}
                                            className="rounded-full p-1 text-[#A7A19A] hover:bg-[#F2EEE6] hover:text-[#3E3A34]"
                                            aria-label="Clear search"
                                        >
                                            <X size={12} />
                                        </button>
                                    )}
                                </div>
                                <div className="mt-3">
                                    <div className="flex items-center justify-between">
                                        <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">Folders</div>
                                    </div>
                                    <div className="mt-2 flex items-center gap-2">
                                        <input
                                            value={folderDraft}
                                            onChange={(event) => setFolderDraft(event.target.value)}
                                            onKeyDown={(event) => {
                                                if (event.key === 'Enter') {
                                                    event.preventDefault();
                                                    handleCreateFolder();
                                                }
                                            }}
                                            placeholder="New folder"
                                            className="w-full rounded-md border border-[#E6E1D7] bg-white px-2 py-1 text-[12px] text-[#3E3A34] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                                        />
                                        <button
                                            type="button"
                                            onClick={handleCreateFolder}
                                            className="rounded-md bg-[#DA7756] px-2 py-1 text-[11px] text-white hover:bg-[#C4654A]"
                                        >
                                            Add
                                        </button>
                                    </div>
                                    <div className="mt-2 flex flex-wrap gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setActiveFolderId(null)}
                                            className={clsx(
                                                "rounded-full border px-3 py-1 text-[11px]",
                                                !activeFolderId
                                                    ? "border-[#DA7756] text-[#DA7756]"
                                                    : "border-[#E8E5DE] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                            )}
                                        >
                                            All
                                        </button>
                                        {safeFolders.map((folder) => (
                                            <button
                                                key={folder.id}
                                                type="button"
                                                onClick={() => setActiveFolderId(folder.id)}
                                                className={clsx(
                                                    "rounded-full border px-3 py-1 text-[11px]",
                                                    activeFolderId === folder.id
                                                        ? "border-[#DA7756] text-[#DA7756]"
                                                        : "border-[#E8E5DE] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                                )}
                                            >
                                                {folder.name}
                                            </button>
                                        ))}
                                    </div>
                                    {safeFolders.length === 0 && (
                                        <div className="mt-2 text-[12px] text-[#A7A19A]">No folders yet.</div>
                                    )}
                                </div>
                                {allTags.length > 0 && (
                                    <div className="mt-3">
                                        <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">Tags</div>
                                        <div className="mt-2 flex flex-wrap gap-2">
                                            <button
                                                type="button"
                                                onClick={() => setActiveTag('')}
                                                className={clsx(
                                                    "rounded-full border px-3 py-1 text-[11px]",
                                                    !activeTag
                                                        ? "border-[#DA7756] text-[#DA7756]"
                                                        : "border-[#E8E5DE] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                                )}
                                            >
                                                All
                                            </button>
                                            {allTags.map((tag) => (
                                                <button
                                                    key={tag}
                                                    type="button"
                                                    onClick={() => setActiveTag(tag)}
                                                    className={clsx(
                                                        "rounded-full border px-3 py-1 text-[11px]",
                                                        activeTag === tag
                                                            ? "border-[#DA7756] text-[#DA7756]"
                                                            : "border-[#E8E5DE] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                                    )}
                                                >
                                                    {tag}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                <div className="mt-3 space-y-1">
                                    {filteredConversations.length === 0 && (
                                        <div className="py-2 text-[13px] text-[#A7A19A]">
                                            {emptyMessage}
                                        </div>
                                    )}
                                    {limitedConversations.map(renderConversationRow)}
                                    {hasMoreRecents && (
                                        <button
                                            type="button"
                                            onClick={() => setRecentsLimit((limit) => Math.min(limit + 40, filteredConversations.length))}
                                            className="mt-2 w-full rounded-lg border border-[#E8E5DE] px-3 py-2 text-[12px] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                        >
                                            Show more
                                        </button>
                                    )}
                                </div>
                            </>
                        )}
                    </>
                ) : null}

                {activeSection === 'projects' && (
                    <>
                        {projectViewId ? (
                            <>
                                <div className="flex items-center justify-between">
                                    <button
                                        type="button"
                                        onClick={() => setProjectViewId(null)}
                                        className="flex items-center gap-2 text-[12px] uppercase tracking-[0.2em] text-[#A7A19A] hover:text-[#3E3A34]"
                                    >
                                        <ChevronLeft size={16} strokeWidth={1.6} />
                                        Projects
                                    </button>
                                    <div className="text-[12px] text-[#A7A19A]">
                                        {projectLookup.get(projectViewId)?.name || 'Project'}
                                    </div>
                                </div>
                                <div className="mt-3">
                                    <label className="block text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Project instructions
                                    </label>
                                    <textarea
                                        value={projectLookup.get(projectViewId)?.instructions || ''}
                                        onChange={(event) => onUpdateProject?.(projectViewId, { instructions: event.target.value })}
                                        rows={3}
                                        placeholder="Add per-project instructions for the assistant"
                                        className="mt-2 w-full rounded-lg border border-[#E8E5DE] bg-white px-2 py-1 text-[12px] text-[#3E3A34] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                                    />
                                </div>
                                <div className="mt-3 rounded-lg border border-[#E8E5DE] bg-white p-3 text-[12px] text-[#6F6A63]">
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">Project policies</div>
                                    <div className="mt-2 space-y-3">
                                        <label className="block text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                            Memory scope
                                        </label>
                                        <select
                                            value={projectLookup.get(projectViewId)?.memoryScope || 'enabled'}
                                            onChange={(event) => onUpdateProject?.(projectViewId, { memoryScope: event.target.value })}
                                            className="w-full rounded-lg border border-[#E8E5DE] px-2 py-1 text-[12px] text-[#3E3A34]"
                                        >
                                            <option value="enabled">Enabled</option>
                                            <option value="disabled">Disabled</option>
                                        </select>
                                        <label className="block text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                            PII handling
                                        </label>
                                        <select
                                            value={projectLookup.get(projectViewId)?.piiPolicy || 'redact'}
                                            onChange={(event) => onUpdateProject?.(projectViewId, { piiPolicy: event.target.value })}
                                            className="w-full rounded-lg border border-[#E8E5DE] px-2 py-1 text-[12px] text-[#3E3A34]"
                                        >
                                            <option value="redact">Redact in storage</option>
                                            <option value="retain">Retain raw</option>
                                        </select>
                                        <label className="block text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                            Retention days
                                        </label>
                                        <input
                                            type="number"
                                            min="0"
                                            value={projectLookup.get(projectViewId)?.retentionDays || 0}
                                            onChange={(event) => onUpdateProject?.(projectViewId, { retentionDays: Number(event.target.value || 0) })}
                                            className="w-full rounded-lg border border-[#E8E5DE] px-2 py-1 text-[12px] text-[#3E3A34]"
                                        />
                                        <label className="block text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                            Prompt variant
                                        </label>
                                        <select
                                            value={projectLookup.get(projectViewId)?.promptVariant || 'default'}
                                            onChange={(event) => onUpdateProject?.(projectViewId, { promptVariant: event.target.value })}
                                            className="w-full rounded-lg border border-[#E8E5DE] px-2 py-1 text-[12px] text-[#3E3A34]"
                                        >
                                            {promptVariantOptions.map((variant) => (
                                                <option key={variant.key} value={variant.key}>
                                                    {variant.label || variant.key}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                                <div className="mt-3 rounded-lg border border-[#E8E5DE] bg-white p-3 text-[12px] text-[#6F6A63]">
                                    <div className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">Memory summary</div>
                                    <div className="mt-2 whitespace-pre-wrap">
                                        {projectMemory[projectViewId]?.summary || 'No memory summary yet.'}
                                    </div>
                                    <div className="mt-2 flex items-center justify-between text-[11px] text-[#A7A19A]">
                                        <span>Messages summarized: {projectMemory[projectViewId]?.message_count || 0}</span>
                                        <span>
                                            {projectMemory[projectViewId]?.updated_at
                                                ? new Date(projectMemory[projectViewId].updated_at * 1000).toLocaleString()
                                                : ''}
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleClearProjectMemory(projectViewId)}
                                        className="mt-3 inline-flex items-center gap-2 rounded-full border border-[#E8E5DE] px-3 py-1 text-[11px] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                    >
                                        Clear memory
                                    </button>
                                </div>
                                <div className="mt-3">
                                    <div className="flex items-center justify-between">
                                        <label className="text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                            Project files
                                        </label>
                                        <label className="rounded-full border border-[#E8E5DE] px-3 py-1 text-[11px] text-[#6F6A63] hover:bg-[#F7F5F0] cursor-pointer">
                                            Add files
                                            <input
                                                type="file"
                                                multiple
                                                accept=".txt,.md,.csv,.json,text/plain,text/markdown,text/csv,application/json"
                                                className="hidden"
                                                onChange={(event) => handleProjectFiles(event, projectViewId)}
                                            />
                                        </label>
                                    </div>
                                    <div className="mt-2 space-y-2">
                                        {(projectLookup.get(projectViewId)?.files || []).length === 0 && (
                                            <div className="text-[12px] text-[#A7A19A]">No project files yet.</div>
                                        )}
                                        {(projectLookup.get(projectViewId)?.files || []).map((file) => (
                                            <div key={file.id} className="flex items-center justify-between rounded-lg border border-[#EFEAE2] bg-white px-3 py-2 text-[12px] text-[#4C4842]">
                                                <span className="truncate">{file.name}</span>
                                                <button
                                                    type="button"
                                                    onClick={() => onRemoveProjectFile?.(projectViewId, file.id)}
                                                    className="rounded-full p-1 text-[#A7A19A] hover:bg-[#F2EEE6] hover:text-[#3E3A34]"
                                                >
                                                    <X size={12} />
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                                <div className="mt-3 flex flex-wrap gap-2">
                                    <button
                                        type="button"
                                        onClick={async () => {
                                            const project = projectLookup.get(projectViewId);
                                            const projectConversations = conversations.filter((conv) => conv.projectId === projectViewId);
                                            await handleShare({ project, conversations: projectConversations }, 'project');
                                        }}
                                        className="inline-flex items-center gap-2 rounded-full border border-[#E8E5DE] px-3 py-1.5 text-[12px] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                    >
                                        <ExternalLink size={12} />
                                        Share project
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const project = projectLookup.get(projectViewId);
                                            const projectConversations = conversations.filter((conv) => conv.projectId === projectViewId);
                                            downloadFile(
                                                `${project?.name || 'project'}.json`,
                                                JSON.stringify({ project, conversations: projectConversations }, null, 2)
                                            );
                                        }}
                                        className="inline-flex items-center gap-2 rounded-full border border-[#E8E5DE] px-3 py-1.5 text-[12px] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                    >
                                        <FileText size={12} />
                                        Export JSON
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const project = projectLookup.get(projectViewId);
                                            const projectConversations = conversations.filter((conv) => conv.projectId === projectViewId);
                                            const markdown = [
                                                `# ${project?.name || 'Project'}`,
                                                '',
                                                project?.instructions ? `> ${project.instructions}` : '',
                                                '',
                                                ...projectConversations.flatMap((conv) => [
                                                    `## ${conv.title || 'New chat'}`,
                                                    '',
                                                    ...(toMarkdown(conv).split('\n')),
                                                ]),
                                            ].join('\n');
                                            downloadFile(`${project?.name || 'project'}.md`, markdown, 'text/markdown');
                                        }}
                                        className="inline-flex items-center gap-2 rounded-full border border-[#E8E5DE] px-3 py-1.5 text-[12px] text-[#6F6A63] hover:bg-[#F7F5F0]"
                                    >
                                        <FileText size={12} />
                                        Export MD
                                    </button>
                                </div>
                                <div className="mt-3 space-y-1">
                                    {activeConversations.filter((conv) => conv.projectId === projectViewId).length === 0 && (
                                        <div className="py-2 text-[13px] text-[#A7A19A]">
                                            No chats in this project yet.
                                        </div>
                                    )}
                                    {activeConversations
                                        .filter((conv) => conv.projectId === projectViewId)
                                        .map(renderConversationRow)}
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="flex items-center justify-between">
                                    <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        Projects
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setProjectComposerOpen((open) => !open)}
                                        className="rounded-md p-1 text-[#A7A19A] hover:bg-[#F2EEE6] hover:text-[#3E3A34] transition-colors"
                                        aria-label="Create project"
                                    >
                                        <Plus size={14} strokeWidth={1.8} />
                                    </button>
                                </div>
                                {projectComposerOpen && (
                                    <div className="mt-3 flex items-center gap-2">
                                        <input
                                            value={projectComposerDraft}
                                            onChange={(event) => setProjectComposerDraft(event.target.value)}
                                            onKeyDown={(event) => {
                                                if (event.key === 'Enter') {
                                                    event.preventDefault();
                                                    if (!projectComposerDraft.trim()) return;
                                                    const projectId = handleCreateProject(projectComposerDraft);
                                                    if (projectId) {
                                                        setProjectViewId(projectId);
                                                    }
                                                    setProjectComposerDraft('');
                                                    setProjectComposerOpen(false);
                                                }
                                            }}
                                            placeholder="New project"
                                            className="w-full rounded-md border border-[#E6E1D7] bg-white px-2 py-1 text-[12px] text-[#3E3A34] focus:outline-none focus:ring-2 focus:ring-[#DA7756]"
                                        />
                                        <button
                                            type="button"
                                            onClick={() => {
                                                if (!projectComposerDraft.trim()) return;
                                                const projectId = handleCreateProject(projectComposerDraft);
                                                if (projectId) {
                                                    setProjectViewId(projectId);
                                                }
                                                setProjectComposerDraft('');
                                                setProjectComposerOpen(false);
                                            }}
                                            className="rounded-md bg-[#DA7756] px-2 py-1 text-[11px] text-white hover:bg-[#C4654A] transition-colors"
                                        >
                                            Create
                                        </button>
                                    </div>
                                )}
                                <div className="mt-3 space-y-1">
                                    {safeProjects.length === 0 && (
                                        <div className="py-2 text-[13px] text-[#A7A19A]">
                                            No projects yet.
                                        </div>
                                    )}
                                    {safeProjects.map((project) => {
                                        const count = projectCounts.get(project.id) || 0;
                                        return (
                                            <button
                                                key={project.id}
                                                type="button"
                                                onClick={() => setProjectViewId(project.id)}
                                                className="flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-[14px] text-[#4C4842] hover:bg-[#F2EEE6] transition-colors"
                                            >
                                                <span className="truncate">{project.name}</span>
                                                <span className="rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[11px] text-[#6F6A63]">
                                                    {count}
                                                </span>
                                            </button>
                                        );
                                    })}
                                </div>
                            </>
                        )}
                    </>
                )}

                {activeSection === 'artifacts' && (
                    <>
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">
                            Artifacts
                        </div>
                        <div className="mt-3 space-y-1">
                            {sortedArtifacts.length === 0 && (
                                <div className="py-2 text-[13px] text-[#A7A19A]">
                                    No artifacts yet.
                                </div>
                            )}
                            {sortedArtifacts.map((artifact) => (
                                <button
                                    key={artifact.id}
                                    type="button"
                                    onClick={() => onSelectConversation(artifact.conversationId)}
                                    className="flex w-full flex-col gap-1 rounded-lg px-3 py-2 text-left text-[#4C4842] hover:bg-[#F2EEE6] transition-colors"
                                >
                                    <span className="truncate text-[14px]">{artifact.title || 'Artifact'}</span>
                                    <span className="truncate text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        {artifact.conversationTitle || 'Conversation'}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </>
                )}

                {activeSection === 'code' && (
                    <>
                        <div className="text-[12px] uppercase tracking-[0.2em] text-[#A7A19A]">
                            Code
                        </div>
                        <div className="mt-3 space-y-1">
                            {sortedCode.length === 0 && (
                                <div className="py-2 text-[13px] text-[#A7A19A]">
                                    No code snippets yet.
                                </div>
                            )}
                            {sortedCode.map((snippet) => (
                                <button
                                    key={snippet.id}
                                    type="button"
                                    onClick={() => onSelectConversation(snippet.conversationId)}
                                    className="flex w-full flex-col gap-1 rounded-lg px-3 py-2 text-left text-[#4C4842] hover:bg-[#F2EEE6] transition-colors"
                                >
                                    <div className="flex items-center justify-between gap-2">
                                        <span className="truncate text-[14px]">{snippet.title || 'Snippet'}</span>
                                        <span className="rounded-full bg-[#ECE6DD] px-2 py-0.5 text-[10px] uppercase tracking-[0.2em] text-[#6F6A63]">
                                            {snippet.language || 'text'}
                                        </span>
                                    </div>
                                    <span className="truncate text-[11px] uppercase tracking-[0.2em] text-[#A7A19A]">
                                        {snippet.conversationTitle || 'Conversation'}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </>
                )}
                </div>
            )}
            <div
                onMouseDown={onResizeStart}
                className="absolute right-0 top-0 h-full w-1.5 cursor-col-resize bg-transparent hover:bg-[#E7E2D8]"
                aria-hidden="true"
            />
        </aside>
    );
};

export default Sidebar;
