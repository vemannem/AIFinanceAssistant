import { useState, useCallback } from 'react';
import { orchestrationService, OrchestrationResponse } from '@/services/orchestrationService';

interface UseOrchestrationOptions {
  onSuccess?: (response: OrchestrationResponse) => void;
  onError?: (error: Error) => void;
}

export function useOrchestration(options?: UseOrchestrationOptions) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [response, setResponse] = useState<OrchestrationResponse | null>(null);

  const sendMessage = useCallback(
    async (
      message: string,
      sessionId?: string,
      conversationHistory?: Array<{ role: 'user' | 'assistant'; content: string }>
    ) => {
      try {
        setLoading(true);
        setError(null);

        const result = await orchestrationService.sendMessage(
          message,
          sessionId,
          conversationHistory
        );

        setResponse(result);
        options?.onSuccess?.(result);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setError(error);
        options?.onError?.(error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [options]
  );

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResponse(null);
  }, []);

  return {
    sendMessage,
    loading,
    error,
    response,
    clearError,
    reset,
  };
}
