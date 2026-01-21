'use client'

import { TOPICS, DATE_RANGES } from '@/lib/types'

interface FilterChipsProps {
  selectedTopics: string[]
  onToggleTopic: (topic: string) => void
  selectedDateRange: number
  onSelectDateRange: (days: number) => void
}

export default function FilterChips({
  selectedTopics,
  onToggleTopic,
  selectedDateRange,
  onSelectDateRange,
}: FilterChipsProps) {
  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="space-y-3">
        {/* Date Range Filter */}
        <div>
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 block">
            Time Range
          </label>
          <div className="flex flex-wrap gap-2">
            {DATE_RANGES.map((range) => (
              <button
                key={range.id}
                onClick={() => onSelectDateRange(range.days)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  selectedDateRange === range.days
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Topic Filter */}
        <div>
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2 block">
            Topics
          </label>
          <div className="flex flex-wrap gap-2">
            {TOPICS.map((topic) => (
              <button
                key={topic.id}
                onClick={() => onToggleTopic(topic.id)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  selectedTopics.includes(topic.id)
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {topic.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
