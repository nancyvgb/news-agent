import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
  ChatRequest,
  ChatResponse,
  ClearResponse,
  NewsCategory,
  NewsResponse
} from '../models/news.models';

import { environment } from '../../enviroment/enviroment';

@Injectable({ providedIn: 'root' })
export class NewsService {
  private readonly http = inject(HttpClient);

  private readonly endpoint = 'https://newsapi.org/v2/top-headlines';
  private readonly chatApiUrl = environment.chatApiUrl;

  /**
   * Get the country from the browser's locale.
   *
   * Example:
   * en-US -> us
   * es-CO -> co
   * es-MX -> mx
   *
   * Falls back to Colombia if the browser doesn't
   * provide a region.
   */
  private getBrowserCountry(): string {
    const locale = navigator.language;

    try {
      const region = new Intl.Locale(locale).region;

      if (region) {
        return region.toLowerCase();
      }
    } catch (error) {
      console.warn('Could not determine browser country:', error);
    }

    // Fallback
    return 'us';
  }

  getHeadlines(options: {
    category?: NewsCategory;
    query?: string;
    page?: number;
    pageSize?: number;
    country?: string;
  } = {}): Observable<NewsResponse> {

    const country = options.country ?? this.getBrowserCountry();

    let params = new HttpParams()
      .set('country', country)
      .set('page', String(options.page ?? 1))
      .set('pageSize', String(options.pageSize ?? 12));

    if (options.category) {
      params = params.set('category', options.category);
    }

    if (options.query?.trim()) {
      params = params.set('q', options.query.trim());
    }

    params = params.set(
      'apiKey',
      'c055f9f4ccd64e53bb193e94fe9bfa2c'
    );

    return this.http.get<NewsResponse>(
      this.endpoint,
      { params }
    );
  }

  sendMessage(
    message: string,
    threadId?: string
  ): Observable<ChatResponse> {

    const body: ChatRequest = {
      message
    };

    if (threadId) {
      body.thread_id = threadId;
    }

    return this.http.post<ChatResponse>(
      `${this.chatApiUrl}/chat`,
      body
    );
  }

  clearChat(threadId?: string): Observable<ClearResponse> {

    const body = threadId
      ? { thread_id: threadId }
      : {};

    return this.http.post<ClearResponse>(
      `${this.chatApiUrl}/clear`,
      body
    );
  }
}