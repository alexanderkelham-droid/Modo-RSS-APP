'use client'

import useSWR from 'swr'

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function FeedManagerPage() {
  const { data: sources } = useSWR(
    `${process.env.NEXT_PUBLIC_API_URL}/sources`,
    fetcher
  )

  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Source Management</h1>
            <p className="text-gray-500 text-sm mt-0.5">
              Manage RSS feeds and configure ingestion settings.
            </p>
          </div>
          <button className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium">
            + Add Source
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="p-5">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Name
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  URL
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Status
                </th>
                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                  Last Sync
                </th>
                <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sources?.map((source: any) => (
                <tr key={source.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {source.name}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 font-mono truncate max-w-xs">
                    {source.rss_url}
                  </td>
                  <td className="px-4 py-3 text-sm">
                    {source.enabled ? (
                      <span className="inline-flex px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 rounded">
                        Active
                      </span>
                    ) : (
                      <span className="inline-flex px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-800 rounded">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500">
                    {source.created_at
                      ? new Date(source.created_at).toLocaleDateString()
                      : 'Never'}
                  </td>
                  <td className="px-4 py-3 text-sm text-right">
                    <button className="text-blue-600 hover:text-blue-800 mr-3 text-xs font-medium">
                      Refresh
                    </button>
                    <button className="text-red-600 hover:text-red-800 text-xs font-medium">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
