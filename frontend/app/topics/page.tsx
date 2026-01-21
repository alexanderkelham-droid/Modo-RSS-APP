'use client'

import { useState } from 'react'
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

const topics = [
  { id: 'all', label: 'All Topics' },
  { id: 'renewables_solar', label: 'Solar' },
  { id: 'renewables_wind', label: 'Wind' },
  { id: 'hydrogen', label: 'Hydrogen' },
  { id: 'storage_batteries', label: 'Battery' },
  { id: 'nuclear', label: 'Nuclear' },
  { id: 'power_grid', label: 'Grid' },
]

export default function TopicsPage() {
  const [selectedTopic, setSelectedTopic] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data } = useSWR(
    selectedTopic === 'all'
      ? `${process.env.NEXT_PUBLIC_API_URL}/articles?days=7&page_size=20`
      : `${process.env.NEXT_PUBLIC_API_URL}/articles?days=7&topic=${selectedTopic}&page_size=20`,
    fetcher
  )

  const filteredArticles = data?.items?.filter((article: any) =>
    searchQuery
      ? article.title.toLowerCase().includes(searchQuery.toLowerCase())
      : true
  )

  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Explore Topics</h1>
        <p className="text-gray-500 text-sm mt-0.5">
          Filter news by technology sector or search specific keywords.
        </p>

        {/* Search Bar */}
        <div className="mt-4 max-w-xl mx-auto">
          <input
            type="text"
            placeholder="Search keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Topic Pills */}
        <div className="flex flex-wrap justify-center gap-2 mt-4">
          {topics.map((topic) => (
            <button
              key={topic.id}
              onClick={() => setSelectedTopic(topic.id)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                selectedTopic === topic.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:border-gray-400'
              }`}
            >
              {topic.label}
            </button>
          ))}
        </div>
      </div>

      {/* Articles Grid */}
      <div className="p-5">
        <div className="grid grid-cols-4 gap-4">
          {filteredArticles?.map((article: any) => (
            <a
              key={article.id}
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
            >
              {/* Image Placeholder */}
              <div className="h-36 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative overflow-hidden">
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
              </div>

              {/* Content */}
              <div className="p-3">
                <div className="flex items-center gap-2 text-xs mb-2">
                  <span className="font-bold text-orange-500 uppercase truncate">
                    {article.source_name || 'NEWS SOURCE'}
                  </span>
                  <span className="text-gray-400">•</span>
                  <span className="text-gray-500">
                    {Math.floor(
                      (new Date().getTime() -
                        new Date(article.published_at).getTime()) /
                        (1000 * 60 * 60)
                    )}h
                  </span>
                </div>

                <h3 className="text-sm font-bold text-gray-900 mb-2 line-clamp-2 leading-tight">
                  {article.title}
                </h3>

                <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                  {article.summary || 'No summary available'}
                </p>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {article.country_codes?.slice(0, 2).map((code: string) => (
                    <span
                      key={code}
                      className="px-1.5 py-0.5 bg-blue-50 text-blue-600 text-xs rounded"
                    >
                      {code}
                    </span>
                  ))}
                  {article.topic_tags?.slice(0, 2).map((tag: string) => (
                    <span
                      key={tag}
                      className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
                    >
                      {tag.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
