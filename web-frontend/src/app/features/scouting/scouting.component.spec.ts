import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { ScoutingComponent } from './scouting.component';
import { PlayerService } from '../../core/services/player.service';
import { Player } from '../../core/models/player.model';

describe('ScoutingComponent', () => {
  let component: ScoutingComponent;
  let fixture: ComponentFixture<ScoutingComponent>;
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
      nombre: 'Lamine Yamal',
      fecha_nacimiento: '2007-07-13',
      posicion: 'Extremo Derecho',
      liga: 'LaLiga',
      club: 'FC Barcelona',
    },
  ];

  beforeEach(async () => {
    const playerServiceSpy = jasmine.createSpyObj('PlayerService', ['searchPlayers', 'getPlayerStats']);
    playerServiceSpy.searchPlayers.and.returnValue(of(mockPlayers));
    playerServiceSpy.getPlayerStats.and.returnValue(of({
      player_id: 1,
      pace: 80,
      shooting: 75,
      passing: 90,
      dribbling: 88,
      defending: 68,
      physicality: 73,
      overall: 85,
    }));

    await TestBed.configureTestingModule({
      imports: [ScoutingComponent, HttpClientTestingModule],
      providers: [
        provideRouter([]),
        { provide: PlayerService, useValue: playerServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ScoutingComponent);
    component = fixture.componentInstance;
    playerService = TestBed.inject(PlayerService) as jasmine.SpyObj<PlayerService>;
    fixture.detectChanges();
  });

  it('debe crearse e inicializar la búsqueda de talentos', () => {
    expect(component).toBeTruthy();
    expect(playerService.searchPlayers).toHaveBeenCalled();
    expect(component.players().length).toBe(2);
  });

  it('debe ejecutar una nueva búsqueda cuando el usuario presiona Enter en la search-bar', () => {
    component.onSearchSubmitted('Mbappé');
    expect(playerService.searchPlayers).toHaveBeenCalledWith('Mbappé', undefined, 24);
    expect(component.currentQuery()).toBe('Mbappé');
  });

  it('debe navegar a la vista de perfil del jugador cuando se selecciona uno', () => {
    const router = TestBed.inject(Router);
    spyOn(router, 'navigate');
    component.onPlayerSelected(mockPlayers[0]);
    expect(router.navigate).toHaveBeenCalledWith(['/scouting/player', 1]);
  });
});
