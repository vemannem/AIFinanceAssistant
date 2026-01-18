import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface Citation {
  title: string;
  source_url: string;
  category: string;
}

interface AgentExecutionResult {
  agent_name: string;
  answer_text: string;
  structured_data?: Record<string, any>;
  citations: Citation[];
}

interface OrchestrationRequest {
  message: string;
  session_id?: string;
  conversation_history?: ChatMessage[];
}

interface OrchestrationResponse {
  session_id: string;
  message: string;
  citations: Citation[];
  timestamp: string;
  confidence?: number;
  intent?: string;
  agents_used?: string[];
  execution_times?: Record<string, number>;
  total_time_ms?: number;
  metadata: {
    agent: string;
    tools_used: string[];
    chunks_retrieved?: number;
  };
}

class OrchestrationService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Send message to multi-agent orchestration system
   */
  async sendMessage(
    message: string,
    sessionId?: string,
    conversationHistory?: ChatMessage[]
  ): Promise<OrchestrationResponse> {
    try {
      const request: OrchestrationRequest = {
        message,
        session_id: sessionId,
        conversation_history: conversationHistory,
      };

      const response = await this.client.post<OrchestrationResponse>(
        '/api/chat/orchestration',
        request
      );

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail ||
          error.message ||
          'Failed to process query with agents'
        );
      }
      throw error;
    }
  }

  /**
   * Extract portfolio data from agent results
   */
  getPortfolioAnalysis(agentResults: AgentExecutionResult[]) {
    const portfolioResult = agentResults.find(
      (r) => r.agent_name.toLowerCase().includes('portfolio')
    );
    return portfolioResult?.structured_data;
  }

  /**
   * Extract market data from agent results
   */
  getMarketAnalysis(agentResults: AgentExecutionResult[]) {
    const marketResult = agentResults.find(
      (r) => r.agent_name.toLowerCase().includes('market')
    );
    return marketResult?.structured_data;
  }

  /**
   * Extract goal planning data from agent results
   */
  getGoalPlanning(agentResults: AgentExecutionResult[]) {
    const goalResult = agentResults.find(
      (r) => r.agent_name.toLowerCase().includes('goal')
    );
    return goalResult?.structured_data;
  }

  /**
   * Extract tax education data from agent results
   */
  getTaxEducation(agentResults: AgentExecutionResult[]) {
    const taxResult = agentResults.find(
      (r) => r.agent_name.toLowerCase().includes('tax')
    );
    return taxResult?.structured_data;
  }

  /**
   * Extract news synthesis data from agent results
   */
  getNewsSynthesis(agentResults: AgentExecutionResult[]) {
    const newsResult = agentResults.find(
      (r) => r.agent_name.toLowerCase().includes('news')
    );
    return newsResult?.structured_data;
  }
}

export const orchestrationService = new OrchestrationService();

export type {
  OrchestrationRequest,
  OrchestrationResponse,
  AgentExecutionResult,
  Citation,
  ChatMessage,
};
