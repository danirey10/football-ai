import {
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  EventEmitter,
  HostListener,
  Input,
  OnDestroy,
  OnInit,
  Output,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import {
  Observable,
  Subject,
  catchError,
  debounceTime,
  distinctUntilChanged,
  finalize,
  of,
  shareReplay,
  switchMap,
  takeUntil,
  tap,
} from 'rxjs';
import { Player, calculateAge, getPositionGroup } from '../../core/models/player.model';
import { PlayerService } from '../../core/services/player.service';

@Component({
  selector: 'app-search-bar',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './search-bar.component.html',
  styleUrls: ['./search-bar.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SearchBarComponent implements OnInit, OnDestroy {
  private readonly playerService = inject(PlayerService);
  private readonly elementRef = inject(ElementRef);
  private readonly router = inject(Router);
  private readonly destroy$ = new Subject<void>();

  @Input() placeholder: string = 'Buscar futbolista por nombre (ej. Pedri, Mbappé, Yamal)...';
  @Output() playerSelected = new EventEmitter<Player>();
  @Output() searchSubmitted = new EventEmitter<string>();
  @Output() resultsFound = new EventEmitter<Player[]>();

  readonly searchControl = new FormControl<string>('', { nonNullable: true });
  readonly isLoading = signal<boolean>(false);
  readonly isOpen = signal<boolean>(false);
  readonly selectedIndex = signal<number>(-1);
  readonly latestResults = signal<Player[]>([]);

  /**
   * Flujo reactivo RxJS:
   * 1. debounceTime(300): amortigua pulsaciones de teclado para no saturar la API
   * 2. distinctUntilChanged(): evita llamadas duplicadas si el valor de búsqueda no ha variado
   * 3. switchMap(): cancela peticiones en curso y conmuta a la más reciente
   */
  readonly searchResults$: Observable<Player[]> = this.searchControl.valueChanges.pipe(
    debounceTime(300),
    distinctUntilChanged(),
    tap(() => {
      this.isLoading.set(true);
      this.selectedIndex.set(-1);
    }),
    switchMap((query: string) => {
      const term = (query || '').trim();
      if (!term) {
        this.isLoading.set(false);
        this.isOpen.set(false);
        this.latestResults.set([]);
        return of([]);
      }

      this.isOpen.set(true);
      return this.playerService.searchPlayers(term, undefined, 8).pipe(
        catchError((err) => {
          console.error('[SearchBarComponent] Error al buscar jugadores:', err);
          return of([]);
        }),
        finalize(() => {
          this.isLoading.set(false);
        })
      );
    }),
    tap((results) => {
      this.latestResults.set(results);
      this.resultsFound.emit(results);
    }),
    shareReplay(1),
    takeUntil(this.destroy$)
  );

  ngOnInit(): void {
    // Suscripción de ciclo de vida para mantener el flujo activo y propagar señales
    this.searchResults$.subscribe();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  @HostListener('document:click', ['$event'])
  onDocumentClick(event: MouseEvent): void {
    if (!this.elementRef.nativeElement.contains(event.target)) {
      this.isOpen.set(false);
    }
  }

  @HostListener('keydown.escape')
  onEscape(): void {
    this.isOpen.set(false);
  }

  onFocus(): void {
    if (this.searchControl.value.trim().length > 0) {
      this.isOpen.set(true);
    }
  }

  onKeyDown(event: KeyboardEvent): void {
    const results = this.latestResults();

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (!this.isOpen()) {
        this.isOpen.set(true);
        return;
      }
      const nextIdx = Math.min(this.selectedIndex() + 1, results.length - 1);
      this.selectedIndex.set(nextIdx);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      const prevIdx = Math.max(this.selectedIndex() - 1, -1);
      this.selectedIndex.set(prevIdx);
    } else if (event.key === 'Enter') {
      event.preventDefault();
      const currentIdx = this.selectedIndex();

      if (this.isOpen() && currentIdx >= 0 && currentIdx < results.length) {
        this.selectPlayer(results[currentIdx]);
      } else {
        this.submitSearch();
      }
    }
  }

  selectPlayer(player: Player): void {
    this.isOpen.set(false);
    this.playerSelected.emit(player);
    if (player.id !== undefined && player.id !== null) {
      this.router.navigate(['/scouting/player', player.id]);
    }
  }

  submitSearch(): void {
    const query = this.searchControl.value.trim();
    this.isOpen.set(false);
    this.searchSubmitted.emit(query);
  }

  clearSearch(): void {
    this.searchControl.setValue('');
    this.isOpen.set(false);
    this.selectedIndex.set(-1);
    this.latestResults.set([]);
  }

  calculateAge(birthDate?: string | null): number {
    return calculateAge(birthDate);
  }

  getPositionGroup(posicion: string): string {
    return getPositionGroup(posicion);
  }
}
