export interface Player {
  id?: number;
  nombre: string;
  fecha_nacimiento: string; // YYYY-MM-DD
  posicion: string;
  liga: string;
  club?: string;
  valor?: string;
  pace?: number;
  shooting?: number;
  passing?: number;
  dribbling?: number;
  defending?: number;
  physicality?: number;
  overall?: number;
}

export interface PlayerStats {
  player_id: number;
  nombre?: string;
  posicion?: string;
  pace: number;
  shooting: number;
  passing: number;
  dribbling: number;
  defending: number;
  physicality: number;
  overall: number;
}

/**
 * Calcula la edad precisa en años a partir de una fecha de nacimiento ISO (YYYY-MM-DD).
 */
export function calculateAge(birthDateStr?: string | null): number {
  if (!birthDateStr) return 0;
  const birth = new Date(birthDateStr);
  if (isNaN(birth.getTime())) return 0;

  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();

  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--;
  }

  return Math.max(0, age);
}

/**
 * Devuelve la categoría general según la demarcación táctica.
 * Prioriza demarcaciones ofensivas (DEL) y defensivas específicas antes de términos genéricos como 'centro'.
 */
export function getPositionGroup(posicion: string): 'POR' | 'DEF' | 'MED' | 'DEL' {
  const p = (posicion || '').toLowerCase();
  if (p.includes('portero') || p.includes('arquero') || p === 'por') return 'POR';
  if (p.includes('mediapunta')) return 'MED';
  if (p.includes('delantero') || p.includes('extremo') || p.includes('ariete') || p.includes('punta') || p === 'del') return 'DEL';
  if (p.includes('defensa') || p.includes('lateral') || p.includes('carrilero') || p.includes('central') || p === 'def') return 'DEF';
  if (p.includes('medio') || p.includes('centro') || p.includes('pivote') || p.includes('volante') || p.includes('interior') || p === 'med') return 'MED';
  return 'DEL';
}

/**
 * Estima el valor de mercado según media OVR y edad.
 */
export function estimateMarketValue(overall: number, age: number): string {
  if (!overall) return '€10M - €15M';
  let base = 5;

  if (overall >= 90) base = 130;
  else if (overall >= 87) base = 95;
  else if (overall >= 84) base = 70;
  else if (overall >= 80) base = 42;
  else if (overall >= 76) base = 22;
  else if (overall >= 72) base = 12;
  else base = 5;

  if (age > 0 && age <= 20) base *= 1.4;
  else if (age <= 23) base *= 1.2;
  else if (age >= 32) base *= 0.6;
  else if (age >= 34) base *= 0.4;

  const low = Math.round(base * 0.85);
  const high = Math.round(base * 1.15);
  return `€${low}M - €${high}M`;
}
