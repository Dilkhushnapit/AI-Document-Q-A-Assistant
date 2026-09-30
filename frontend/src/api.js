// Thin wrappers around the FastAPI endpoints.

async function check(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export const listDocuments = () => fetch('/api/documents').then(check)

export function uploadDocuments(files) {
  const form = new FormData()
  for (const f of files) form.append('files', f)
  return fetch('/api/documents', { method: 'POST', body: form }).then(check)
}

export const deleteDocument = (name) =>
  fetch(`/api/documents/${encodeURIComponent(name)}`, { method: 'DELETE' }).then(check)

// Streams the answer. The server sends newline-delimited JSON events:
// {type:"sources"}, then many {type:"token"}, then {type:"done"} (or {type:"error"}).
export async function streamChat(question, history, onEvent) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, history }),
  })
  if (!res.ok || !res.body) throw new Error(`Chat request failed (${res.status})`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() // keep the incomplete last line for the next read
    for (const line of lines) if (line.trim()) onEvent(JSON.parse(line))
  }
}
