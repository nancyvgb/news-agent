import {
  Component,
  ChangeDetectionStrategy,
  inject,
  signal
} from '@angular/core';

import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { NewsService } from '../../services/news.service';
import { ChatMessage } from '../../models/news.models';

@Component({
  selector: 'app-news-agent',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './news-agent.component.html',
  styleUrls: ['./news-agent.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class NewsAgentComponent {
  private readonly newsService = inject(NewsService);

  readonly messages = signal<ChatMessage[]>([]);
  readonly loading = signal(false);
  readonly isOpen = signal(true);

  userInput = '';

  /**
   * Unique conversation ID for this chat.
   */
  private readonly threadId = crypto.randomUUID();

  toggle(): void {
    this.isOpen.update(v => !v);
  }

  send(): void {
    const message = this.userInput.trim();

    if (!message || this.loading()) {
      return;
    }

    this.userInput = '';

    this.messages.update(msgs => [
      ...msgs,
      {
        type: 'human',
        content: message
      }
    ]);

    this.loading.set(true);

    this.newsService
      .sendMessage(message, this.threadId)
      .subscribe({
        next: (response) => {
          this.messages.set(response.messages);
          this.loading.set(false);
        },

        error: () => {
          this.messages.update(msgs => [
            ...msgs,
            {
              type: 'ai',
              content:
                'Sorry, something went wrong. Please try again.'
            }
          ]);

          this.loading.set(false);
        }
      });
  }

  clear(): void {
    this.newsService
      .clearChat(this.threadId)
      .subscribe({
        next: () => {
          this.messages.set([]);
        },

        error: () => {
          this.messages.set([]);
        }
      });
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }
}