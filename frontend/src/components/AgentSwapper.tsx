import { useState, useEffect } from 'react'

interface AgentOption {
  file: string
  name: string
}

export default function AgentSwapper({ apiUrl, onSwap }: { apiUrl: string; onSwap: () => void }) {
  const [agents, setAgents] = useState<AgentOption[]>([])
  const [current, setCurrent] = useState<string>('')
  const [swapping, setSwapping] = useState(false)

  useEffect(() => {
    // Fetch available agents
    fetch(`${apiUrl}/agents`)
      .then(r => r.json())
      .then(setAgents)
      .catch(() => {})

    // Fetch current agent
    fetch(`${apiUrl}/agent`)
      .then(r => r.json())
      .then(data => setCurrent(data.name))
      .catch(() => {})
  }, [apiUrl])

  const handleSwap = async (agentFile: string) => {
    setSwapping(true)
    try {
      const res = await fetch(`${apiUrl}/agent/swap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_file: agentFile }),
      })
      if (res.ok) {
        const data = await res.json()
        setCurrent(data.name)
        onSwap()
      }
    } catch { /* ignore */ }
    finally { setSwapping(false) }
  }

  if (agents.length === 0) return null

  return (
    <div>
      <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Switch Agent</h3>
      <div className="flex flex-wrap gap-1.5">
        {agents.map(agent => (
          <button
            key={agent.file}
            onClick={() => handleSwap(agent.file)}
            disabled={swapping || agent.name === current}
            className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
              agent.name === current
                ? 'bg-slate-900 text-white border-slate-900'
                : 'bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50'
            } disabled:opacity-60`}
          >
            {agent.name}
          </button>
        ))}
      </div>
    </div>
  )
}
