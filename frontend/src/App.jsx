import React, { useCallback, useEffect, useMemo, useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import SettingsPanel from './components/SettingsPanel';
import CommandPalette from './components/CommandPalette';
import AdminPanel from './components/AdminPanel';
import ImageUploader from './components/ImageUploader';
import PodcastPlayer from './components/PodcastPlayer';
import TouristPlanner from './components/TouristPlanner';
import AgentExecutor from './components/AgentExecutor';
import useStore from './store/useStore';
import { enqueueFeedback, flushFeedbackQueue } from './utils/feedbackQueue';
import { flushAnalyticsQueue, trackEvent } from './utils/analytics';

const API_KEY = import.meta.env.VITE_API_KEY;

const createId = (prefix) => `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

const extractCodeBlocks = (content = '') => {
  const blocks = [];
  const regex = /```([\w-]+)?\n([\s\S]*?)```/g;
  let match;
  while ((match = regex.exec(content)) !== null) {
    blocks.push({
      language: match[1] || 'text',
      content: match[2].replace(/\n$/, ''),
    });
  }
  return blocks;
};

const truncateText = (text, limit = 48) => {
  const trimmed = (text || '').trim().replace(/\s+/g, ' ');
  if (!trimmed) return '';
  if (trimmed.length <= limit) return trimmed;
  return `${trimmed.slice(0, limit)}...`;
};

const downloadFile = (filename, content, type = 'application/json') => {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
};

function App() {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [adminOpen, setAdminOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [activeFeature, setActiveFeature] = useState(null);
  const [promptVariants, setPromptVariants] = useState([]);

  const {
    isSidebarOpen,
    sidebarWidth,
    conversations,
    activeConversationId,
    projects,
    folders,
    artifacts,
    codeSnippets,
    settings,
    preferences,
    sessionId,
    init,
    setActiveConversation,
    createConversation,
    setConversationMessages,
    archiveConversation,
    deleteConversation,
    renameConversation,
    togglePinConversation,
    updateTags,
    assignProject,
    assignFolder,
    bulkAction,
    createProject,
    updateProject,
    addProjectFiles,
    removeProjectFile,
    createFolder,
    renameFolder,
    deleteFolder,
    addArtifact,
    addCodeSnippet,
    updateSettings,
    updatePreferences,
    setSidebarWidth,
    resetData,
  } = useStore();

  useEffect(() => {
    init();
  }, [init]);

  useEffect(() => {
    document.body.classList.toggle('high-contrast', Boolean(settings?.highContrast));
    document.body.classList.toggle('reduce-motion', Boolean(settings?.reduceMotion));
  }, [settings?.highContrast, settings?.reduceMotion]);

  useEffect(() => {
    flushAnalyticsQueue();
    flushFeedbackQueue();
    const handleOnline = () => {
      flushAnalyticsQueue();
      flushFeedbackQueue();
    };
    window.addEventListener('online', handleOnline);
    fetch('/health').catch(() => { });
    return () => window.removeEventListener('online', handleOnline);
  }, []);

  useEffect(() => {
    const loadVariants = async () => {
      try {
        const res = await fetch('/api/chat/prompt-variants', {
          headers: {
            ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
          },
        });
        if (!res.ok) return;
        const data = await res.json();
        if (Array.isArray(data?.variants)) {
          setPromptVariants(data.variants);
        }
      } catch (error) {
        console.error('Failed to load prompt variants', error);
      }
    };
    loadVariants();
  }, []);

  useEffect(() => {
    const handleKeyDown = (event) => {
      const isMeta = event.metaKey || event.ctrlKey;
      if (isMeta && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCommandOpen(true);
      }
      if (isMeta && event.key === ',') {
        event.preventDefault();
        setSettingsOpen(true);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const activeConversation = useMemo(() => (
    conversations.find((conv) => conv.id === activeConversationId) || conversations[0] || null
  ), [conversations, activeConversationId]);

  const activeProject = useMemo(() => (
    activeConversation?.projectId
      ? projects.find((project) => project.id === activeConversation.projectId)
      : null
  ), [projects, activeConversation]);

  const effectiveProfile = useMemo(() => (
    [preferences?.profile, preferences?.instructions].filter(Boolean).join('\n')
  ), [preferences]);

  const projectMemoryEnabled = settings?.projectMemoryEnabled !== false
    && (activeProject?.memoryScope || 'enabled') !== 'disabled';
  const projectId = projectMemoryEnabled ? activeProject?.id || null : null;

  const promptVariant = activeProject?.promptVariant || settings?.promptVariant || 'default';
  const responseModeDefault = settings?.responseMode || 'auto';

  const setMessages = useCallback((updater) => {
    if (!activeConversation) return;
    setConversationMessages(activeConversation.id, updater);
  }, [activeConversation, setConversationMessages]);

  const handleNewChat = useCallback(() => {
    const newId = createConversation();
    setActiveConversation(newId);
  }, [createConversation, setActiveConversation]);

  const handleResizeStart = (event) => {
    if (settings?.sidebarCollapsed) return;
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = sidebarWidth;
    const handleMove = (moveEvent) => {
      const nextWidth = Math.min(420, Math.max(220, startWidth + (moveEvent.clientX - startX)));
      setSidebarWidth(nextWidth);
    };
    const handleUp = () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };
    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
  };

  const handleSaveArtifact = (conversationId) => {
    const conv = conversations.find((item) => item.id === conversationId);
    if (!conv) return;
    const assistantMessages = (conv.messages || []).filter((msg) => msg.role === 'assistant' && msg.content);
    const latest = assistantMessages[assistantMessages.length - 1];
    if (!latest) return;
    const artifact = {
      id: createId('artifact'),
      conversationId,
      conversationTitle: conv.title || 'Conversation',
      title: truncateText(latest.content) || 'Artifact',
      content: latest.content,
      createdAt: new Date().toISOString(),
    };
    addArtifact(artifact);
    trackEvent('artifact_saved', { conversation_id: conversationId });
  };

  const handleSaveCode = (conversationId) => {
    const conv = conversations.find((item) => item.id === conversationId);
    if (!conv) return;
    const assistantMessages = (conv.messages || []).filter((msg) => msg.role === 'assistant' && msg.content);
    const blocks = assistantMessages.flatMap((msg) => extractCodeBlocks(msg.content));
    if (blocks.length === 0) return;
    const block = blocks[blocks.length - 1];
    const snippet = {
      id: createId('code'),
      conversationId,
      conversationTitle: conv.title || 'Conversation',
      title: truncateText(block.content.split('\n')[0]) || 'Snippet',
      language: block.language || 'text',
      content: block.content,
      createdAt: new Date().toISOString(),
    };
    addCodeSnippet(snippet);
    trackEvent('code_saved', { conversation_id: conversationId, language: snippet.language });
  };

  const handleFeedback = async (payload) => {
    if (!payload?.rating) return;
    const body = {
      conversation_id: payload.conversationId || null,
      message_id: payload.messageId || null,
      rating: payload.rating,
      comment: payload.comment || null,
      model_provider: payload.model?.provider || null,
      model_name: payload.model?.name || null,
      metadata: payload.metadata || {},
    };
    try {
      const res = await fetch('/api/chat/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error('Feedback error');
    } catch (error) {
      enqueueFeedback(body);
    }
  };

  const handleExportData = () => {
    const payload = {
      exportedAt: new Date().toISOString(),
      conversations,
      projects,
      folders,
      artifacts,
      codeSnippets,
      settings,
      preferences,
    };
    downloadFile('malaya-export.json', JSON.stringify(payload, null, 2));
  };

  const handleClearData = () => {
    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('malaya-llm-storage');
    }
    resetData();
  };

  useEffect(() => {
    const now = Date.now();
    const idsToDelete = [];
    conversations.forEach((conv) => {
      const project = conv.projectId ? projects.find((item) => item.id === conv.projectId) : null;
      const retention = Number.isFinite(project?.retentionDays) && project?.retentionDays > 0
        ? project.retentionDays
        : (settings?.retentionDays || 0);
      if (!retention) return;
      const updatedAt = new Date(conv.updatedAt || conv.createdAt || now).getTime();
      const expiry = updatedAt + retention * 24 * 60 * 60 * 1000;
      if (expiry <= now) {
        idsToDelete.push(conv.id);
      }
    });
    if (idsToDelete.length) {
      bulkAction({ action: 'delete', ids: idsToDelete });
    }
  }, [conversations, projects, settings?.retentionDays, bulkAction]);

  const commandItems = useMemo(() => {
    const items = [
      {
        id: 'new-chat',
        label: 'New chat',
        description: 'Start a fresh conversation',
        shortcut: 'N',
        onSelect: handleNewChat,
      },
      {
        id: 'open-settings',
        label: 'Open settings',
        description: 'Workspace preferences',
        shortcut: 'Cmd+,',
        onSelect: () => setSettingsOpen(true),
      },
      {
        id: 'open-admin',
        label: 'Open admin console',
        description: 'Operations dashboard',
        onSelect: () => setAdminOpen(true),
      },
    ];
    conversations.forEach((conv) => {
      items.push({
        id: `conv-${conv.id}`,
        label: conv.title || 'New chat',
        description: conv.projectId ? 'Project chat' : 'Conversation',
        onSelect: () => setActiveConversation(conv.id),
      });
    });
    return items;
  }, [conversations, handleNewChat, setActiveConversation]);

  const effectiveSidebarWidth = settings?.sidebarCollapsed ? 84 : sidebarWidth;

  return (
    <div className="flex h-screen w-full bg-[#f8f9fa] overflow-hidden">
      <div
        className={`h-full border-r border-[#e5e7eb] bg-[#f8f9fa] transition-all duration-300 ease-in-out ${isSidebarOpen ? 'opacity-100' : 'opacity-0 w-0 overflow-hidden'}`}
        style={{ width: isSidebarOpen ? `${effectiveSidebarWidth}px` : '0px' }}
      >
        <Sidebar
          width={effectiveSidebarWidth}
          conversations={conversations}
          activeId={activeConversation?.id}
          onSelectConversation={setActiveConversation}
          onNewChat={handleNewChat}
          onArchiveConversation={archiveConversation}
          onDeleteConversation={deleteConversation}
          onAssignProject={assignProject}
          onCreateProject={createProject}
          onSaveArtifact={handleSaveArtifact}
          onSaveCode={handleSaveCode}
          onRenameConversation={renameConversation}
          onTogglePinConversation={togglePinConversation}
          onUpdateTags={updateTags}
          folders={folders}
          onCreateFolder={createFolder}
          onRenameFolder={renameFolder}
          onDeleteFolder={deleteFolder}
          onAssignFolder={assignFolder}
          onBulkAction={bulkAction}
          projects={projects}
          artifacts={artifacts}
          codeSnippets={codeSnippets}
          onUpdateProject={updateProject}
          onAddProjectFiles={addProjectFiles}
          onRemoveProjectFile={removeProjectFile}
          onOpenAdmin={() => setAdminOpen(true)}
          onOpenSettings={() => setSettingsOpen(true)}
          collapsed={settings?.sidebarCollapsed}
          onToggleCollapse={() => updateSettings({ sidebarCollapsed: !settings?.sidebarCollapsed })}
          onResizeStart={handleResizeStart}
          semanticSearch={settings?.semanticSearch}
          onToggleSemanticSearch={(nextValue) => updateSettings({ semanticSearch: Boolean(nextValue) })}
          promptVariants={promptVariants}
        />
      </div>

      <div className="flex-1 h-full min-w-0 bg-white relative flex flex-col">
        <div className="flex-1 min-h-0">
          {activeConversation ? (
            <ChatInterface
              key={activeConversation.id}
              onNewChat={handleNewChat}
              onFeatureSelect={setActiveFeature}
              messages={activeConversation.messages || []}
              setMessages={setMessages}
              conversationId={activeConversation.id}
              onOpenCommandPalette={() => setCommandOpen(true)}
              onOpenSettings={() => setSettingsOpen(true)}
              projectId={projectId}
              projectInstructions={activeProject?.instructions || ''}
              projectFiles={activeProject?.files || []}
              tone={preferences?.tone}
              profile={effectiveProfile}
              settings={settings}
              onUpdatePreferences={updatePreferences}
              onFeedback={handleFeedback}
              promptVariant={promptVariant}
              defaultResponseMode={responseModeDefault}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">
              Select a conversation to start
            </div>
          )}
        </div>
      </div>

      {activeFeature === 'snap' && (
        <ImageUploader
          onClose={() => setActiveFeature(null)}
          onTranslationResult={(result) => console.log('Translation:', result)}
        />
      )}
      {activeFeature === 'podcast' && (
        <PodcastPlayer onClose={() => setActiveFeature(null)} />
      )}
      {activeFeature === 'tourist' && (
        <TouristPlanner
          onClose={() => setActiveFeature(null)}
          onItineraryGenerated={(result) => console.log('Itinerary:', result)}
        />
      )}
      {activeFeature === 'agent' && (
        <AgentExecutor
          onClose={() => setActiveFeature(null)}
          onResult={(result) => console.log('Agent result:', result)}
        />
      )}

      <SettingsPanel
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        settings={settings}
        onUpdateSettings={updateSettings}
        preferences={preferences}
        onUpdatePreferences={updatePreferences}
        onExportData={handleExportData}
        onClearData={handleClearData}
        sessionId={sessionId}
        promptVariants={promptVariants}
      />

      <AdminPanel
        open={adminOpen}
        onClose={() => setAdminOpen(false)}
      />

      <CommandPalette
        open={commandOpen}
        onClose={() => setCommandOpen(false)}
        items={commandItems}
      />
    </div>
  );
}

export default App;
