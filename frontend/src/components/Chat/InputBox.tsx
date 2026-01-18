import { FC, useState, useRef, useEffect } from 'react'

interface InputBoxProps {
  onSubmit: (text: string) => void
  loading?: boolean
  placeholder?: string
  disabled?: boolean
}

/**
 * InputBox Component
 * Text input with submit button for sending queries
 */
export const InputBox: FC<InputBoxProps> = ({
  onSubmit,
  loading = false,
  placeholder = 'Ask me about your finances...',
  disabled = false,
}) => {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        200
      )}px`
    }
  }, [text])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (text.trim() && !loading && !disabled) {
      onSubmit(text)
      setText('')
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto'
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.ctrlKey && !loading && !disabled) {
      handleSubmit(e as any)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 border-t border-gray-200 bg-white"
    >
      <div className="flex gap-3">
        {/* Text input */}
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={loading || disabled}
            rows={1}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <p className="text-xs text-gray-500 mt-1">
            Press Ctrl+Enter to send
          </p>
        </div>

        {/* Submit button */}
        <button
          type="submit"
          disabled={loading || disabled || !text.trim()}
          className="flex-shrink-0 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors font-medium h-fit"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
              Sending
            </span>
          ) : (
            'Send'
          )}
        </button>
      </div>
    </form>
  )
}

export default InputBox
