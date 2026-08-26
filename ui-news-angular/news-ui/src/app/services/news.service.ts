// src/app/services/news.service.ts

import {
  HttpClient,
  HttpHeaders,
  HttpParams
} from '@angular/common/http';

import {
  Injectable,
  inject
} from '@angular/core';

import {
  Observable,
  map
} from 'rxjs';

import {
  ChatRequest,
  ChatResponse,
  ClearResponse,
  CurrentsArticle,
  CurrentsResponse,
  NewsArticle,
  NewsCategory,
  NewsResponse
} from '../models/news.models';

import {
  environment
} from '../../enviroment/enviroment';


@Injectable({
  providedIn: 'root'
})
export class NewsService {

  private readonly http =
    inject(HttpClient);

  private readonly latestEndpoint =
    'https://api.currentsapi.services/v1/latest-news';

  private readonly searchEndpoint =
    'https://api.currentsapi.services/v1/search';

  private readonly apiKey = environment.newsApiKey;

  private readonly chatApiUrl =
    environment.chatApiUrl;


  private getBrowserCountry(): string {

    const locale =
      navigator.language;

    try {

      const region =
        new Intl.Locale(locale).region;

      if (region) {
        return region.toUpperCase();
      }

    } catch (error) {

      console.warn(
        'Could not determine browser country:',
        error
      );

    }

    return 'US';
  }


  getHeadlines(
    options: {
      category?: NewsCategory;
      query?: string;
      page?: number;
      pageSize?: number;
      country?: string;
    } = {}
  ): Observable<NewsResponse> {

    const query =
      options.query?.trim();

    const country =
      options.country ??
      this.getBrowserCountry();

    const endpoint =
      query
        ? this.searchEndpoint
        : this.latestEndpoint;


    let params =
      new HttpParams()
        .set(
          'language',
          'en'
        )
        .set(
          'country',
          country
        )
        .set(
          'page_size',
          String(
            options.pageSize ?? 10
          )
        );


    if (options.page) {

      params = params.set(
        'page_number',
        String(options.page)
      );

    }


    if (
      options.category &&
      options.category !== 'top'
    ) {

      params = params.set(
        'category',
        options.category
      );

    }


    if (query) {

      params = params.set(
        'keywords',
        query
      );

    }


    const headers =
      new HttpHeaders({
        Authorization:
          `Bearer ${this.apiKey}`
      });


    return this.http
      .get<CurrentsResponse>(
        endpoint,
        {
          params,
          headers
        }
      )
      .pipe(
        map(response =>
          this.mapCurrentsResponse(
            response
          )
        )
      );

  }


  private mapCurrentsResponse(
    response: CurrentsResponse
  ): NewsResponse {

    const articles =
      (response.news ?? [])
        .map(article =>
          this.mapCurrentsArticle(
            article
          )
        );


    return {
      status: 'ok',
      totalResults:
        articles.length,
      articles
    };

  }


  private mapCurrentsArticle(
    article: CurrentsArticle
  ): NewsArticle {

    return {

      source: {
        id:
          article.id ??
          null,

        name:
          this.getSourceName(
            article.url
          )
      },


      author:
        article.author ??
        null,


      title:
        article.title ??
        'Untitled article',


      description:
        article.description ??
        null,


      url:
        article.url ??
        '',


      urlToImage:
        article.image ??
        null,


      publishedAt:
        article.published ??
        new Date().toISOString(),


      content:
        article.description ??
        null

    };

  }


  private getSourceName(
    url?: string
  ): string {

    if (!url) {
      return 'News source';
    }


    try {

      const hostname =
        new URL(url).hostname;


      return hostname
        .replace(
          /^www\./,
          ''
        );

    } catch {

      return 'News source';

    }

  }


  // ======================================================
  // CHAT - UNCHANGED
  // ======================================================

  sendMessage(
    message: string,
    threadId?: string
  ): Observable<ChatResponse> {

    const body: ChatRequest = {
      message
    };


    if (threadId) {
      body.thread_id =
        threadId;
    }


    return this.http.post<ChatResponse>(
      `${this.chatApiUrl}/chat`,
      body
    );

  }


  clearChat(
    threadId?: string
  ): Observable<ClearResponse> {

    const body =
      threadId
        ? {
            thread_id: threadId
          }
        : {};


    return this.http.post<ClearResponse>(
      `${this.chatApiUrl}/clear`,
      body
    );

  }

}