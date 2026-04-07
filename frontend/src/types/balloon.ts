export type BalloonType =
  | "dimension"
  | "tolerance"
  | "note"
  | "surface_finish"
  | "gd&t"
  | "other";

export interface Balloon {
  id: string;
  number: number;
  x_pct: number;
  y_pct: number;
  page: number;
  type: BalloonType;
  text?: string;
  description?: string;
  isAuto?: boolean;
}