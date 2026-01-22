'use client'

export default function SettingsPage() {
  return (
    <div className="h-full overflow-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 text-sm mt-0.5">
            Manage application settings and preferences.
          </p>
        </div>
      </div>

      {/* Settings Content */}
      <div className="p-6 max-w-4xl">
        {/* General Settings */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-4">
          <h2 className="text-lg font-bold text-gray-900 mb-4">General</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                API URL
              </label>
              <input
                type="text"
                value={process.env.NEXT_PUBLIC_API_URL}
                disabled
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500 text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">Backend API endpoint (read-only)</p>
            </div>
          </div>
        </div>

        {/* Ingestion Settings */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-4">
          <h2 className="text-lg font-bold text-gray-900 mb-4">RSS Ingestion</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Ingestion Frequency
              </label>
              <p className="text-sm text-gray-600">
                Articles are fetched from RSS feeds when you manually trigger ingestion.
              </p>
            </div>
            <div>
              <a
                href={`${process.env.NEXT_PUBLIC_API_URL}/docs`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium"
              >
                Trigger Ingestion
              </a>
            </div>
          </div>
        </div>

        {/* AI Settings */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">AI Features</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Brief Generation
              </label>
              <p className="text-sm text-gray-600">
                AI-generated country briefs are cached for 24 hours to minimize API costs.
              </p>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">OpenAI Integration</p>
                <p className="text-xs text-gray-500">Configured via environment variables</p>
              </div>
              <span className="inline-flex px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                Active
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
