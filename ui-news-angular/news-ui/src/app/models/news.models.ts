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
  | 'business'
  | 'entertainment'
  | 'health'
  | 'science'
  | 'sports'
  | 'technology'
  | 'world'
  | 'politics'
  | 'top';

export interface CategoryOption {
  label: string;
  value: NewsCategory;
}


// ======================================================
// CURRENTS API
// ======================================================

export interface CurrentsArticle {
  id?: string;
  title?: string;
  description?: string;
  url?: string;
  author?: string;
  image?: string;
  language?: string;
  category?: string[];
  published?: string;
}

export interface CurrentsResponse {
  status: string;
  news?: CurrentsArticle[];
  page?: number;
}


// ======================================================
// CHAT
// ======================================================

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