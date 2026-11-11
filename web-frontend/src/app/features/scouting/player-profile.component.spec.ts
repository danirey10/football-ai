import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { ActivatedRoute, convertToParamMap, provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { PlayerProfileComponent } from './player-profile.component';
import { PlayerService } from '../../core/services/player.service';
import { Player, PlayerStats } from '../../core/models/player.model';

describe('PlayerProfileComponent', () => {
  let component: PlayerProfileComponent;
  let fixture: ComponentFixture<PlayerProfileComponent>;
  let playerService: jasmine.SpyObj<PlayerService>;

  const mockPlayer: Player = {
    id: 1,
    nombre: 'Pedri González',
    fecha_nacimiento: '2002-11-25',
    posicion: 'Centrocampista',
    liga: 'LaLiga EA Sports',
    club: 'FC Barcelona',
  };

  const mockStats: PlayerStats = {
    player_id: 1,
    nombre: 'Pedri González',
    posicion: 'Centrocampista',
    pace: 79,
    shooting: 74,
    passing: 91,
    dribbling: 89,
    defending: 68,
    physicality: 73,
    overall: 86,
  };

  beforeEach(async () => {
    const playerServiceSpy = jasmine.createSpyObj('PlayerService', [
      'getPlayerStats',
      'getPlayerWithStats',
      'searchPlayers',
    ]);
    playerServiceSpy.getPlayerWithStats.and.returnValue(of({ player: mockPlayer, stats: mockStats }));

    await TestBed.configureTestingModule({
      imports: [PlayerProfileComponent, HttpClientTestingModule],
      providers: [
        provideRouter([]),
        { provide: PlayerService, useValue: playerServiceSpy },
        {
          provide: ActivatedRoute,
          useValue: {
            paramMap: of(convertToParamMap({ id: '1' })),
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PlayerProfileComponent);
    component = fixture.componentInstance;
    playerService = TestBed.inject(PlayerService) as jasmine.SpyObj<PlayerService>;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe leer el ID de la URL y consultar los datos del jugador', () => {
    expect(component.playerId()).toBe('1');
    expect(playerService.getPlayerWithStats).toHaveBeenCalledWith('1');
    expect(component.player()?.nombre).toBe('Pedri González');
    expect(component.stats()?.overall).toBe(86);
  });

  it('debe configurar los datos para el gráfico de Radar con acentos esmeralda', () => {
    expect(component.radarChartData.labels?.length).toBe(6);
    expect(component.radarChartData.datasets.length).toBe(2);

    const playerDataset = component.radarChartData.datasets[0];
    expect(playerDataset.data).toEqual([79, 74, 91, 89, 68, 73]);
    expect(playerDataset.borderColor).toBe('#34d399'); // Acento esmeralda requerido

    const benchmarkDataset = component.radarChartData.datasets[1];
    expect(benchmarkDataset.data.length).toBe(6);
  });

  it('debe calcular la edad y el valor de mercado correctamente', () => {
    const age = component.calculateAge(mockPlayer.fecha_nacimiento);
    expect(age).toBeGreaterThanOrEqual(21);

    const value = component.getMarketValue(mockStats, mockPlayer);
    expect(value).toContain('€');
    expect(value).toContain('M');
  });

  it('debe mostrar mensaje de error si falla la llamada al servicio', () => {
    playerService.getPlayerWithStats.and.returnValue(throwError(() => new Error('Error al cargar')));
    const errorFixture = TestBed.createComponent(PlayerProfileComponent);
    const errorComp = errorFixture.componentInstance;
    errorFixture.detectChanges();

    expect(errorComp.errorMessage()).toBeTruthy();
  });

  it('debe generar el diagnóstico técnico dinámico listando métricas superiores a la media', () => {
    const verdict = component.getTechnicalVerdict(mockPlayer, mockStats);
    expect(verdict).toContain('Futbolista monitorizado en el que destacan sobre la media');
    expect(verdict).toContain('Pase (PAS)');
    expect(verdict).toContain('Regate (DRI)');
    expect(component.hasNoPotential(mockPlayer, mockStats)).toBeFalse();
  });

  it('debe indicar sin potencial adecuado si ninguna estadística supera la media posicional', () => {
    const lowStats: PlayerStats = {
      player_id: 99,
      nombre: 'Jugador Promedio',
      posicion: 'Centrocampista',
      pace: 50,
      shooting: 50,
      passing: 50,
      dribbling: 50,
      defending: 50,
      physicality: 50,
      overall: 50,
    };
    const verdict = component.getTechnicalVerdict(mockPlayer, lowStats);
    expect(verdict).toBe('Futbolista monitorizado sin potencial adecuado.');
    expect(component.hasNoPotential(mockPlayer, lowStats)).toBeTrue();
  });
});
