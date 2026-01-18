import { FC } from 'react'
import { Citation } from '../../types'

interface CitationsListProps {
  citations?: Citation[]
}

/**
 * CitationsList Component
 * Displays references and sources for the response
 */
export const CitationsList: FC<CitationsListProps> = ({ citations = [] }) => {
  if (!citations || citations.length === 0) {
    return null
  }

  return (
    <div className="mt-4 pt-4 border-t border-gray-200">
      <p className="text-sm font-semibold text-gray-700 mb-2">Sources:</p>
      <div className="space-y-2">
        {citations.map((citation, index) => (
          <div
            key={citation.id}
            className="text-sm flex gap-2 items-start p-2 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
          >
            <span className="text-gray-400 font-semibold flex-shrink-0">
              [{index + 1}]
            </span>
            <div className="min-w-0">
              <a
                href={citation.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 hover:underline font-medium break-words"
              >
                {citation.title}
              </a>
              {citation.category && (
                <span className="text-xs text-gray-500 ml-2">
                  ({citation.category})
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default CitationsList
