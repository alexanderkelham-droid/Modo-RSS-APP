'use client'

import { useState } from 'react'
import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function CountryBriefsPage() {
  const [selectedCountry, setSelectedCountry] = useState('US')
  
  const { data: stories } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/articles/top-stories?country=${selectedCountry}&days=7&limit=20`,
    fetcher
  )

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
        <div className="grid grid-cols-2 gap-4">
          {/* AI Daily Briefing */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h2 className="font-bold text-gray-900 text-sm mb-3">AI Daily Briefing</h2>
            <p className="text-gray-500 text-sm">No briefing generated for today.</p>
          </div>

          {/* Regional Coverage */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <h2 className="font-bold text-gray-900 text-sm mb-3">Regional Coverage</h2>
            <div className="grid grid-cols-2 gap-6">
              {stories?.items?.slice(0, 2).map((article: any) => (
                <div key={article.id} className="space-y-3">
                  <div className="h-32 bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg flex items-center justify-center">
                    <span className="text-5xl">⚡</span>
                  </div>
                  <div>
                    <div className="text-xs font-bold text-orange-500 uppercase mb-1">
                      {article.source_name}
                    </div>
                    <h3 className="text-sm font-bold text-gray-900 line-clamp-2">
                      {article.title}
                    </h3>
                    <div className="flex gap-2 mt-2">
                      {article.country_codes?.map((code: string) => (
                        <span
                          key={code}
                          className="px-2 py-1 bg-gray-100 rounded text-xs"
                        >
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Regional Data */}
        <div className="mt-4 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h2 className="text-blue-600 font-bold text-sm mb-3">Regional Data</h2>
          <p className="text-gray-500 text-xs mb-4">
            Comprehensive datasets for {selectedCountry}.
          </p>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <div className="text-xs text-gray-600 mb-1">Renewable Share</div>
              <div className="text-xl font-bold">24.5%</div>
            </div>
            <div>
              <div className="text-xs text-gray-600 mb-1">Capacity Added (YTD)</div>
              <div className="text-xl font-bold">12 GW</div>
            </div>
            <div>
              <div className="text-xs text-gray-600 mb-1">Active Projects</div>
              <div className="text-xl font-bold">142</div>
            </div>
          </div>
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
