'use client'

import useSWR from 'swr'
import { fetchCountries } from '@/lib/api'
import { CountryStats } from '@/lib/types'

interface CountrySidebarProps {
  selectedCountry: string | null
  onSelectCountry: (country: string) => void
  days: number
}

export default function CountrySidebar({
  selectedCountry,
  onSelectCountry,
  days,
}: CountrySidebarProps) {
  const { data, error, isLoading } = useSWR(
    `countries-${days}`,
    () => fetchCountries(days),
    { refreshInterval: 60000 } // Refresh every minute
  )

  if (error) {
    return (
      <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Countries</h2>
        <div className="text-red-600 text-sm">Failed to load countries</div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="w-64 bg-gray-50 border-r border-gray-200 p-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-900">Countries</h2>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col h-screen">
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Countries</h2>
        {data && (
          <p className="text-xs text-gray-500 mt-1">
            {data.total_articles} articles in last {days} days
          </p>
        )}
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
        <div className="space-y-1">
          {data?.items.map((country: CountryStats) => (
            <button
              key={country.country_code}
              onClick={() => onSelectCountry(country.country_code)}
              className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                selectedCountry === country.country_code
                  ? 'bg-primary-500 text-white'
                  : 'hover:bg-gray-200 text-gray-700'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className="font-medium text-sm">{country.country_name}</span>
                <span
                  className={`text-xs px-2 py-0.5 rounded-full ${
                    selectedCountry === country.country_code
                      ? 'bg-white/20 text-white'
                      : 'bg-gray-300 text-gray-700'
                  }`}
                >
                  {country.article_count}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
