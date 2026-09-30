import { useEffect, useRef, useState } from 'react'
import { listDocuments, streamChat } from './api'
import Message from './components/Message'
import Sidebar from './components/Sidebar'

const SUGGESTIONS = [
  'How many days of annual leave do employees get?',
  'What does the SkyNote warranty cover?',
  'Why does RAG use overlapping chunks?',
]

export default function App() {
  const [documents, setDocuments] = useState([])
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  const refreshDocuments = () => listDocuments().then(setDocuments).catch(() => setDocuments([]))

  useEffect(() => { refreshDocuments() }, [])
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  // Update the last (assistant) message in place as stream events arrive.
  const updateLast = (fn) => setMessages((prev) => [...prev.slice(0, -1), fn(prev[prev.length - 1])])

  async function ask(question) {
    question = question.trim()
    if (!question || loading) return
    const history = messages.map(({ role, content }) => ({ role, content }))
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: question },
      { role: 'assistant', content: '', sources: [] },
    ])
    setInput('')
    setLoading(true)
    try {
      await streamChat(question, history, (event) => {
        if (event.type === 'sources') updateLast((m) => ({ ...m, sources: event.sources }))
        if (event.type === 'token') updateLast((m) => ({ ...m, content: m.content + event.text }))
        if (event.type === 'error') updateLast((m) => ({ ...m, error: event.message }))
      })
    } catch (e) {
      updateLast((m) => ({ ...m, error: e.message }))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="layout">
      <Sidebar documents={documents} onChange={refreshDocuments} />
      <main className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              <h2>Ask anything about your documents</h2>
              <p className="muted">Answers are grounded in the uploaded files, with numbered source citations.</p>
              <div className="suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="suggestion" onClick={() => ask(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}
          {messages.map((m, i) => <Message key={i} message={m} />)}
          <div ref={bottomRef} />
        </div>
        <form className="composer" onSubmit={(e) => { e.preventDefault(); ask(input) }}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={documents.length ? 'Ask a question…' : 'Upload a document to get started'}
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>{loading ? '…' : 'Send'}</button>
        </form>
      </main>
    </div>
  )
}
