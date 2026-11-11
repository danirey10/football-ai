import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink, RouterLinkActive } from '@angular/router';
import { Subject, catchError, finalize, of, switchMap, takeUntil } from 'rxjs';
import { BaseChartDirective } from 'ng2-charts';
import {
  Chart,
  ChartConfiguration,
  ChartData,
  ChartType,
  registerables,
} from 'chart.js';
import {
  Player,
  PlayerStats,
  calculateAge,
  estimateMarketValue,
  getPositionGroup,
} from '../../core/models/player.model';
import { PlayerService } from '../../core/services/player.service';

// Registro explícito de los controladores y componentes requeridos por Chart.js
Chart.register(...registerables);

@Component({
  selector: 'app-player-profile',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, BaseChartDirective],
  templateUrl: './player-profile.component.html',
  styleUrls: ['./player-profile.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlayerProfileComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly playerService = inject(PlayerService);
  private readonly destroy$ = new Subject<void>();

  readonly playerId = signal<string>('');
  readonly player = signal<Player | null>(null);
  readonly stats = signal<PlayerStats | null>(null);
  readonly isLoading = signal<boolean>(true);
  readonly errorMessage = signal<string | null>(null);

  // Configuración del gráfico de Radar (Chart.js / ng2-charts)
  readonly radarChartType: ChartType = 'radar';
  radarChartData: ChartData<'radar'> = {
    labels: ['Ritmo (PAC)', 'Tiro (SHO)', 'Pase (PAS)', 'Regate (DRI)', 'Defensa (DEF)', 'Físico (PHY)'],
    datasets: [],
  };

  readonly radarChartOptions: ChartConfiguration['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    elements: {
      line: {
        tension: 0.2,
      },
    },
    scales: {
      r: {
        min: 0,
        max: 100,
        beginAtZero: true,
        ticks: {
          stepSize: 20,
          color: '#64748b',
          backdropColor: 'transparent',
          font: { size: 10, family: 'Inter, sans-serif' },
        },
        grid: {
          color: 'rgba(51, 65, 85, 0.75)',
          lineWidth: 1,
        },
        angleLines: {
          color: 'rgba(71, 85, 105, 0.6)',
          lineWidth: 1,
        },
        pointLabels: {
          color: '#f8fafc',
          font: {
            size: 11,
            weight: 'bold',
            family: 'Inter, sans-serif',
          },
          padding: 8,
        },
      },
    },
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          color: '#cbd5e1',
          font: { size: 12, weight: 'bold' },
          usePointStyle: true,
          padding: 16,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.95)',
        titleColor: '#34d399',
        bodyColor: '#f8fafc',
        borderColor: '#334155',
        borderWidth: 1,
        padding: 12,
        boxPadding: 6,
        usePointStyle: true,
        callbacks: {
          label: (context) => ` ${context.dataset.label}: ${context.raw} / 99`,
        },
      },
    },
  };

  ngOnInit(): void {
    // 1. Lee el ID del jugador desde los parámetros de la URL
    this.route.paramMap
      .pipe(
        switchMap((params) => {
          const id = params.get('id') || params.get('player_id') || '1';
          this.playerId.set(id);
          this.isLoading.set(true);
          this.errorMessage.set(null);

          // 2. Consume el endpoint /api/players/{player_id}/stats
          return this.playerService.getPlayerWithStats(id).pipe(
            catchError((err) => {
              console.error('[PlayerProfileComponent] Error al obtener ficha técnica:', err);
              this.errorMessage.set('No se pudo encontrar la ficha técnica del futbolista solicitado.');
              return of(null);
            }),
            finalize(() => {
              this.isLoading.set(false);
            })
          );
        }),
        takeUntil(this.destroy$)
      )
      .subscribe((data) => {
        if (data) {
          this.player.set(data.player);
          this.stats.set(data.stats);
          // 3. Configura los datos para el gráfico de Radar
          this.configureRadarData(data.player, data.stats);
        }
      });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  /**
   * Configura las métricas del jugador frente al benchmark promedio de su posición.
   */
  private configureRadarData(player: Player, stats: PlayerStats): void {
    const playerMetrics = [
      stats.pace,
      stats.shooting,
      stats.passing,
      stats.dribbling,
      stats.defending,
      stats.physicality,
    ];

    const benchmark = this.getPositionBenchmark(player.posicion);

    this.radarChartData = {
      labels: ['Ritmo (PAC)', 'Tiro (SHO)', 'Pase (PAS)', 'Regate (DRI)', 'Defensa (DEF)', 'Físico (PHY)'],
      datasets: [
        {
          label: `${player.nombre} (Evaluación)`,
          data: playerMetrics,
          borderColor: '#34d399', // Acento esmeralda solicitado
          backgroundColor: 'rgba(52, 211, 153, 0.22)',
          pointBackgroundColor: '#34d399',
          pointBorderColor: '#ffffff',
          pointHoverBackgroundColor: '#ffffff',
          pointHoverBorderColor: '#34d399',
          borderWidth: 2.5,
          pointRadius: 4,
          pointHoverRadius: 6,
        },
        {
          label: `Media de Referencia (${player.posicion || 'Posición'})`,
          data: benchmark,
          borderColor: 'rgba(148, 163, 184, 0.75)', // Slate suave
          backgroundColor: 'rgba(148, 163, 184, 0.08)',
          pointBackgroundColor: 'rgba(148, 163, 184, 0.8)',
          pointBorderColor: '#ffffff',
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 3,
        },
      ],
    };
  }

  /**
   * Genera el benchmark posicional comparativo estándar para scouting.
   */
  private getPositionBenchmark(posicion: string): number[] {
    const group = getPositionGroup(posicion);
    switch (group) {
      case 'DEL':
        return [82, 80, 68, 78, 38, 74];
      case 'MED':
        return [73, 72, 82, 80, 68, 73];
      case 'DEF':
        return [72, 45, 68, 64, 80, 81];
      case 'POR':
        return [48, 22, 65, 48, 84, 76];
      default:
        return [70, 70, 70, 70, 70, 70];
    }
  }

  calculateAge(birthDateStr?: string | null): number {
    return calculateAge(birthDateStr);
  }

  getMarketValue(stats: PlayerStats | null, player: Player | null): string {
    const overall = stats?.overall ?? 75;
    const age = calculateAge(player?.fecha_nacimiento);
    return estimateMarketValue(overall, age);
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

  /**
   * Genera el diagnóstico técnico dinámico comparando las métricas del jugador
   * con la media de referencia de su posición.
   */
  getTechnicalVerdict(player: Player | null, stats: PlayerStats | null): string {
    if (!player || !stats) {
      return 'Futbolista en proceso de análisis técnico.';
    }

    const benchmark = this.getPositionBenchmark(player.posicion);
    const metricDefs: { name: string; key: keyof PlayerStats; benchIndex: number }[] = [
      { name: 'Ritmo (PAC)', key: 'pace', benchIndex: 0 },
      { name: 'Tiro (SHO)', key: 'shooting', benchIndex: 1 },
      { name: 'Pase (PAS)', key: 'passing', benchIndex: 2 },
      { name: 'Regate (DRI)', key: 'dribbling', benchIndex: 3 },
      { name: 'Defensa (DEF)', key: 'defending', benchIndex: 4 },
      { name: 'Físico (PHY)', key: 'physicality', benchIndex: 5 },
    ];

    const standouts: { label: string; diff: number }[] = [];
    for (const m of metricDefs) {
      const val = (stats[m.key] as number) ?? 0;
      const bench = benchmark[m.benchIndex];
      if (val > bench) {
        standouts.push({
          label: `${m.name} (${val} vs ${bench} media)`,
          diff: val - bench,
        });
      }
    }

    if (standouts.length === 0) {
      return 'Futbolista monitorizado sin potencial adecuado.';
    }

    // Ordenados de mayor a menor diferencia respecto a la media
    standouts.sort((a, b) => b.diff - a.diff);

    return `Futbolista monitorizado en el que destacan sobre la media de los demás futbolistas de su posición en: ${standouts.map((s) => s.label).join(', ')}.`;
  }

  /**
   * Indica si el jugador no supera la media posicional en ninguna estadística clave.
   */
  hasNoPotential(player: Player | null, stats: PlayerStats | null): boolean {
    if (!player || !stats) return false;
    const benchmark = this.getPositionBenchmark(player.posicion);
    const metricKeys: (keyof PlayerStats)[] = [
      'pace',
      'shooting',
      'passing',
      'dribbling',
      'defending',
      'physicality',
    ];
    return metricKeys.every((key, idx) => ((stats[key] as number) ?? 0) <= benchmark[idx]);
  }
}
