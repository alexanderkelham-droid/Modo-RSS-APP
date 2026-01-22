/**
 * Format a date string to a human-readable relative time
 * @param dateString - ISO date string
 * @returns Formatted time string (e.g., "2h ago", "3 days ago", "2 weeks ago", "1 month ago")
 */
export function formatTimeAgo(dateString: string): string {
  const now = new Date().getTime()
  const published = new Date(dateString).getTime()
  const diffMs = now - published
  
  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const weeks = Math.floor(days / 7)
  const months = Math.floor(days / 30)
  
  if (hours < 24) {
    return `${hours}h ago`
  } else if (days < 7) {
    return `${days} ${days === 1 ? 'day' : 'days'} ago`
  } else if (weeks < 4) {
    return `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ago`
  } else {
    return `${months} ${months === 1 ? 'month' : 'months'} ago`
  }
}

/**
 * Format a date to a standard format (e.g., "Jan 21, 2026")
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
