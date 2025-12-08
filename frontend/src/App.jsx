
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';

function App() {
  const [mode, setMode] = useState('chat');

  return (
    <div className="flex h-screen bg-[#FAF9F7] text-[#1A1915] font-sans overflow-hidden">
      <Sidebar mode={mode} setMode={setMode} />
      <main className="flex-1 flex flex-col h-full relative">
        <ChatInterface mode={mode} />
      </main>
    </div>
  );
}

export default App;
