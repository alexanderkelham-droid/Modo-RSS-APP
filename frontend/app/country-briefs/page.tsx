'use client'

import { useState } from 'react'
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function CountryBriefsPage() {
  const [selectedCountry, setSelectedCountry] = useState('US')
  const [loadingBrief, setLoadingBrief] = useState(false)
  const [brief, setBrief] = useState<any>(null)
  
  const { data: stories } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/articles/top-stories?country=${selectedCountry}&days=7&limit=20`,
    fetcher
  )

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
    <div className="h-full overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Country Intelligence</h1>
            <p className="text-gray-500 text-sm mt-0.5">
              Deep dive into regional energy transition developments.
            </p>
          </div>
          <select
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="US">United States</option>
            <option value="GB">United Kingdom</option>
            <option value="DE">Germany</option>
            <option value="CN">China</option>
            <option value="IN">India</option>
            <option value="AU">Australia</option>
          </select>
        </div>
      </div>

      <div className="p-5">
        {/* AI Daily Briefing */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-4">
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
            <p className="text-gray-500 text-sm">Click "Generate Brief" to create an AI-powered summary of recent {selectedCountry} energy developments.</p>
          )}
        </div>

        {/* Articles List */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          {stories?.items?.map((article: any) => (
            <a
              key={article.id}
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
            >
              <div className="h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg mb-3 flex items-center justify-center relative overflow-hidden">
                <img
                  src={article.image_url || '/source-logos/eia.jpg'}
                  alt={article.title}
                  className="w-full h-full object-cover rounded-lg"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement
                    if (target.src !== window.location.origin + '/source-logos/eia.jpg') {
                      target.src = '/source-logos/eia.jpg'
                    }
                  }}
                />
              </div>
              <div className="text-xs font-bold text-orange-500 uppercase mb-2">
                {article.source_name} •{' '}
                {Math.floor(
                  (new Date().getTime() - new Date(article.published_at).getTime()) /
                    (1000 * 60 * 60)
                )}h ago
              </div>
              <h3 className="text-sm font-bold text-gray-900 mb-2 line-clamp-2">
                {article.title}
              </h3>
              <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                {article.summary}
              </p>
              <div className="flex gap-1 flex-wrap">
                {article.country_codes?.slice(0, 2).map((code: string) => (
                  <span
                    key={code}
                    className="px-1.5 py-0.5 bg-blue-50 text-blue-600 rounded text-xs"
                  >
                    {code}
                  </span>
                ))}
                {article.topic_tags?.slice(0, 2).map((tag: string) => (
                  <span
                    key={tag}
                    className="px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                  >
                    {tag.replace(/_/g, ' ')}
                  </span>
                ))}
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
