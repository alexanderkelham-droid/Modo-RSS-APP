'use client'

import { useState } from 'react'
import useSWR from 'swr'
import Image from 'next/image'
import { formatTimeAgo } from '@/utils/time'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function Dashboard() {
  const [days, setDays] = useState(7)
  const [selectedCountry, setSelectedCountry] = useState('US')
  const [loadingBrief, setLoadingBrief] = useState(false)
  const [brief, setBrief] = useState<any>(null)

  const { data: stories } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/articles/top-stories?country=${selectedCountry}&days=${days}&limit=1`,
    fetcher,
    { refreshInterval: 30000 }
  )

  const { data: updates } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/articles?days=${days}&page_size=3`,
    fetcher
  )

  const { data: countries } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/countries?days=${days}`,
    fetcher
  )

  const featuredStory = stories?.items?.[0]

  const generateBrief = async () => {
    setLoadingBrief(true)
    setBrief(null)
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/briefs/latest?country_code=${selectedCountry}`
      )
      const data = await response.json()
      setBrief(data)
    } catch (error) {
      console.error('Failed to generate brief:', error)
      setBrief({ content: null, error: 'Failed to generate brief' })
    } finally {
      setLoadingBrief(false)
    }
  }

  return (
    <div className="h-full overflow-auto bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-8 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Market Overview</h1>
            <p className="text-gray-500 text-sm mt-0.5">
              Real-time insights on the global energy transition.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="US">United States</option>
              <option value="GB">United Kingdom</option>
              <option value="DE">Germany</option>
              <option value="CN">China</option>
              <option value="IN">India</option>
              <option value="AU">Australia</option>
              <option value="IT">Italy</option>
              <option value="PL">Poland</option>
              <option value="ES">Spain</option>
              <option value="NO">Norway</option>
              <option value="JP">Japan</option>
              <option value="KR">South Korea</option>
              <option value="CA">Canada</option>
            </select>
            <select
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
            </select>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-8">
        {/* AI Daily Briefing */}
        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-gray-900 text-lg">AI Daily Briefing</h2>
            <button
              onClick={generateBrief}
              disabled={loadingBrief}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium"
            >
              {loadingBrief ? 'Generating...' : 'Generate Brief'}
            </button>
          </div>
          
          {loadingBrief ? (
            <div className="text-center py-8">
              <div className="animate-pulse text-gray-500">
                Analyzing {selectedCountry} articles with AI... (10-15 seconds)
              </div>
            </div>
          ) : brief?.content ? (
            <div className="prose prose-sm max-w-none">
              <div className="text-gray-600 whitespace-pre-wrap">{brief.content}</div>
              <div className="mt-4 text-xs text-gray-400">
                Generated: {brief.generated_at || 'Just now'} • {brief.article_count || 0} articles analyzed
              </div>
            </div>
          ) : brief?.error ? (
            <div className="text-red-600 text-sm">
              {brief.error}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">Click \"Generate Brief\" to create an AI-powered summary of recent {selectedCountry} energy developments.</p>
          )}
        </div>
        
        <div className="grid grid-cols-3 gap-6">
          {/* Featured Article */}
          <div className="col-span-2">
            {featuredStory ? (
              <a
                href={featuredStory.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block bg-white rounded-xl shadow-sm overflow-hidden h-full hover:shadow-lg transition-shadow"
              >
                <div className="h-64 bg-gradient-to-br from-gray-100 to-gray-200 relative overflow-hidden">
                  <img
                    src={featuredStory.image_url || '/source-logos/eia.jpg'}
                    alt={featuredStory.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      if (target.src !== window.location.origin + '/source-logos/eia.jpg') {
                        target.src = '/source-logos/eia.jpg'
                      }
                    }}
                  />
                </div>
                <div className="p-5">
                  <div className="flex items-center gap-2 text-xs mb-3">
                    <span className="font-bold text-orange-500 uppercase">
                      {featuredStory.source_name}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="text-gray-500">
                      {formatTimeAgo(featuredStory.published_at)}
                    </span>
                  </div>
                  <h2 className="text-xl font-bold text-gray-900 mb-3 leading-tight">
                    {featuredStory.title}
                  </h2>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {featuredStory.summary}
                  </p>
                </div>
              </a>
            ) : (
              <div className="bg-gray-100 rounded-lg h-full flex items-center justify-center">
                <div className="text-gray-400 text-sm">Loading...</div>
              </div>
            )}
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Activity Trend */}
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <h3 className="font-bold text-gray-900 text-sm mb-3">Activity Trend</h3>
              <div className="h-32 bg-gradient-to-br from-blue-100 to-blue-200 rounded-lg flex items-end justify-center px-4 pb-4">
                <svg className="w-full h-20" viewBox="0 0 200 50">
                  <polyline
                    points="0,40 30,35 60,25 90,30 120,15 150,20 180,10 200,5"
                    fill="none"
                    stroke="#2563eb"
                    strokeWidth="2"
                  />
                  <polyline
                    points="0,40 30,35 60,25 90,30 120,15 150,20 180,10 200,5 200,50 0,50"
                    fill="rgba(37, 99, 235, 0.2)"
                  />
                </svg>
              </div>
              <div className="mt-4 flex justify-between text-xs text-gray-500">
                <span>Tue</span>
                <span>Wed</span>
                <span>Thu</span>
                <span>Fri</span>
                <span>Sat</span>
                <span>Sun</span>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-white rounded-lg shadow-sm p-3 border border-gray-200">
                <div className="text-xs text-gray-500 uppercase mb-1">Articles</div>
                <div className="text-2xl font-bold text-gray-900">
                  {updates?.total || 0}
                </div>
              </div>
              <div className="bg-white rounded-lg shadow-sm p-3 border border-gray-200">
                <div className="text-xs text-gray-500 uppercase mb-1">
                  Countries
                </div>
                <div className="text-2xl font-bold text-gray-900">{countries?.length || 0}</div>
              </div>
            </div>

            {/* Latest Updates */}
            <div className="bg-white rounded-lg shadow-sm p-4 border border-gray-200">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-gray-900 text-sm">Latest Updates</h3>
                <a href="/topics" className="text-blue-600 text-xs hover:underline">
                  View All
                </a>
              </div>
              <div className="space-y-3">
                {updates?.items?.slice(0, 3).map((item: any) => (
                  <a
                    key={item.id}
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex gap-3 group"
                  >
                    <div className="w-12 h-12 bg-gray-100 rounded flex-shrink-0 overflow-hidden relative">
                      {item.image_url ? (
                        <img
                          src={item.image_url}
                          alt=""
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement
                            target.style.display = 'none'
                          }}
                        />
                      ) : (
                        <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600">
                        {item.title}
                      </h4>
                      <p className="text-xs text-gray-500 mt-1">
                        {item.topic_tags?.[0]?.replace(/_/g, ' ') || 'General'} • {formatTimeAgo(item.published_at)}
                      </p>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
