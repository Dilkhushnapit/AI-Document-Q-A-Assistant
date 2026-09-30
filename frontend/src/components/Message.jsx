import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

// Only show the sources the answer actually cited, e.g. "[2]" or "[1][3]".
function citedIds(text) {
  return new Set([...text.matchAll(/\[(\d+)\]/g)].map((m) => Number(m[1])))
}

export default function Message({ message }) {
  const [open, setOpen] = useState(null)

  if (message.role === 'user') {
    return <div className="msg user"><div className="bubble">{message.content}</div></div>
  }

  const cited = citedIds(message.content)
  const sources = (message.sources || []).filter((s) => cited.has(s.id))

  return (
    <div className="msg assistant">
      <div className="bubble">
        {message.content ? (
          <ReactMarkdown>{message.content}</ReactMarkdown>
        ) : (
          <span className="typing">Thinking…</span>
        )}
        {message.error && <p className="error small">{message.error}</p>}
        {sources.length > 0 && (
          <div className="sources">
            <div className="muted small">Sources</div>
            {sources.map((s) => (
              <div key={s.id} className="source">
                <button className="source-chip" onClick={() => setOpen(open === s.id ? null : s.id)}>
                  [{s.id}] {s.source}
                  {s.page > 0 && ` · p.${s.page}`}
                  <span className="muted"> · {Math.round(s.score * 100)}% match</span>
                </button>
                {open === s.id && <blockquote className="source-text">{s.text}</blockquote>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
