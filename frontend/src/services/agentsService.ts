import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Citation {
  title: string;
  source_url: string;
  category: string;
}

interface AgentResponse {
  session_id: string;
  message: string;
  citations: Citation[];
  structured_data?: Record<string, any>;
  timestamp: string;
  metadata: {
    agent: string;
    tools_used: string[];
  };
  // LangGraph execution metrics
  confidence?: number;
  intent?: string;
  agents_used?: string[];
  execution_times?: Record<string, number>;
  total_time_ms?: number;
}

interface Holding {
  ticker: string;
  quantity: number;
  current_price: number;
  cost_basis?: number;
}

class AgentsService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * Analyze investment portfolio
   */
  async analyzePortfolio(
    holdings: Holding[],
    sessionId?: string,
    analysisType: string = 'full'
  ): Promise<AgentResponse> {
    try {
      const response = await this.client.post<AgentResponse>(
        '/api/agents/portfolio-analysis',
        {
          holdings,
          session_id: sessionId,
          analysis_type: analysisType,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Portfolio analysis failed');
    }
  }

  /**
   * Analyze market data
   */
  async analyzeMarket(
    tickers: string[],
    sessionId?: string,
    analysisType: string = 'quote'
  ): Promise<AgentResponse> {
    try {
      const response = await this.client.post<AgentResponse>(
        '/api/agents/market-analysis',
        {
          tickers,
          session_id: sessionId,
          analysis_type: analysisType,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Market analysis failed');
    }
  }

  /**
   * Plan financial goals
   */
  async planGoals(
    currentValue: number,
    goalAmount: number,
    timeHorizonYears: number,
    sessionId?: string,
    riskAppetite: string = 'moderate',
    currentReturn: number = 6.0
  ): Promise<AgentResponse> {
    try {
      const response = await this.client.post<AgentResponse>(
        '/api/agents/goal-planning',
        {
          current_value: currentValue,
          goal_amount: goalAmount,
          time_horizon_years: timeHorizonYears,
          risk_appetite: riskAppetite,
          current_return: currentReturn,
          session_id: sessionId,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Goal planning failed');
    }
  }

  /**
   * Answer tax questions
   */
  async answerTaxQuestion(
    question: string,
    sessionId?: string,
    categoryFilter?: string
  ): Promise<AgentResponse> {
    try {
      const response = await this.client.post<AgentResponse>(
        '/api/agents/tax-education',
        {
          question,
          session_id: sessionId,
          category_filter: categoryFilter,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'Tax question failed');
    }
  }

  /**
   * Synthesize news and market sentiment
   */
  async synthesizeNews(
    tickers?: string[],
    sessionId?: string,
    sentimentFocus?: string
  ): Promise<AgentResponse> {
    try {
      const response = await this.client.post<AgentResponse>(
        '/api/agents/news-synthesis',
        {
          tickers,
          session_id: sessionId,
          sentiment_focus: sentimentFocus,
        }
      );
      return response.data;
    } catch (error) {
      throw this.handleError(error, 'News synthesis failed');
    }
  }

  private handleError(error: any, defaultMsg: string): Error {
    if (axios.isAxiosError(error)) {
      return new Error(
        error.response?.data?.detail ||
        error.message ||
        defaultMsg
      );
    }
    return error instanceof Error ? error : new Error(defaultMsg);
  }
}

export const agentsService = new AgentsService();

export type { AgentResponse, Citation, Holding };
