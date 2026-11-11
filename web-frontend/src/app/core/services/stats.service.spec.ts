import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { StatsService, RaeStats } from './stats.service';

describe('StatsService', () => {
  let service: StatsService;
  let httpTestingController: HttpTestingController;

  const mockRaeStats: RaeStats = {
    totalPlayers: 350,
    category: 'Canteras LaLiga / Sub-19',
    season: '2025/2026',
    quarters: [
      { id: 'Q1', name: 'Primer Trimestre', months: 'Ene - Mar', count: 145, percentage: 41.4 },
      { id: 'Q2', name: 'Segundo Trimestre', months: 'Abr - Jun', count: 100, percentage: 28.6 },
      { id: 'Q3', name: 'Tercer Trimestre', months: 'Jul - Sep', count: 65, percentage: 18.6 },
      { id: 'Q4', name: 'Cuarto Trimestre', months: 'Oct - Dic', count: 40, percentage: 11.4 },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        StatsService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(StatsService);
    httpTestingController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTestingController.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  it('should retrieve RAE stats via GET', () => {
    service.getRaeStats().subscribe((stats) => {
      expect(stats).toEqual(mockRaeStats);
      expect(stats.quarters.length).toBe(4);
    });

    const req = httpTestingController.expectOne('http://localhost:8000/api/stats/rae');
    expect(req.request.method).toEqual('GET');
    req.flush(mockRaeStats);
  });

  it('should handle HTTP error gracefully', (done) => {
    service.getRaeStats().subscribe({
      next: () => fail('expected an error, not stats'),
      error: (error) => {
        expect(error.message).toContain('Error del servidor');
        done();
      },
    });

    const req = httpTestingController.expectOne('http://localhost:8000/api/stats/rae');
    req.flush('Error de servidor', { status: 500, statusText: 'Internal Server Error' });
  });
});
