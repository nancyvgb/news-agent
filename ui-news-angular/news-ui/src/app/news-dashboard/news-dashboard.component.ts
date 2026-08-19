// src/app/pages/news-dashboard/news-dashboard.component.ts
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  signal
} from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { finalize } from 'rxjs';


import { NewsService } from '../services/news.service';
import { CategoryOption, NewsArticle, NewsCategory } from '../models/news.models';
import { FormsModule } from '@angular/forms';
import { NewsAgentComponent } from '../components/news-agent/news-agent.component';


@Component({
  selector: 'app-news-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    DatePipe,
    FormsModule, // Add FormsModule here,
    NewsAgentComponent
  ],
  templateUrl: './news-dashboard.component.html',
  styleUrl: './news-dashboard.component.scss',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class NewsDashboardComponent {
  private readonly newsService = inject(NewsService);

  readonly categories: CategoryOption[] = [
    { label: 'News', value: 'general' },
    { label: 'Economics', value: 'business' },
    { label: 'Politics', value: 'general' },
    { label: 'Business', value: 'business' },
    { label: 'Entertainment', value: 'entertainment' },
    { label: 'Technology', value: 'technology' },
    { label: 'Science', value: 'science' },
    { label: 'Sports', value: 'sports' }
  ];

  readonly articles = signal<NewsArticle[]>([]);
  readonly loading = signal(false);
  readonly error = signal('');
  readonly activeCategory = signal<NewsCategory>('general');
  readonly page = signal(1);
  readonly totalResults = signal(0);
  readonly pageSize = 12;

  searchTerm = '';
  readonly today = new Date();
  readonly featured = computed(() => this.articles()[0] ?? null);
  readonly latest = computed(() => this.articles().slice(1, 5));
  readonly feed = computed(() => this.articles().slice(5));
  readonly canLoadMore = computed(() => this.articles().length < this.totalResults());

  constructor() {
    this.loadNews(true);
  }

  selectCategory(category: NewsCategory): void {
    if (this.activeCategory() === category && !this.searchTerm) return;
    this.activeCategory.set(category);
    this.searchTerm = '';
    this.loadNews(true);
  }

  search(): void {
    this.loadNews(true);
  }

  clearSearch(): void {
    this.searchTerm = '';
    this.loadNews(true);
  }

  loadMore(): void {
    if (!this.canLoadMore() || this.loading()) return;
    this.page.update(value => value + 1);
    this.loadNews(false);
  }

  openArticle(article: NewsArticle): void {
    window.open(article.url, '_blank', 'noopener,noreferrer');
  }

  imageFallback(event: Event): void {
    const image = event.target as HTMLImageElement;
    image.style.display = 'none';
    image.parentElement?.classList.add('image-fallback');
  }

  private loadNews(reset: boolean): void {
    if (reset) {
      this.page.set(1);
      this.articles.set([]);
    }

    this.loading.set(true);
    this.error.set('');

    this.newsService.getHeadlines({
      category: this.activeCategory(),
      query: this.searchTerm,
      page: this.page(),
      pageSize: this.pageSize
    }).pipe(finalize(() => this.loading.set(false))).subscribe({
      next: response => {
        this.totalResults.set(response.totalResults);
        this.articles.update(current => reset ? response.articles : [...current, ...response.articles]);
      },
      error: (error: { error?: { message?: string }; message?: string }) => {
        this.error.set(error.error?.message ?? error.message ?? 'Unable to load the news right now.');
      }
    });
  }
}
