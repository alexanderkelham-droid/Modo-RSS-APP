'use client'

import { useState } from 'react'

interface BriefResponse {
  brief: string
  article_count: number
  country_code: string | null
  topic: string | null
  date_range: {
    start: string
    end: string
  }
}

export default function AIAnalystPage() {
  const [message, setMessage] = useState('')
  const [countryCode, setCountryCode] = useState('')
  const [topic, setTopic] = useState('')
  const [days, setDays] = useState(7)
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState<Array<{ role: string; content: string; metadata?: any }>>([
    {
      role: 'assistant',
      content:
        "Hello! I'm your energy analyst AI. You can:\n\n1. **Generate a Brief**: Select a country or topic and click 'Generate Brief' to get an AI-powered summary of recent developments.\n\n2. **Ask Questions**: Type a question about energy trends, specific projects, or market data and I'll answer using the latest articles.",
    },
  ])

  const handleGenerateBrief = async () => {
    if (loading) return

    setLoading(true)
    const requestInfo = `Generating brief for: ${countryCode || 'all countries'}${topic ? `, topic: ${topic}` : ''}, last ${days} days`
    
    setMessages(prev => [...prev, { 
      role: 'user', 
      content: requestInfo 
    }])

    try {
      const response = await fetch('http://localhost:8000/briefs/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          country_code: countryCode || null,
          topic: topic || null,
          days: days,
          max_articles: 15,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to generate brief: ${response.statusText}`)
      }

      const data: BriefResponse = await response.json()

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.brief,
          metadata: {
            article_count: data.article_count,
            date_range: data.date_range,
          },
        },
      ])
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Error generating brief: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleSend = async () => {
    if (!message.trim() || loading) return

    const newMessages = [...messages, { role: 'user', content: message }]
    setMessages(newMessages)
    setMessage('')
    setLoading(true)

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: message,
          k: 10,
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to get answer: ${response.statusText}`)
      }

      const data = await response.json()

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          metadata: {
            citations: data.citations,
            confidence: data.confidence,
          },
        },
      ])
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-900 text-center">AI Research Assistant</h1>
        <p className="text-gray-500 text-sm mt-0.5 text-center">Powered by RAG on your verified news corpus.</p>
        
        {/* Brief Generation Controls */}
        <div className="mt-4 max-w-4xl mx-auto">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Generate Country/Topic Brief</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
              <input
                type="text"
                value={countryCode}
                onChange={(e) => setCountryCode(e.target.value.toUpperCase())}
                placeholder="Country (e.g., US, UK)"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Topic (optional)"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="number"
                value={days}
                onChange={(e) => setDays(parseInt(e.target.value) || 7)}
                min={1}
                max={365}
                placeholder="Days"
                className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={handleGenerateBrief}
                disabled={loading}
                className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Generating...' : 'Generate Brief'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-auto p-5">
        <div className="max-w-3xl mx-auto space-y-4">
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
            >
              {msg.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
                  AI
                </div>
              )}
              <div
                className={`p-3 rounded-lg max-w-xl text-sm ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {msg.metadata?.article_count !== undefined && (
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                    Based on {msg.metadata.article_count} articles
                  </div>
                )}
                {msg.metadata?.confidence && (
                  <div className="mt-2 pt-2 border-t border-gray-200 text-xs text-gray-500">
                    Confidence: {msg.metadata.confidence}
                  </div>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center flex-shrink-0 text-white text-xs font-bold">
                AI
              </div>
              <div className="p-3 rounded-lg bg-white border border-gray-200 text-sm text-gray-500">
                Thinking...
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <p className="text-xs text-gray-500 mb-2">Ask a specific question about energy trends or news:</p>
          <div className="flex gap-2">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
              placeholder="Ask about energy trends, projects, or market data..."
              disabled={loading}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            />
            <button
              onClick={handleSend}
              disabled={loading || !message.trim()}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
