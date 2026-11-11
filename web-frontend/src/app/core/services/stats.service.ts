import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, catchError, throwError, shareReplay } from 'rxjs';
import { environment } from '../../../environments/environment';
import { RaeStats } from '../models/rae-stats.model';

export * from '../models/rae-stats.model';

@Injectable({
  providedIn: 'root',
})
export class StatsService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = `${environment.apiUrl}/stats/rae`;

  /**
   * Obtiene la distribución del Efecto de la Edad Relativa (RAE).
   * Utiliza shareReplay(1) para cachear la última emisión entre múltiples suscriptores.
   */
  getRaeStats(sampleSize?: number, categoria?: string): Observable<RaeStats> {
    let params = new HttpParams();
    if (sampleSize) {
      params = params.set('sample_size', sampleSize.toString());
    }
    if (categoria && categoria.trim()) {
      params = params.set('categoria', categoria.trim());
    }

    return this.http.get<RaeStats>(this.apiUrl, { params }).pipe(
      shareReplay(1),
      catchError(this.handleError)
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    const errorMsg =
      error.error instanceof ErrorEvent
        ? `Error del cliente: ${error.error.message}`
        : `Error del servidor (${error.status}): ${error.message}`;

    console.error(`[StatsService] Error en la petición RAE:`, errorMsg);
    return throwError(() => new Error(errorMsg));
  }
}
