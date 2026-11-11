export type QuarterId = 'Q1' | 'Q2' | 'Q3' | 'Q4';

export interface RaeQuarter {
  id: QuarterId;
  name: string;
  months: string;
  count: number;
  percentage: number;
}

export interface RaeStats {
  totalPlayers: number;
  category?: string;
  season?: string;
  updatedAt?: string;
  quarters: RaeQuarter[];
}
