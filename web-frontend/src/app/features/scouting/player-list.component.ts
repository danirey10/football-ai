import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { Player, PlayerStats, calculateAge, getPositionGroup } from '../../core/models/player.model';
import { PlayerService } from '../../core/services/player.service';

@Component({
  selector: 'app-player-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './player-list.component.html',
  styleUrls: ['./player-list.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlayerListComponent {
  private readonly playerService = inject(PlayerService);
  private readonly router = inject(Router);

  @Input() players: Player[] = [];
  @Input() searchQuery: string = '';
  @Input() isLoading: boolean = false;

  @Output() playerSelected = new EventEmitter<Player>();
  @Output() positionFilterChanged = new EventEmitter<string>();

  readonly viewMode = signal<'grid' | 'table'>('grid');
  readonly activePositionFilter = signal<string>('ALL');

  // Estado para el modal de vista rápida
  readonly isProfileModalOpen = signal<boolean>(false);
  readonly selectedPlayer = signal<Player | null>(null);
  readonly selectedPlayerStats = signal<PlayerStats | null>(null);
  readonly isLoadingStats = signal<boolean>(false);
  readonly statsError = signal<string | null>(null);

  setViewMode(mode: 'grid' | 'table'): void {
    this.viewMode.set(mode);
  }

  setPositionFilter(group: string): void {
    this.activePositionFilter.set(group);
    this.positionFilterChanged.emit(group);
  }

  get filteredPlayers(): Player[] {
    const filter = this.activePositionFilter();
    if (filter === 'ALL') {
      return this.players;
    }
    const matched = this.players.filter(
      (player) => getPositionGroup(player.posicion) === filter
    );
    return matched.length > 0 ? matched : this.players;
  }

  /**
   * Abre el modal de vista rápida con los atributos técnicos y físicos (0-99).
   */
  openPlayerDetail(player: Player): void {
    if (this.selectedPlayer()?.id === player.id && this.isProfileModalOpen()) {
      return;
    }

    this.selectedPlayer.set(player);
    this.isProfileModalOpen.set(true);
    this.isLoadingStats.set(true);
    this.statsError.set(null);
    this.selectedPlayerStats.set(null);

    const playerId = player.id ?? player.nombre;
    this.playerService.getPlayerStats(playerId).subscribe({
      next: (stats) => {
        this.selectedPlayerStats.set(stats);
        this.isLoadingStats.set(false);
      },
      error: (err) => {
        console.error('[PlayerListComponent] Error al cargar estadísticas del jugador:', err);
        this.statsError.set('No se pudieron obtener las estadísticas de scouting.');
        this.isLoadingStats.set(false);
      },
    });
  }

  closeProfileModal(): void {
    this.isProfileModalOpen.set(false);
    this.selectedPlayer.set(null);
    this.selectedPlayerStats.set(null);
    this.statsError.set(null);
  }

  navigateToProfile(player: Player): void {
    this.closeProfileModal();
    if (player.id !== undefined && player.id !== null) {
      this.router.navigate(['/scouting/player', player.id]);
    }
  }

  calculateAge(birthDate?: string | null): number {
    return calculateAge(birthDate);
  }

  getPositionGroup(posicion: string): string {
    return getPositionGroup(posicion);
  }

  getStatClass(val: number): string {
    if (val >= 85) return 'stat-elite';
    if (val >= 75) return 'stat-high';
    if (val >= 65) return 'stat-medium';
    return 'stat-low';
  }
}
