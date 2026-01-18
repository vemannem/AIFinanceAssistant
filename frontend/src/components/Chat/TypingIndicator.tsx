import { FC } from 'react'

interface TypingIndicatorProps {
  text?: string
}

/**
 * TypingIndicator Component
 * Shows animated dots while waiting for assistant response
 */
export const TypingIndicator: FC<TypingIndicatorProps> = ({
  text = 'AI is thinking',
}) => {
  return (
    <div className="flex items-center gap-2 py-2">
      <span className="text-sm text-gray-600">{text}</span>
      <div className="flex gap-1">
        <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
        <span
          className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"
          style={{ animationDelay: '0.1s' }}
        ></span>
        <span
          className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"
          style={{ animationDelay: '0.2s' }}
        ></span>
      </div>
    </div>
  )
}

export default TypingIndicator
