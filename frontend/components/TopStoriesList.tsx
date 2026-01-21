'use client'

import useSWR from 'swr'
import { fetchTopStories } from '@/lib/api'
import { TopStory } from '@/lib/types'
import { formatDistanceToNow } from 'date-fns'

interface TopStoriesListProps {
  country: string
  days: number
}

export default function TopStoriesList({ country, days }: TopStoriesListProps) {
  const { data, error, isLoading } = useSWR(
    country ? `top-stories-${country}-${days}` : null,
    () => fetchTopStories(country, days, 20),
    { refreshInterval: 60000 }
  )

  if (!country) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
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
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Select a country</h3>
          <p className="mt-1 text-sm text-gray-500">
            Choose a country from the sidebar to view top stories
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          Failed to load stories
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-4 space-y-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="h-6 bg-gray-200 rounded w-3/4 mb-2 animate-pulse" />
            <div className="h-4 bg-gray-200 rounded w-1/2 animate-pulse" />
          </div>
        ))}
      </div>
    )
  }

  if (!data || data.items.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center text-gray-500">
          <p className="text-sm">No stories found for this country</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto custom-scrollbar">
      <div className="p-4 space-y-3">
        {data.items.map((story: TopStory) => (
          <article
            key={story.id}
            className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <a
                  href={story.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block group"
                >
                  <h3 className="text-base font-semibold text-gray-900 group-hover:text-primary-600 transition-colors mb-2 line-clamp-2">
                    {story.title}
                  </h3>
                </a>
                
                <div className="flex items-center gap-3 text-xs text-gray-500 mb-3">
                  <span className="font-medium">{story.source_name}</span>
                  {story.published_at && (
                    <>
                      <span>•</span>
                      <span>
                        {formatDistanceToNow(new Date(story.published_at), {
                          addSuffix: true,
                        })}
                      </span>
                    </>
                  )}
                </div>

                {story.summary && (
                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                    {story.summary}
                  </p>
                )}

                {/* Tags */}
                <div className="flex flex-wrap gap-2">
                  {story.topic_tags?.map((tag) => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {tag.replace(/_/g, ' ')}
                    </span>
                  ))}
                  {story.country_codes?.map((code) => (
                    <span
                      key={code}
                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                    >
                      {code}
                    </span>
                  ))}
                </div>
              </div>

              {/* Score badge */}
              <div className="flex-shrink-0">
                <div className="text-center">
                  <div className="text-lg font-bold text-primary-600">
                    {story.score.toFixed(0)}
                  </div>
                  <div className="text-xs text-gray-500">score</div>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
