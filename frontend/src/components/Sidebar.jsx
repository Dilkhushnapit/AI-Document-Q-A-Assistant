import { useRef, useState } from 'react'
import { deleteDocument, uploadDocuments } from '../api'

export default function Sidebar({ documents, onChange }) {
  const inputRef = useRef(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  async function handleFiles(fileList) {
    if (!fileList.length) return
    setBusy(true)
    setError('')
    try {
      await uploadDocuments(fileList)
      await onChange()
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
      inputRef.current.value = ''
    }
  }

  async function handleDelete(name) {
    await deleteDocument(name)
    await onChange()
  }

  const totalChunks = documents.reduce((sum, d) => sum + d.chunks, 0)

  return (
    <aside className="sidebar">
      <h1 className="brand">DocQ&amp;A</h1>
      <p className="muted small">Ask questions about your own documents.</p>

      <label
        className={`dropzone ${busy ? 'busy' : ''}`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          handleFiles([...e.dataTransfer.files])
        }}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept=".pdf,.txt,.md,.docx"
          hidden
          onChange={(e) => handleFiles([...e.target.files])}
        />
        {busy ? 'Indexing…' : 'Drop files or click to upload'}
        <span className="muted small">PDF, DOCX, TXT, MD</span>
      </label>
      {error && <p className="error small">{error}</p>}

      <h2 className="section-title">
        Documents <span className="muted">({documents.length} · {totalChunks} chunks)</span>
      </h2>
      <ul className="doc-list">
        {documents.length === 0 && <li className="muted small">Nothing indexed yet.</li>}
        {documents.map((d) => (
          <li key={d.name} className="doc-item">
            <div className="doc-name" title={d.name}>{d.name}</div>
            <span className="muted small">{d.chunks}</span>
            <button className="icon-btn" aria-label={`Remove ${d.name}`} onClick={() => handleDelete(d.name)}>
              ×
            </button>
          </li>
        ))}
      </ul>
    </aside>
  )
}
