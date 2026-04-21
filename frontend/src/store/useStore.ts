import { create } from "zustand";

type Tool = "select" | "add" | "pan";

export type Balloon = {
  id: number;
  balloon_number: number;
  x_pct: number;
  y_pct: number;
  page_number: number;
  balloon_type: string;
  extracted_text?: string;
  description?: string;
};

type StagePos = {
  x: number;
  y: number;
};

type StoreState = {
  imageUrl: string;
  setImageUrl: (url: string) => void;

  drawingId: number | null;
  setDrawingId: (id: number | null) => void;

  pageNumber: number;
  setPageNumber: (page: number) => void;

  balloons: Balloon[];
  selectedBalloonId: number | null;
  tool: Tool;
  zoom: number;
  stagePos: StagePos;

  setBalloons: (balloons: Balloon[]) => void;
  setSelectedBalloonId: (id: number | null) => void;
  setTool: (tool: Tool) => void;
  setZoom: (zoom: number) => void;
  setStagePos: (pos: StagePos) => void;
};

export const useStore = create<StoreState>((set) => ({
  imageUrl: "",
  drawingId: null,
  pageNumber: 1,
  balloons: [],
  selectedBalloonId: null,
  tool: "select",
  zoom: 1,
  stagePos: { x: 0, y: 0 },
  
  setImageUrl: (url: string) => set({ imageUrl: url }),
  setDrawingId: (id) => set({ drawingId: id }),
  setPageNumber: (page) => set({ pageNumber: page }),
  setBalloons: (balloons) => set({ balloons }),
  setSelectedBalloonId: (id) => set({ selectedBalloonId: id }),
  setTool: (tool) => set({ tool }),
  setZoom: (zoom) => set({ zoom }),
  setStagePos: (pos) => set({ stagePos: pos }),
}));

