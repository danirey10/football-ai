import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { DashboardComponent } from './dashboard.component';
import { StatsService, RaeStats } from '../../core/services/stats.service';
import { PlayerService } from '../../core/services/player.service';
import { Player } from '../../core/models/player.model';

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let mockStatsService: jasmine.SpyObj<StatsService>;
  let mockPlayerService: jasmine.SpyObj<PlayerService>;

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

  const mockPlayers: Player[] = [
    {
      id: 4,
      nombre: 'Kylian Mbappé',
      posicion: 'Delantero Centro',
      liga: 'LaLiga',
      fecha_nacimiento: '1998-12-20',
      club: 'Real Madrid',
      overall: 91,
      shooting: 90,
      pace: 97,
      passing: 80,
      defending: 36,
    },
    {
      id: 1,
      nombre: 'Pedri González',
      posicion: 'Centrocampista',
      liga: 'LaLiga',
      fecha_nacimiento: '2002-11-25',
      club: 'FC Barcelona',
      overall: 86,
      shooting: 74,
      pace: 79,
      passing: 91,
      defending: 68,
    },
  ];

  beforeEach(async () => {
    mockStatsService = jasmine.createSpyObj('StatsService', ['getRaeStats']);
    mockStatsService.getRaeStats.and.returnValue(of(mockRaeStats));

    mockPlayerService = jasmine.createSpyObj('PlayerService', ['searchPlayers', 'getPlayerStats']);
    mockPlayerService.searchPlayers.and.returnValue(of(mockPlayers));

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideRouter([]),
        { provide: StatsService, useValue: mockStatsService },
        { provide: PlayerService, useValue: mockPlayerService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the dashboard component', () => {
    expect(component).toBeTruthy();
  });

  it('should render the hero section and title correctly', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.hero-title')?.textContent).toContain('Encuentra y Evalúa');
  });

  it('should render four quarter cards when stats are loaded', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const cards = compiled.querySelectorAll('.quarter-card');
    expect(cards.length).toBe(4);
  });

  it('should handle service errors by emitting null without throwing', (done) => {
    mockStatsService.getRaeStats.and.returnValue(throwError(() => new Error('Error')));
    const errorFixture = TestBed.createComponent(DashboardComponent);
    const errorComp = errorFixture.componentInstance;

    errorComp.raeStats$.subscribe((data) => {
      expect(data).toBeNull();
      done();
    });
  });

  it('should return quarter id in trackByQuarter', () => {
    const quarter = mockRaeStats.quarters[0];
    expect(component.trackByQuarter(0, quarter)).toBe('Q1');
  });

  it('should sort top valued players correctly', () => {
    const top = component.topValuedPlayers;
    expect(top.length).toBe(2);
    expect(top[0].nombre).toBe('Kylian Mbappé');
  });

  it('should switch active leader tabs', () => {
    expect(component.activeLeaderTab()).toBe('goals');
    component.setActiveLeaderTab('passing');
    expect(component.activeLeaderTab()).toBe('passing');
  });
});
