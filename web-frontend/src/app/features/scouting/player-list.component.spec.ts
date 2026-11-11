import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { PlayerListComponent } from './player-list.component';
import { PlayerService } from '../../core/services/player.service';
import { Player, PlayerStats } from '../../core/models/player.model';

describe('PlayerListComponent', () => {
  let component: PlayerListComponent;
  let fixture: ComponentFixture<PlayerListComponent>;
  let playerService: jasmine.SpyObj<PlayerService>;

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
      nombre: 'Kylian Mbappé',
      fecha_nacimiento: '1998-12-20',
      posicion: 'Delantero Centro',
      liga: 'LaLiga',
      club: 'Real Madrid',
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

  beforeEach(async () => {
    const playerServiceSpy = jasmine.createSpyObj('PlayerService', ['getPlayerStats', 'searchPlayers']);
    playerServiceSpy.getPlayerStats.and.returnValue(of(mockStats));

    await TestBed.configureTestingModule({
      imports: [PlayerListComponent, HttpClientTestingModule],
      providers: [
        provideRouter([]),
        { provide: PlayerService, useValue: playerServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(PlayerListComponent);
    component = fixture.componentInstance;
    playerService = TestBed.inject(PlayerService) as jasmine.SpyObj<PlayerService>;
    component.players = mockPlayers;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe conmutar el modo de vista entre grid y table', () => {
    expect(component.viewMode()).toBe('grid');
    component.setViewMode('table');
    expect(component.viewMode()).toBe('table');
  });

  it('debe filtrar jugadores por demarcación táctica', () => {
    component.setPositionFilter('DEL');
    expect(component.filteredPlayers.length).toBe(1);
    expect(component.filteredPlayers[0].nombre).toBe('Kylian Mbappé');

    component.setPositionFilter('MED');
    expect(component.filteredPlayers.length).toBe(1);
    expect(component.filteredPlayers[0].nombre).toBe('Pedri González');

    component.setPositionFilter('ALL');
    expect(component.filteredPlayers.length).toBe(2);
  });

  it('debe abrir el modal de perfil detallado y consultar los atributos normalizados (0-99)', () => {
    component.openPlayerDetail(mockPlayers[0]);

    expect(component.isProfileModalOpen()).toBeTrue();
    expect(component.selectedPlayer()).toEqual(mockPlayers[0]);
    expect(playerService.getPlayerStats).toHaveBeenCalledWith(1);
    expect(component.selectedPlayerStats()).toEqual(mockStats);
  });

  it('debe cerrar el modal de perfil al ejecutar closeProfileModal()', () => {
    component.openPlayerDetail(mockPlayers[0]);
    component.closeProfileModal();

    expect(component.isProfileModalOpen()).toBeFalse();
    expect(component.selectedPlayer()).toBeNull();
    expect(component.selectedPlayerStats()).toBeNull();
  });
});
