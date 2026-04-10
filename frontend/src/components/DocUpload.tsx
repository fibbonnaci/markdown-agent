import { useState, useEffect, useCallback } from 'react'

interface Doc {
  name: string
  chunks: number
}

export default function DocUpload({ apiUrl }: { apiUrl: string }) {
  const [docs, setDocs] = useState<Doc[]>([])
  const [uploading, setUploading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const [lastUpload, setLastUpload] = useState<string | null>(null)

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/docs`)
      if (res.ok) setDocs(await res.json())
    } catch { /* ignore */ }
  }, [apiUrl])

  useEffect(() => { fetchDocs() }, [fetchDocs])

  const uploadFile = async (file: File) => {
    setUploading(true)
    setLastUpload(null)
    try {
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetch(`${apiUrl}/docs/upload`, {
        method: 'POST',
        body: formData,
      })
      if (res.ok) {
        const result = await res.json()
        setLastUpload(`Indexed ${result.chunks} chunks from ${result.name}`)
        fetchDocs()
      }
    } catch (err) {
      setLastUpload(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) uploadFile(file)
    e.target.value = ''
  }

  return (
    <div>
      <h3 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">Documents</h3>

      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors cursor-pointer ${
          dragOver ? 'border-slate-400 bg-slate-100' : 'border-slate-200 hover:border-slate-300'
        }`}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleFileInput}
          className="hidden"
        />
        {uploading ? (
          <div className="flex items-center justify-center gap-2 text-slate-500 text-sm">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Indexing...
          </div>
        ) : (
          <div className="text-slate-400 text-sm">
            <p>Drop PDF or TXT here</p>
            <p className="text-xs mt-0.5">or click to browse</p>
          </div>
        )}
      </div>

      {/* Upload result */}
      {lastUpload && (
        <p className="text-xs text-emerald-600 mt-2">{lastUpload}</p>
      )}

      {/* Document list */}
      {docs.length > 0 && (
        <ul className="mt-3 space-y-1">
          {docs.map(doc => (
            <li key={doc.name} className="flex items-center justify-between text-xs text-slate-600 py-1">
              <span className="truncate mr-2">{doc.name}</span>
              <span className="text-slate-400 whitespace-nowrap">{doc.chunks} chunks</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
