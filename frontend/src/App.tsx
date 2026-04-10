import { useState, useCallback, useEffect } from 'react'
import Chat from './components/Chat'
import DocUpload from './components/DocUpload'
import AgentCard from './components/AgentCard'
import AgentSwapper from './components/AgentSwapper'

const API = import.meta.env.VITE_API_URL || '/api'

export default function App() {
  const [agentRefreshKey, setAgentRefreshKey] = useState(0)
  const [chatKey, setChatKey] = useState(0)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [agentName, setAgentName] = useState('Agent')

  const fetchAgentName = useCallback(() => {
    fetch(`${API}/agent`)
      .then(r => r.json())
      .then(data => setAgentName(data.name))
      .catch(() => {})
  }, [])

  useEffect(() => { fetchAgentName() }, [fetchAgentName])

  const handleAgentSwap = useCallback(() => {
    setAgentRefreshKey(k => k + 1)
    setChatKey(k => k + 1)
    fetchAgentName()
  }, [fetchAgentName])

  return (
    <div className="h-screen flex bg-white">
      {/* Mobile sidebar toggle */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white border border-slate-200 rounded-lg shadow-sm"
      >
        <svg className="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'translate-x-0' : '-translate-x-full'} lg:translate-x-0 fixed lg:relative z-40 w-80 h-full border-r border-slate-200 bg-slate-50 flex flex-col transition-transform duration-200 ease-in-out`}>
        <div className="p-4 border-b border-slate-200">
          <h1 className="text-lg font-semibold text-slate-900">Markdown Agent</h1>
          <p className="text-xs text-slate-500 mt-0.5">Your agent is defined in agent.md</p>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          <AgentSwapper apiUrl={API} onSwap={handleAgentSwap} />
          <AgentCard apiUrl={API} key={`agent-${agentRefreshKey}`} />
          <DocUpload apiUrl={API} />
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 z-30 bg-black/20"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col min-w-0">
        <Chat apiUrl={API} agentName={agentName} key={`chat-${chatKey}`} />
      </div>
    </div>
  )
}
