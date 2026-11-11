import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
  },
  {
    path: 'scouting',
    loadComponent: () =>
      import('./features/scouting/scouting.component').then((m) => m.ScoutingComponent),
  },
  {
    path: 'scouting/player/:id',
    loadComponent: () =>
      import('./features/scouting/player-profile.component').then((m) => m.PlayerProfileComponent),
  },
  {
    path: 'players/:id',
    loadComponent: () =>
      import('./features/scouting/player-profile.component').then((m) => m.PlayerProfileComponent),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
