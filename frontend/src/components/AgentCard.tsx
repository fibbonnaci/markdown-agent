import { useState, useEffect } from 'react'

interface AgentInfo {
  name: string
  purpose: string
  behavior: string
  guardrails: string
  model: string
  tools: { name: string; description: string }[]
  active_tools: string[]
  warnings: string[]
}

export default function AgentCard({ apiUrl }: { apiUrl: string }) {
  const [agent, setAgent] = useState<AgentInfo | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    fetch(`${apiUrl}/agent`)
      .then(r => r.json())
      .then(setAgent)
      .catch(() => {})
  }, [apiUrl])

  if (!agent) return null

  return (
    <div className="border border-slate-200 rounded-lg bg-white">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 text-left"
      >
        <div>
          <h3 className="text-sm font-semibold text-slate-900">{agent.name}</h3>
          <p className="text-xs text-slate-400 mt-0.5">{agent.model}</p>
        </div>
        <svg
          className={`w-4 h-4 text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-slate-100">
          {/* Purpose */}
          <div className="pt-3">
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Purpose</h4>
            <p className="text-xs text-slate-600 leading-relaxed">{agent.purpose}</p>
          </div>

          {/* Tools */}
          <div>
            <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Tools</h4>
            <div className="flex flex-wrap gap-1">
              {agent.tools.map(t => (
                <span
                  key={t.name}
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    agent.active_tools.includes(t.name)
                      ? 'bg-slate-100 text-slate-700'
                      : 'bg-amber-50 text-amber-600 line-through'
                  }`}
                >
                  {t.name}
                </span>
              ))}
            </div>
          </div>

          {/* Behavior */}
          {agent.behavior && (
            <div>
              <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Behavior</h4>
              <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-line">{agent.behavior}</p>
            </div>
          )}

          {/* Guardrails */}
          {agent.guardrails && (
            <div>
              <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">Guardrails</h4>
              <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-line">{agent.guardrails}</p>
            </div>
          )}

          {/* Warnings */}
          {agent.warnings.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded p-2">
              {agent.warnings.map((w, i) => (
                <p key={i} className="text-xs text-amber-700">{w}</p>
              ))}
            </div>
          )}

          <p className="text-[10px] text-slate-400 italic pt-1">
            This agent is defined entirely in agent.md
          </p>
        </div>
      )}
    </div>
  )
}
