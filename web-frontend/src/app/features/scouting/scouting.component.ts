import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { Player } from '../../core/models/player.model';
import { PlayerService } from '../../core/services/player.service';
import { SearchBarComponent } from './search-bar.component';
import { PlayerListComponent } from './player-list.component';

@Component({
  selector: 'app-scouting',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, SearchBarComponent, PlayerListComponent],
  templateUrl: './scouting.component.html',
  styleUrls: ['./scouting.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ScoutingComponent implements OnInit {
  private readonly playerService = inject(PlayerService);
  private readonly router = inject(Router);

  readonly players = signal<Player[]>([]);
  readonly currentQuery = signal<string>('');
  readonly currentPosition = signal<string>('ALL');
  readonly isLoading = signal<boolean>(false);

  ngOnInit(): void {
    this.executeSearch('', 'ALL', 24);
  }

  onSearchSubmitted(query: string): void {
    this.executeSearch(query, this.currentPosition(), 24);
  }

  onPositionChanged(position: string): void {
    this.currentPosition.set(position);
    this.executeSearch(this.currentQuery(), position, 24);
  }

  onPlayerSelected(player: Player): void {
    if (player.id !== undefined && player.id !== null) {
      this.router.navigate(['/scouting/player', player.id]);
    }
  }

  onResultsFound(results: Player[]): void {
    if (results.length > 0 && !this.currentQuery()) {
      this.players.set(results);
    }
  }

  private executeSearch(query: string, position: string = 'ALL', maxResults: number = 24): void {
    this.isLoading.set(true);
    this.currentQuery.set(query);

    const posFilter = position && position !== 'ALL' ? position : undefined;

    this.playerService.searchPlayers(query || undefined, posFilter, maxResults).subscribe({
      next: (data) => {
        this.players.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        console.error('[ScoutingComponent] Error en la búsqueda de scouting:', err);
        this.players.set([]);
        this.isLoading.set(false);
      },
    });
  }
}
