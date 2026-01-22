'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { formatTimeAgo, formatDate } from '@/utils/time'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

const topics = [
  { id: 'all', label: 'All', color: 'bg-gray-900' },
  { id: 'renewables', label: 'Renewable Energy', color: 'bg-green-600' },
  { id: 'oil_gas', label: 'Oil & Gas', color: 'bg-gray-800' },
  { id: 'nuclear', label: 'Nuclear', color: 'bg-orange-600' },
  { id: 'ev_transport', label: 'Electric Vehicles', color: 'bg-blue-600' },
  { id: 'policy', label: 'Energy Policy', color: 'bg-purple-600' },
  { id: 'climate', label: 'Climate & Environment', color: 'bg-emerald-600' },
]

const topicColorMap: { [key: string]: string } = {
  'renewables_solar': 'bg-green-600',
  'renewables_wind': 'bg-green-600',
  'renewables': 'bg-green-600',
  'oil_gas': 'bg-gray-800',
  'nuclear': 'bg-orange-600',
  'ev_transport': 'bg-blue-600',
  'policy': 'bg-purple-600',
  'climate': 'bg-emerald-600',
  'hydrogen': 'bg-cyan-600',
  'storage_batteries': 'bg-blue-600',
  'power_grid': 'bg-indigo-600',
}

const topicLabelMap: { [key: string]: string } = {
  'renewables_solar': 'Renewable Energy',
  'renewables_wind': 'Renewable Energy',
  'renewables': 'Renewable Energy',
  'oil_gas': 'Oil & Gas',
  'nuclear': 'Nuclear',
  'ev_transport': 'Electric Vehicles',
  'policy': 'Energy Policy',
  'climate': 'Climate & Environment',
  'hydrogen': 'Renewable Energy',
  'storage_batteries': 'Electric Vehicles',
  'power_grid': 'Energy Policy',
}

export default function TopicsPage() {
  const [selectedTopic, setSelectedTopic] = useState('all')

  const { data } = useSWR(
    selectedTopic === 'all'
      ? `${process.env.NEXT_PUBLIC_API_URL}/articles?days=7&page_size=50`
      : `${process.env.NEXT_PUBLIC_API_URL}/articles?days=7&page_size=50`,
    fetcher
  )

  // Filter articles by selected topic
  const filteredArticles = data?.items?.filter((article: any) => {
    if (selectedTopic === 'all') return true
    
    // Check if any topic tag matches the selected topic or its category
    return article.topic_tags?.some((tag: string) => {
      if (selectedTopic === 'renewables') {
        return tag.includes('renewables') || tag.includes('solar') || tag.includes('wind')
      }
      return tag.includes(selectedTopic)
    })
  })

  const getTopicColor = (tags: string[]) => {
    if (!tags || tags.length === 0) return 'bg-gray-600'
    const firstTag = tags[0]
    return topicColorMap[firstTag] || 'bg-gray-600'
  }

  const getTopicLabel = (tags: string[]) => {
    if (!tags || tags.length === 0) return 'Energy'
    const firstTag = tags[0]
    return topicLabelMap[firstTag] || firstTag.replace(/_/g, ' ')
  }

  return (
    <div className="h-full overflow-auto bg-gray-50">
      {/* Topic Filter Bar */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center gap-3">
          {topics.map((topic) => (
            <button
              key={topic.id}
              onClick={() => setSelectedTopic(topic.id)}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
                selectedTopic === topic.id
                  ? 'bg-gray-900 text-white shadow-md'
                  : 'bg-white text-gray-700 border border-gray-300 hover:border-gray-400 hover:shadow-sm'
              }`}
            >
              {topic.label}
            </button>
          ))}
        </div>
      </div>

      {/* Articles Section */}
      <div className="px-8 py-6">
        {/* Article Count */}
        <p className="text-sm text-gray-600 mb-6">
          Showing {filteredArticles?.length || 0} articles
        </p>

        {/* Articles Grid - 3 columns */}
        <div className="grid grid-cols-3 gap-6">
          {filteredArticles?.map((article: any) => (
            <div
              key={article.id}
              className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg transition-shadow"
            >
              {/* Image with Topic Badge */}
              <div className="relative h-56 bg-gradient-to-br from-gray-100 to-gray-200">
                <img
                  src={article.image_url || '/source-logos/eia.jpg'}
                  alt={article.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    if (target.src !== window.location.origin + '/source-logos/eia.jpg') {
                      target.src = '/source-logos/eia.jpg'
                    }
                  }}
                />
                {/* Topic Badge Overlay */}
                {article.topic_tags && article.topic_tags.length > 0 && (
                  <div className="absolute top-4 left-4">
                    <span className={`${getTopicColor(article.topic_tags)} text-white text-xs font-medium px-3 py-1.5 rounded-full shadow-md`}>
                      {getTopicLabel(article.topic_tags)}
                    </span>
                  </div>
                )}
              </div>

              {/* Content */}
              <div className="p-5">
                {/* Title */}
                <h3 className="text-lg font-bold text-gray-900 mb-3 line-clamp-2 leading-tight">
                  {article.title}
                </h3>

                {/* Source and Date */}
                <div className="flex items-center gap-2 text-sm text-gray-500 mb-3">
                  <span className="font-medium">{article.source_name || 'News Source'}</span>
                  <span>•</span>
                  <span>{formatDate(article.published_at)}</span>
                </div>

                {/* Summary */}
                <p className="text-sm text-gray-600 line-clamp-3 mb-4 leading-relaxed">
                  {article.summary || article.raw_summary || 'No summary available'}
                </p>

                {/* Read More Button */}
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 text-sm font-medium text-gray-900 hover:text-blue-600 transition-colors"
                >
                  Read More
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {(!filteredArticles || filteredArticles.length === 0) && (
          <div className="text-center py-12">
            <p className="text-gray-500">No articles found for this topic.</p>
          </div>
        )}
      </div>
    </div>
  )
}
