// src/app/models/news.models.ts
export interface NewsSource {
  id: string | null;
  name: string;
}

export interface NewsArticle {
  source: NewsSource;
  author: string | null;
  title: string;
  description: string | null;
  url: string;
  urlToImage: string | null;
  publishedAt: string;
  content: string | null;
}

export interface NewsResponse {
  status: 'ok' | 'error';
  totalResults: number;
  articles: NewsArticle[];
  code?: string;
  message?: string;
}

export type NewsCategory =
  | 'general'
  | 'business'
  | 'technology'
  | 'science'
  | 'health'
  | 'sports'
  | 'entertainment';

export interface CategoryOption { label: string; value: NewsCategory; }

// Chat models (matches FastAPI backend)
export interface ChatMessage {
  type: 'human' | 'ai';
  content: string;
}

export interface ChatRequest {
  message: string;
  thread_id?: string;
}

export interface ChatResponse {
  messages: ChatMessage[];
}

export interface ClearResponse {
  status: string;
  thread_id: string;
}