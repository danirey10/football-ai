import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { PlayerService } from './player.service';
import { Player, PlayerStats } from '../models/player.model';

describe('PlayerService', () => {
  let service: PlayerService;
  let httpMock: HttpTestingController;

  const mockPlayers: Player[] = [
    {
      id: 1,
      nombre: 'Pedri González',
      fecha_nacimiento: '2002-11-25',
      posicion: 'Centrocampista',
      liga: 'LaLiga',
      club: 'FC Barcelona',
    },
    {
      id: 2,
      nombre: 'Lamine Yamal',
      fecha_nacimiento: '2007-07-13',
      posicion: 'Extremo Derecho',
      liga: 'LaLiga',
      club: 'FC Barcelona',
    },
  ];

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

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [PlayerService],
    });

    service = TestBed.inject(PlayerService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse correctamente', () => {
    expect(service).toBeTruthy();
  });

  it('debe buscar jugadores pasando query, position y max_results', () => {
    service.searchPlayers('Pedri', 'Centrocampista', 5).subscribe((players) => {
      expect(players.length).toBe(1);
      expect(players[0].nombre).toBe('Pedri González');
    });

    const req = httpMock.expectOne((r) =>
      r.url === 'http://localhost:8000/api/players/search' &&
      r.params.get('query') === 'Pedri' &&
      r.params.get('position') === 'Centrocampista' &&
      r.params.get('max_results') === '5'
    );
    expect(req.request.method).toBe('GET');
    req.flush([mockPlayers[0]]);
  });

  it('debe obtener atributos normalizados de un jugador', () => {
    service.getPlayerStats(1).subscribe((stats) => {
      expect(stats.player_id).toBe(1);
      expect(stats.overall).toBe(86);
      expect(stats.passing).toBe(91);
    });

    const req = httpMock.expectOne('http://localhost:8000/api/players/1/stats');
    expect(req.request.method).toBe('GET');
    req.flush(mockStats);
  });

  it('debe obtener perfil del futbolista por ID', () => {
    service.getPlayerById(1).subscribe((player) => {
      expect(player.id).toBe(1);
      expect(player.nombre).toBe('Pedri González');
    });

    const req = httpMock.expectOne('http://localhost:8000/api/players/1');
    expect(req.request.method).toBe('GET');
    req.flush(mockPlayers[0]);
  });
});
