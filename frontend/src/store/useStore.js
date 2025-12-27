import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const DEFAULT_SETTINGS = {
    highContrast: false,
    reduceMotion: false,
    fontScale: 'md',
    density: 'comfortable',
    showThinking: true,
    showLatency: true,
    sidebarCollapsed: false,
    projectMemoryEnabled: true,
    redactPii: false,
    retentionDays: 0,
    responseMode: 'auto',
    promptVariant: 'default',
    semanticSearch: false,
};

const DEFAULT_PREFERENCES = {
    profile: '',
    tone: 'neutral',
    instructions: '',
};

const createId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

const truncateTitle = (text, limit = 46) => {
    const trimmed = (text || '').trim().replace(/\s+/g, ' ');
    if (!trimmed) return '';
    if (trimmed.length <= limit) return trimmed;
    return `${trimmed.slice(0, limit)}...`;
};

const redactPiiText = (text) => {
    if (!text) return text;
    let output = text;
    output = output.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[redacted-email]');
    output = output.replace(/\b(\+?60|0)1[0-9][ -]?\d{3,4}[ -]?\d{4}\b/g, '[redacted-phone]');
    output = output.replace(/\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b/g, '[redacted-card]');
    output = output.replace(/\b\d{6}-\d{2}-\d{4}\b/g, '[redacted-id]');
    return output;
};

const deriveTitle = (messages) => {
    const firstUser = (messages || []).find((msg) => msg.role === 'user' && msg.content?.trim());
    if (!firstUser) return '';
    return truncateTitle(firstUser.content);
};

const normalizeConversation = (conv) => {
    const now = new Date().toISOString();
    return {
        ...conv,
        id: conv.id || createId('conv'),
        title: conv.title || 'New chat',
        messages: Array.isArray(conv.messages) ? conv.messages : [],
        createdAt: conv.createdAt || now,
        updatedAt: conv.updatedAt || conv.createdAt || now,
        archived: Boolean(conv.archived),
        pinned: Boolean(conv.pinned),
        tags: Array.isArray(conv.tags) ? conv.tags : [],
        projectId: conv.projectId || null,
        folderId: conv.folderId || null,
    };
};

const normalizeProject = (project) => {
    const now = new Date().toISOString();
    return {
        id: project.id || createId('proj'),
        name: project.name || 'Project',
        instructions: project.instructions || '',
        files: Array.isArray(project.files) ? project.files : [],
        memoryScope: project.memoryScope || 'enabled',
        piiPolicy: project.piiPolicy || 'redact',
        retentionDays: Number.isFinite(project.retentionDays) ? project.retentionDays : 0,
        promptVariant: project.promptVariant || 'default',
        createdAt: project.createdAt || now,
        updatedAt: project.updatedAt || now,
    };
};

const normalizeFolder = (folder) => ({
    id: folder.id || createId('folder'),
    name: folder.name || 'Folder',
});

const useStore = create(
    persist(
        (set, get) => ({
            conversations: [],
            activeConversationId: null,
            projects: [],
            folders: [],
            artifacts: [],
            codeSnippets: [],
            settings: DEFAULT_SETTINGS,
            preferences: DEFAULT_PREFERENCES,
            sessionId: '',
            isSidebarOpen: true,
            sidebarWidth: 280,
            isVoiceMode: false,
            isListening: false,

            init: () => {
                const state = get();
                const updates = {};
                const settings = { ...DEFAULT_SETTINGS, ...(state.settings || {}) };
                const preferences = { ...DEFAULT_PREFERENCES, ...(state.preferences || {}) };
                const conversations = Array.isArray(state.conversations)
                    ? state.conversations.map(normalizeConversation)
                    : [];
                const projects = Array.isArray(state.projects)
                    ? state.projects.map(normalizeProject)
                    : [];
                const folders = Array.isArray(state.folders)
                    ? state.folders.map(normalizeFolder)
                    : [];

                if (!state.sessionId) {
                    updates.sessionId = createId('session');
                }
                updates.settings = settings;
                updates.preferences = preferences;
                updates.projects = projects;
                updates.folders = folders;

                if (conversations.length === 0) {
                    const now = new Date().toISOString();
                    const newConversation = {
                        id: createId('conv'),
                        title: 'New chat',
                        messages: [],
                        createdAt: now,
                        updatedAt: now,
                        archived: false,
                        pinned: false,
                        tags: [],
                        projectId: null,
                        folderId: null,
                    };
                    updates.conversations = [newConversation];
                    updates.activeConversationId = newConversation.id;
                } else {
                    updates.conversations = conversations;
                    if (!state.activeConversationId || !conversations.find((c) => c.id === state.activeConversationId)) {
                        updates.activeConversationId = conversations[0].id;
                    }
                }

                set(updates);
            },

            setActiveConversation: (id) => set({ activeConversationId: id }),

            createConversation: (overrides = {}) => {
                const now = new Date().toISOString();
                const conversation = normalizeConversation({
                    id: createId('conv'),
                    title: 'New chat',
                    messages: [],
                    createdAt: now,
                    updatedAt: now,
                    archived: false,
                    pinned: false,
                    tags: [],
                    ...overrides,
                });
                set((state) => ({
                    conversations: [conversation, ...state.conversations],
                    activeConversationId: conversation.id,
                }));
                return conversation.id;
            },

            setConversationMessages: (conversationId, updater) => set((state) => {
                const conversations = state.conversations.map((conv) => {
                    if (conv.id !== conversationId) return conv;
                    const prevMessages = Array.isArray(conv.messages) ? conv.messages : [];
                    const nextMessages = typeof updater === 'function' ? updater(prevMessages) : updater;
                    const title = conv.title && conv.title !== 'New chat' ? conv.title : deriveTitle(nextMessages);
                    return {
                        ...conv,
                        title: title || conv.title,
                        messages: Array.isArray(nextMessages) ? nextMessages : prevMessages,
                        updatedAt: new Date().toISOString(),
                    };
                });
                return { conversations };
            }),

            updateConversation: (conversationId, updates) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId
                        ? { ...conv, ...updates, updatedAt: new Date().toISOString() }
                        : conv
                )),
            })),

            archiveConversation: (conversationId, archived) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId ? { ...conv, archived: Boolean(archived) } : conv
                )),
            })),

            deleteConversation: (conversationId) => set((state) => {
                const remaining = state.conversations.filter((conv) => conv.id !== conversationId);
                if (remaining.length === 0) {
                    const now = new Date().toISOString();
                    const fallback = normalizeConversation({
                        id: createId('conv'),
                        title: 'New chat',
                        messages: [],
                        createdAt: now,
                        updatedAt: now,
                    });
                    return {
                        conversations: [fallback],
                        activeConversationId: fallback.id,
                    };
                }
                const activeId = state.activeConversationId === conversationId
                    ? remaining[0].id
                    : state.activeConversationId;
                return {
                    conversations: remaining,
                    activeConversationId: activeId,
                };
            }),

            renameConversation: (conversationId, title) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId
                        ? { ...conv, title: title || conv.title, updatedAt: new Date().toISOString() }
                        : conv
                )),
            })),

            togglePinConversation: (conversationId) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId ? { ...conv, pinned: !conv.pinned } : conv
                )),
            })),

            updateTags: (conversationId, tags) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId ? { ...conv, tags: Array.isArray(tags) ? tags : [] } : conv
                )),
            })),

            assignProject: (conversationId, projectId) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId ? { ...conv, projectId: projectId || null } : conv
                )),
            })),

            assignFolder: (conversationId, folderId) => set((state) => ({
                conversations: state.conversations.map((conv) => (
                    conv.id === conversationId ? { ...conv, folderId: folderId || null } : conv
                )),
            })),

            bulkAction: ({ action, ids, folderId }) => set((state) => {
                const idSet = new Set(ids || []);
                if (action === 'delete') {
                    const remaining = state.conversations.filter((conv) => !idSet.has(conv.id));
                    const activeId = idSet.has(state.activeConversationId)
                        ? (remaining[0]?.id || null)
                        : state.activeConversationId;
                    if (!remaining.length) {
                        const now = new Date().toISOString();
                        const fallback = normalizeConversation({
                            id: createId('conv'),
                            title: 'New chat',
                            messages: [],
                            createdAt: now,
                            updatedAt: now,
                        });
                        return {
                            conversations: [fallback],
                            activeConversationId: fallback.id,
                        };
                    }
                    return {
                        conversations: remaining,
                        activeConversationId: activeId,
                    };
                }

                const updates = {
                    archive: (conv) => ({ ...conv, archived: true }),
                    unarchive: (conv) => ({ ...conv, archived: false }),
                    pin: (conv) => ({ ...conv, pinned: true }),
                    unpin: (conv) => ({ ...conv, pinned: false }),
                    'move-folder': (conv) => ({ ...conv, folderId: folderId || null }),
                };
                const apply = updates[action];
                if (!apply) return {};
                return {
                    conversations: state.conversations.map((conv) => (
                        idSet.has(conv.id) ? apply(conv) : conv
                    )),
                };
            }),

            createProject: (name) => {
                const project = normalizeProject({ id: createId('proj'), name });
                set((state) => ({
                    projects: [project, ...state.projects],
                }));
                return project.id;
            },

            updateProject: (projectId, updates) => set((state) => ({
                projects: state.projects.map((project) => (
                    project.id === projectId
                        ? { ...project, ...updates, updatedAt: new Date().toISOString() }
                        : project
                )),
            })),

            addProjectFiles: (projectId, files) => set((state) => ({
                projects: state.projects.map((project) => (
                    project.id === projectId
                        ? {
                            ...project,
                            files: [...(project.files || []), ...(Array.isArray(files) ? files : [])],
                            updatedAt: new Date().toISOString(),
                        }
                        : project
                )),
            })),

            removeProjectFile: (projectId, fileId) => set((state) => ({
                projects: state.projects.map((project) => (
                    project.id === projectId
                        ? {
                            ...project,
                            files: (project.files || []).filter((file) => file.id !== fileId),
                            updatedAt: new Date().toISOString(),
                        }
                        : project
                )),
            })),

            createFolder: (name) => {
                const folder = normalizeFolder({ id: createId('folder'), name });
                set((state) => ({
                    folders: [folder, ...state.folders],
                }));
                return folder.id;
            },

            renameFolder: (folderId, name) => set((state) => ({
                folders: state.folders.map((folder) => (
                    folder.id === folderId ? { ...folder, name: name || folder.name } : folder
                )),
            })),

            deleteFolder: (folderId) => set((state) => ({
                folders: state.folders.filter((folder) => folder.id !== folderId),
                conversations: state.conversations.map((conv) => (
                    conv.folderId === folderId ? { ...conv, folderId: null } : conv
                )),
            })),

            addArtifact: (artifact) => set((state) => ({
                artifacts: [artifact, ...state.artifacts],
            })),

            addCodeSnippet: (snippet) => set((state) => ({
                codeSnippets: [snippet, ...state.codeSnippets],
            })),

            updateSettings: (updates) => set((state) => ({
                settings: { ...state.settings, ...updates },
            })),

            updatePreferences: (updates) => set((state) => ({
                preferences: { ...state.preferences, ...updates },
            })),

            setSidebarWidth: (width) => set({ sidebarWidth: width }),
            toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
            setVoiceMode: (isActive) => set({ isVoiceMode: isActive }),
            setListening: (isListening) => set({ isListening }),

            resetData: () => {
                const now = new Date().toISOString();
                const conversation = normalizeConversation({
                    id: createId('conv'),
                    title: 'New chat',
                    messages: [],
                    createdAt: now,
                    updatedAt: now,
                });
                set({
                    conversations: [conversation],
                    activeConversationId: conversation.id,
                    projects: [],
                    folders: [],
                    artifacts: [],
                    codeSnippets: [],
                    settings: { ...DEFAULT_SETTINGS },
                    preferences: { ...DEFAULT_PREFERENCES },
                    sessionId: createId('session'),
                    sidebarWidth: 280,
                });
            },
        }),
        {
            name: 'malaya-llm-storage',
            partialize: (state) => {
                const redactEnabled = Boolean(state.settings?.redactPii);
                const projectPolicies = new Map(
                    (state.projects || []).map((project) => [project.id, project.piiPolicy])
                );
                const shouldRedactProject = (projectId) => (
                    redactEnabled || projectPolicies.get(projectId) === 'redact'
                );
                const sanitizedConversations = (state.conversations || []).map((conv) => {
                    if (!shouldRedactProject(conv.projectId)) return conv;
                    const messages = (conv.messages || []).map((msg) => ({
                        ...msg,
                        content: redactPiiText(msg.content),
                        attachments: (msg.attachments || []).map((att) => ({
                            ...att,
                            content: redactPiiText(att.content),
                        })),
                    }));
                    return {
                        ...conv,
                        title: redactPiiText(conv.title),
                        messages,
                    };
                });
                const sanitizedProjects = (state.projects || []).map((project) => {
                    if (!shouldRedactProject(project.id)) return project;
                    return {
                        ...project,
                        name: redactPiiText(project.name),
                        instructions: redactPiiText(project.instructions),
                        files: (project.files || []).map((file) => ({
                            ...file,
                            name: redactPiiText(file.name),
                            content: redactPiiText(file.content),
                        })),
                    };
                });
                const sanitizedArtifacts = redactEnabled
                    ? (state.artifacts || []).map((artifact) => ({
                        ...artifact,
                        title: redactPiiText(artifact.title),
                        content: redactPiiText(artifact.content),
                    }))
                    : state.artifacts;
                const sanitizedCode = redactEnabled
                    ? (state.codeSnippets || []).map((snippet) => ({
                        ...snippet,
                        title: redactPiiText(snippet.title),
                        content: redactPiiText(snippet.content),
                    }))
                    : state.codeSnippets;

                return {
                    conversations: sanitizedConversations,
                    activeConversationId: state.activeConversationId,
                    projects: sanitizedProjects,
                    folders: state.folders,
                    artifacts: sanitizedArtifacts,
                    codeSnippets: sanitizedCode,
                    settings: state.settings,
                    preferences: state.preferences,
                    sidebarWidth: state.sidebarWidth,
                    sessionId: state.sessionId,
                };
            },
        }
    )
);

export default useStore;
