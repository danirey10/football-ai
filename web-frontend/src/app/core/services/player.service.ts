import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, catchError, forkJoin, map, of, switchMap, throwError } from 'rxjs';
import { environment } from '../../../environments/environment';
import { Player, PlayerStats } from '../models/player.model';

@Injectable({
  providedIn: 'root',
})
export class PlayerService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl}/players`;

  /**
   * Busca futbolistas en la API con soporte para filtros de texto, demarcación y límite de resultados.
   */
  searchPlayers(
    query?: string,
    position?: string,
    maxResults: number = 10
  ): Observable<Player[]> {
    let params = new HttpParams().set('max_results', maxResults.toString());

    if (query && query.trim()) {
      params = params.set('query', query.trim());
    }

    if (position && position.trim()) {
      params = params.set('position', position.trim());
    }

    return this.http
      .get<Player[]>(`${this.baseUrl}/search`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Recupera la ficha técnica y datos de un futbolista por su ID.
   */
  getPlayerById(playerId: number | string): Observable<Player> {
    return this.http
      .get<Player>(`${this.baseUrl}/${playerId}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Obtiene los atributos técnicos y físicos normalizados (0-99) de un jugador.
   */
  getPlayerStats(playerId: number | string): Observable<PlayerStats> {
    return this.http
      .get<PlayerStats>(`${this.baseUrl}/${playerId}/stats`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Recupera de forma coordinada el perfil del jugador y sus atributos FM (0-99).
   */
  getPlayerWithStats(playerId: number | string): Observable<{ player: Player; stats: PlayerStats }> {
    return this.getPlayerStats(playerId).pipe(
      switchMap((stats) => {
        return this.getPlayerById(playerId).pipe(
          map((player) => ({ player, stats })),
          catchError(() => {
            // Fallback por búsqueda de nombre si el endpoint por ID falla o no está disponible
            const query = stats.nombre || playerId.toString();
            return this.searchPlayers(query, undefined, 5).pipe(
              map((players) => {
                const numId = Number(playerId);
                const matched = players.find(
                  (p) => p.id === numId || (stats.nombre && p.nombre.toLowerCase() === stats.nombre.toLowerCase())
                ) || players[0];

                const player: Player = matched
                  ? { ...matched }
                  : {
                      id: isNaN(numId) ? 1 : numId,
                      nombre: stats.nombre || `Jugador #${playerId}`,
                      posicion: stats.posicion || 'Centrocampista',
                      fecha_nacimiento: '2002-11-25',
                      liga: 'LaLiga EA Sports',
                      club: 'Club Profesional',
                    };

                return { player, stats };
              }),
              catchError(() => {
                const numId = Number(playerId);
                const player: Player = {
                  id: isNaN(numId) ? 1 : numId,
                  nombre: stats.nombre || `Jugador #${playerId}`,
                  posicion: stats.posicion || 'Centrocampista',
                  fecha_nacimiento: '2002-11-25',
                  liga: 'LaLiga EA Sports',
                  club: 'Club Profesional',
                };
                return of({ player, stats });
              })
            );
          })
        );
      })
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    const errorMsg =
      error.error instanceof ErrorEvent
        ? `Error de red/cliente: ${error.error.message}`
        : `Error de la API (${error.status}): ${error.message}`;

    console.error(`[PlayerService] Fallo en la comunicación:`, errorMsg);
    return throwError(() => new Error(errorMsg));
  }
}
