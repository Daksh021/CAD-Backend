import { api } from "./api";

export const uploadDrawing = (formData: FormData) =>
  api.post("/api/drawings/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export const getDrawingDetails = (drawingId: number) =>
  api.get(`/api/drawings/${drawingId}`);

export const getDrawingPageUrl = (drawingId: number, page: number) =>
  `http://127.0.0.1:8000/api/drawings/${drawingId}/render/${page}`;

export const deleteDrawing = (drawingId: number) =>
  api.delete(`/api/drawings/${drawingId}`);
