import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { SearchBarComponent } from './search-bar.component';
import { PlayerService } from '../../core/services/player.service';
import { Player } from '../../core/models/player.model';

describe('SearchBarComponent', () => {
  let component: SearchBarComponent;
  let fixture: ComponentFixture<SearchBarComponent>;
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

    await TestBed.configureTestingModule({
      imports: [SearchBarComponent, HttpClientTestingModule],
      providers: [
        provideRouter([
          { path: 'scouting/player/:id', component: SearchBarComponent },
        ]),
        { provide: PlayerService, useValue: playerServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(SearchBarComponent);
    component = fixture.componentInstance;
    playerService = TestBed.inject(PlayerService) as jasmine.SpyObj<PlayerService>;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe esperar el debounce de 300ms antes de llamar al endpoint de búsqueda', fakeAsync(() => {
    component.searchControl.setValue('Ped');
    tick(200);
    // A los 200ms todavía no se debe haber llamado a la API
    expect(playerService.searchPlayers).not.toHaveBeenCalled();

    tick(150); // Pasa de los 300ms totales
    expect(playerService.searchPlayers).toHaveBeenCalledWith('Ped', undefined, 8);
    expect(component.latestResults().length).toBe(2);
  }));

  it('no debe llamar repetidamente a la API si el valor no cambia (distinctUntilChanged)', fakeAsync(() => {
    component.searchControl.setValue('Pedri');
    tick(350);
    expect(playerService.searchPlayers).toHaveBeenCalledTimes(1);

    // Mismo valor emitido de nuevo
    component.searchControl.setValue('Pedri');
    tick(350);
    expect(playerService.searchPlayers).toHaveBeenCalledTimes(1);
  }));

  it('debe emitir playerSelected al seleccionar un futbolista del desplegable', () => {
    spyOn(component.playerSelected, 'emit');
    component.selectPlayer(mockPlayers[0]);

    expect(component.playerSelected.emit).toHaveBeenCalledWith(mockPlayers[0]);
    expect(component.isOpen()).toBeFalse();
  });

  it('debe emitir searchSubmitted al pulsar Enter', () => {
    spyOn(component.searchSubmitted, 'emit');
    component.searchControl.setValue('Yamal');
    component.submitSearch();

    expect(component.searchSubmitted.emit).toHaveBeenCalledWith('Yamal');
  });

  it('debe limpiar el control y resultados al ejecutar clearSearch()', () => {
    component.searchControl.setValue('Gavi');
    component.clearSearch();

    expect(component.searchControl.value).toBe('');
    expect(component.isOpen()).toBeFalse();
    expect(component.latestResults()).toEqual([]);
  });
});
