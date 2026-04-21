import type { Balloon } from "../store/useStore";
import { api } from "./api";

export const getBalloons = (drawingId: number, pageNumber?: number) =>
  api.get<Balloon[]>("/api/balloons", {
    params: {
      drawing_id: drawingId,
      page_number: pageNumber,
    },
  });

export const autoDetectBalloons = (drawingId: number, pageNumber: number) =>
  api.post("/api/balloons/auto-detect", {
    drawing_id: drawingId,
    page_number: pageNumber,
  });

export const createBalloon = (payload: unknown) =>
  api.post("/api/balloons/", payload);

export const getBalloon = (balloonId: number) =>
  api.get(`/api/balloons/${balloonId}`);

export const updateBalloon = (balloonId: number, payload: unknown) =>
  api.patch(`/api/balloons/${balloonId}`, payload);

export const deleteBalloon = (balloonId: number) =>
  api.delete(`/api/balloons/${balloonId}`);

export const deleteAllBalloons = (drawingId: number, pageNumber?: number) =>
  api.delete("/api/balloons/all", {
    params: {
      drawing_id: drawingId,
      page_number: pageNumber,
    },
  });

/**
 * Upload a file (image or PDF) to the backend for unified upload + OCR detection.
 * Returns the drawing record, detected balloons, and a rendered image URL.
 */
export const detectImage = async (file: File) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await api.post("/api/drawings/upload-and-detect", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data;
};

