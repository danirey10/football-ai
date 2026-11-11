import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { Observable, catchError, of } from 'rxjs';
import { StatsService, RaeStats, RaeQuarter } from '../../core/services/stats.service';
import { PlayerService } from '../../core/services/player.service';
import {
  Player,
  calculateAge,
  estimateMarketValue,
  getPositionGroup,
} from '../../core/models/player.model';
import { SearchBarComponent } from '../scouting/search-bar.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, SearchBarComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DashboardComponent implements OnInit {
  private readonly statsService = inject(StatsService);
  private readonly playerService = inject(PlayerService);
  private readonly router = inject(Router);

  // Ejemplos de búsqueda rápida
  readonly quickSearchExamples = [
    { label: 'Pedri', query: 'Pedri', id: 1 },
    { label: 'Kylian Mbappé', query: 'Mbappé', id: 4 },
    { label: 'Lamine Yamal', query: 'Yamal', id: 2 },
    { label: 'Jude Bellingham', query: 'Bellingham', id: 3 },
    { label: 'Erling Haaland', query: 'Haaland', id: 6 },
    { label: 'Pau Cubarsí', query: 'Cubarsí', id: 8 },
    { label: 'Vinicius Jr', query: 'Vinicius', id: 5 },
    { label: 'Rodri', query: 'Rodri', id: 7 },
  ];

  // Listados clasificados con Signals
  readonly allPlayers = signal<Player[]>([]);
  readonly isLoadingPlayers = signal<boolean>(true);
  readonly activeLeaderTab = signal<'goals' | 'passing' | 'pace' | 'defense'>('goals');

  // Signals computadas para rankings con memoización automática (máximo rendimiento)
  readonly topValuedPlayersSignal = computed(() =>
    [...this.allPlayers()]
      .sort((a, b) => (b.overall ?? 0) - (a.overall ?? 0))
      .slice(0, 4)
  );

  readonly topShootingPlayersSignal = computed(() =>
    [...this.allPlayers()]
      .sort((a, b) => (b.shooting ?? 0) - (a.shooting ?? 0))
      .slice(0, 5)
  );

  readonly topPassingPlayersSignal = computed(() =>
    [...this.allPlayers()]
      .sort((a, b) => (b.passing ?? 0) - (a.passing ?? 0))
      .slice(0, 5)
  );

  readonly topPacePlayersSignal = computed(() =>
    [...this.allPlayers()]
      .sort((a, b) => (b.pace ?? 0) - (a.pace ?? 0))
      .slice(0, 5)
  );

  readonly topDefendingPlayersSignal = computed(() =>
    [...this.allPlayers()]
      .sort((a, b) => (b.defending ?? 0) - (a.defending ?? 0))
      .slice(0, 5)
  );

  // Getters para compatibilidad transparente con templates y tests
  get topValuedPlayers(): Player[] {
    return this.topValuedPlayersSignal();
  }

  get topShootingPlayers(): Player[] {
    return this.topShootingPlayersSignal();
  }

  get topPassingPlayers(): Player[] {
    return this.topPassingPlayersSignal();
  }

  get topPacePlayers(): Player[] {
    return this.topPacePlayersSignal();
  }

  get topDefendingPlayers(): Player[] {
    return this.topDefendingPlayersSignal();
  }

  /**
   * Suscripción reactiva para el informe demográfico RAE.
   */
  readonly raeStats$: Observable<RaeStats | null> = this.statsService.getRaeStats().pipe(
    catchError((error) => {
      console.error('Fallo en la recepción de estadísticas RAE:', error);
      return of(null);
    })
  );

  ngOnInit(): void {
    this.loadScoutingCatalog();
  }

  loadScoutingCatalog(): void {
    this.isLoadingPlayers.set(true);
    this.playerService.searchPlayers('', undefined, 30).subscribe({
      next: (players) => {
        this.allPlayers.set(players);
        this.isLoadingPlayers.set(false);
      },
      error: (err) => {
        console.error('[DashboardComponent] Error al cargar catálogo de scouting:', err);
        this.isLoadingPlayers.set(false);
      },
    });
  }

  setActiveLeaderTab(tab: 'goals' | 'passing' | 'pace' | 'defense'): void {
    this.activeLeaderTab.set(tab);
  }

  onPlayerSelected(player: Player): void {
    if (player.id !== undefined && player.id !== null) {
      this.router.navigate(['/scouting/player', player.id]);
    }
  }

  onSearchSubmitted(query: string): void {
    this.router.navigate(['/scouting'], { queryParams: { q: query } });
  }

  navigateToPlayer(id?: number): void {
    if (id !== undefined && id !== null) {
      this.router.navigate(['/scouting/player', id]);
    }
  }

  trackByQuarter(_index: number, quarter: RaeQuarter): string {
    return quarter.id;
  }

  calculateAge(birthDateStr?: string | null): number {
    return calculateAge(birthDateStr);
  }

  getMarketValue(player: Player): string {
    return estimateMarketValue(player.overall ?? 75, calculateAge(player.fecha_nacimiento));
  }

  getPositionGroup(posicion: string): string {
    return getPositionGroup(posicion);
  }

  getInitials(name?: string): string {
    if (!name) return 'PL';
    const parts = name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].substring(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
}
