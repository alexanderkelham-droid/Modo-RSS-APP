'use client'

import { useState, useRef, useEffect } from 'react'
import { sendChatMessage } from '@/lib/api'
import { ChatMessage, Citation } from '@/lib/types'

interface ChatPanelProps {
  selectedCountry: string | null
  selectedTopics: string[]
  days: number
}

export default function ChatPanel({
  selectedCountry,
  selectedTopics,
  days,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [citations, setCitations] = useState<Citation[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const filters: any = {}
      if (selectedCountry) {
        filters.countries = [selectedCountry]
      }
      if (selectedTopics.length > 0) {
        filters.topics = selectedTopics
      }
      
      // Add date filter
      const date_from = new Date()
      date_from.setDate(date_from.getDate() - days)
      filters.date_from = date_from.toISOString().split('T')[0]

      const response = await sendChatMessage({
        question: userMessage.content,
        filters: Object.keys(filters).length > 0 ? filters : undefined,
        k: 8,
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.answer,
      }

      setMessages((prev) => [...prev, assistantMessage])
      setCitations(response.citations)
    } catch (error) {
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="w-96 bg-white border-l border-gray-200 flex flex-col h-screen">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Ask Questions</h2>
        <p className="text-xs text-gray-500 mt-1">
          Chat with your energy transition news corpus
        </p>
        {(selectedCountry || selectedTopics.length > 0) && (
          <div className="mt-2 flex flex-wrap gap-1">
            {selectedCountry && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-primary-100 text-primary-800">
                {selectedCountry}
              </span>
            )}
            {selectedTopics.map((topic) => (
              <span
                key={topic}
                className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-800"
              >
                {topic}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
            <p className="mt-2 text-sm">Ask a question about energy transition news</p>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-primary-500 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{message.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Citations */}
      {citations.length > 0 && (
        <div className="border-t border-gray-200 p-4 bg-gray-50 max-h-48 overflow-y-auto custom-scrollbar">
          <h3 className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
            Sources ({citations.length})
          </h3>
          <div className="space-y-2">
            {citations.map((citation, index) => (
              <a
                key={citation.chunk_id}
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-xs hover:bg-gray-100 p-2 rounded transition-colors"
              >
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 font-bold text-primary-600">
                    [{index + 1}]
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-900 line-clamp-2">
                      {citation.title}
                    </p>
                    <p className="text-gray-500 mt-0.5">{citation.source}</p>
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about energy transition news..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !input.trim()}
              className="px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm font-medium"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
