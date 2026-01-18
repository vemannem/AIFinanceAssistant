// Global type definitions

export interface ExecutionMetrics {
  confidence?: number;
  intent?: string;
  agentsUsed?: string[];
  executionTimes?: Record<string, number>;
  totalTimeMs?: number;
  metadata?: Record<string, any>;
}

export interface Message {
  id: string;
  text: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  citations?: Citation[];
  sections?: ResponseSection[];
  agentResults?: AgentExecutionResult[];
  execution?: ExecutionMetrics;
  metadata?: {
    workflow_state: string;
    confidence_score: number;
    agents_count: number;
    error_messages: string[];
  };
}

export interface AgentExecutionResult {
  agent_name: string;
  answer_text: string;
  structured_data?: Record<string, any>;
  citations: Citation[];
}

export interface Citation {
  id: string;
  title: string;
  url: string;
  source: string;
  category?: string;
}

export interface ResponseSection {
  title: string;
  content: string;
  type: 'text' | 'list' | 'table' | 'chart';
}

export interface ConversationSummary {
  sessionId: string;
  summary: string;
  topics: string[];
  timestamp: Date;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: Record<string, unknown>;
}

export interface Holding {
  ticker: string;
  quantity: number;
  currentPrice: number;
  costBasis?: number;
  value?: number;
  allocation?: number;
}

export interface Portfolio {
  holdings: Holding[];
  totalValue: number;
  allocation: Record<string, number>;
  diversificationScore: number;
  riskScore: number;
}
