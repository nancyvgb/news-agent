// app.component.ts
import { Component } from '@angular/core';
import { NewsDashboardComponent } from './news-dashboard/news-dashboard.component';


@Component({
  selector: 'app-root',
  standalone: true,
  imports: [NewsDashboardComponent],
  template: `<app-news-dashboard />`
})
export class AppComponent {}
