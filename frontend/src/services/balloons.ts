import type { Balloon } from "../store/useStore";
import { api } from "./api";

export const getBalloons = (drawingId: number, pageNumber?: number) =>
  api.get<Balloon[]>("/balloons", {
    params: {
      drawing_id: drawingId,
      page_number: pageNumber,
    },
  });

export const autoDetectBalloons = (drawingId: number, pageNumber: number) =>
  api.post("/balloons/auto-detect", {
    drawing_id: drawingId,
    page_number: pageNumber,
  });

export const createBalloon = (payload: unknown) =>
  api.post("/balloons", payload);

export const getBalloon = (balloonId: number) =>
  api.get(`/balloons/${balloonId}`);

export const updateBalloon = (balloonId: number, payload: unknown) =>
  api.patch(`/balloons/${balloonId}`, payload);

export const deleteBalloon = (balloonId: number) =>
  api.delete(`/balloons/${balloonId}`);
