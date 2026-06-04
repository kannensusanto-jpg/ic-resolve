import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Send, Loader2, MessageSquare, Sparkles } from 'lucide-react'
import { api } from '../api'
import clsx from 'clsx'
import { useDataStatus } from '../hooks/useDataStatus'

const SUGGESTED_QUERIES = [
  'Show me all open disputes over £50,000',
  'Which entities have not confirmed their close?',
  'What is the total unmatched exposure?',
  'Summarise all timing differences',
  'Which pairs have the largest discrepancies?',
  'Are any SLA deadlines breached?',
  'List all missing postings',
  'What are the FX-related disputes?',
]

interface Message {
  role: 'user' | 'assistant'
  content: string
  model?: string
  timestamp: Date
}

export default function QueryInterface() {
  const { latestPeriod: period } = useDataStatus()
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const queryMut = useMutation({
    mutationFn: (q: string) => api.query(q, period).then(r => r.data),
    onSuccess: (data) => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        model: data.ai_model,
        timestamp: new Date(),
      }])
    },
    onError: () => {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I could not process that query. Please check that the ANTHROPIC_API_KEY is set.',
        timestamp: new Date(),
      }])
    },
  })

  const submit = (query: string) => {
    if (!query.trim()) return
    setMessages(prev => [...prev, {
      role: 'user',
      content: query,
      timestamp: new Date(),
    }])
    setInput('')
    queryMut.mutate(query)
  }

  return (
    <div className="flex flex-col h-full p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">AI Query Interface</h1>
        <p className="text-sm text-gray-500 mt-1">
          Ask natural language questions about the {period} intercompany reconciliation
        </p>
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto bg-white rounded-xl border border-gray-200 p-4 space-y-4 mb-4 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full py-12 text-center">
            <Sparkles className="w-10 h-10 text-indigo-300 mb-3" />
            <p className="text-gray-500 font-medium">Ask anything about the reconciliation</p>
            <p className="text-gray-400 text-sm mt-1">
              Try one of the suggested queries below, or type your own question
            </p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={clsx('flex', msg.role === 'user' ? 'justify-end' : 'justify-start')}
            >
              <div className={clsx(
                'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
                msg.role === 'user'
                  ? 'bg-brand-600 text-white rounded-br-sm'
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm',
              )}>
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-1.5 mb-1.5 text-xs text-gray-400">
                    <Sparkles size={11} />
                    IC Resolve AI
                    {msg.model && msg.model !== 'none' && (
                      <span className="ml-1 text-gray-300">· {msg.model}</span>
                    )}
                  </div>
                )}
                <div className="whitespace-pre-wrap">{msg.content}</div>
                <div className={clsx(
                  'text-xs mt-1.5',
                  msg.role === 'user' ? 'text-indigo-200' : 'text-gray-400',
                )}>
                  {msg.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
        {queryMut.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggested queries */}
      {messages.length === 0 && (
        <div className="mb-4">
          <p className="text-xs text-gray-400 mb-2 uppercase tracking-wide font-medium">Suggested queries</p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTED_QUERIES.map(q => (
              <button
                key={q}
                onClick={() => submit(q)}
                className="px-3 py-1.5 text-xs bg-white border border-gray-200 rounded-full text-gray-600 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-700 transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <MessageSquare className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(input) } }}
            placeholder="Ask about the reconciliation status..."
            disabled={queryMut.isPending}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent disabled:opacity-50"
          />
        </div>
        <button
          onClick={() => submit(input)}
          disabled={!input.trim() || queryMut.isPending}
          className="px-4 py-3 bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {queryMut.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
      </div>
    </div>
  )
}
