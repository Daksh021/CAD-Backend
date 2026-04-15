import { api } from "./api";

export const exportExcel = (drawingId: number, includeRemarks = true) =>
  api.post(
    "/api/export/excel",
    {
      drawing_id: drawingId,
      include_remarks: includeRemarks,
    },
    {
      responseType: "blob",
    },
  );
