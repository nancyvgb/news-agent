import { ComponentFixture, TestBed } from '@angular/core/testing';

import { NewsDashboardComponent } from './news-dashboard.component';

describe('NewsDashboard', () => {
  let component: NewsDashboardComponent;
  let fixture: ComponentFixture<NewsDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NewsDashboardComponent],
    }).compileComponents();

    fixture = TestBed.createComponent(NewsDashboardComponent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
