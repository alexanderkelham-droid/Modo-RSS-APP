'use client'

import { useState } from 'react'
import CountrySidebar from '@/components/CountrySidebar'
import FilterChips from '@/components/FilterChips'
import TopStoriesList from '@/components/TopStoriesList'
import ChatPanel from '@/components/ChatPanel'

export default function Home() {
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null)
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [selectedDateRange, setSelectedDateRange] = useState(7)

  const handleToggleTopic = (topic: string) => {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    )
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Countries */}
      <CountrySidebar
        selectedCountry={selectedCountry}
        onSelectCountry={setSelectedCountry}
        days={selectedDateRange}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Energy Transition Intelligence
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time news aggregation and analysis for the energy transition
          </p>
        </header>

        {/* Filter Chips */}
        <FilterChips
          selectedTopics={selectedTopics}
          onToggleTopic={handleToggleTopic}
          selectedDateRange={selectedDateRange}
          onSelectDateRange={setSelectedDateRange}
        />

        {/* Top Stories List */}
        <TopStoriesList country={selectedCountry || ''} days={selectedDateRange} />
      </div>

      {/* Right Panel - Chat */}
      <ChatPanel
        selectedCountry={selectedCountry}
        selectedTopics={selectedTopics}
        days={selectedDateRange}
      />
    </div>
  )
}
