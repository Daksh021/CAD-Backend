import { useState } from "react";
import { detectImage, autoDetectBalloons, deleteAllBalloons } from "../../services/balloons";
import { useStore } from "../../store/useStore";
import { exportExcel } from "../../services/export";

const API_BASE = "http://127.0.0.1:8000";

const TopToolbar = () => {
  const balloons = useStore((s) => s.balloons);
  const setBalloons = useStore((s) => s.setBalloons);
  const imageUrl = useStore((s) => s.imageUrl);
  const setImageUrl = useStore((s) => s.setImageUrl);
  const tool = useStore((s) => s.tool);
  const setTool = useStore((s) => s.setTool);
  const setSelectedBalloonId = useStore((s) => s.setSelectedBalloonId);
  const drawingId = useStore((s) => s.drawingId);
  const setDrawingId = useStore((s) => s.setDrawingId);
  const pageNumber = useStore((s) => s.pageNumber);

  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);

  /**
   * Unified upload handler: works for both images and PDFs.
   * - Sends file to backend's /upload-and-detect endpoint
   * - Backend converts PDF→PNG if needed, runs OCR, returns balloons + image URL
   * - For images, also shows a local preview instantly
   */
  const handleUpload = async (file: File) => {
    const isPDF = file.type === "application/pdf";

    // For images, show local preview instantly while backend processes
    if (!isPDF) {
      const localUrl = URL.createObjectURL(file);
      setImageUrl(localUrl);
    }

    setUploading(true);
    try {
      const data = await detectImage(file);

      // Set the drawing ID in store
      setDrawingId(data.drawing.id);

      // For PDFs (or to ensure consistency), use the backend-rendered image URL
      const renderUrl = `${API_BASE}${data.image_url}`;
      setImageUrl(renderUrl);

      // Set detected balloons
      setBalloons(data.balloons || []);
    } catch (err) {
      console.error("Upload & detection failed:", err);
      alert("Upload failed. Please check the backend is running.");
    } finally {
      setUploading(false);
    }
  };

  /**
   * Re-run auto-detection on the current drawing (if already uploaded).
   */
  const handleAutoDetect = async () => {
    if (!drawingId) {
      alert("Please upload a drawing first.");
      return;
    }

    setDetecting(true);
    try {
      const res = await autoDetectBalloons(drawingId, pageNumber);
      setBalloons(res.data.balloons || []);
    } catch (error) {
      console.error("Auto detect failed:", error);
      alert("Auto-detection failed.");
    } finally {
      setDetecting(false);
    }
  };

  const handleDeleteAll = async () => {
    if (!drawingId) return;
    const ok = window.confirm("Delete all balloons on this page?");
    if (!ok) return;

    try {
      await deleteAllBalloons(drawingId, pageNumber);
      setBalloons([]);
      setSelectedBalloonId(null);
    } catch (error) {
      console.error("Delete all failed:", error);
    }
  };

  const handleExport = async () => {
    if (!drawingId) {
      alert("Please upload a drawing first.");
      return;
    }

    try {
      const res = await exportExcel(drawingId);

      const blob = new Blob([res.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `balloons_${drawingId}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Export failed:", error);
    }
  };

  return (
    <div className="h-14 bg-gray-950 border-b border-gray-700 flex items-center px-4 gap-3">
      <button
        onClick={() => setTool("select")}
        className={`px-4 py-2 rounded ${
          tool === "select"
            ? "bg-slate-500 text-white"
            : "bg-slate-700 hover:bg-slate-600 text-white"
        }`}
      >
        Select
      </button>

      {/* File input: accepts images AND PDFs */}
      <label className="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-500 text-white cursor-pointer transition-colors">
        {uploading ? "Uploading..." : "📁 Upload File"}
        <input
          type="file"
          accept="image/*,.pdf,application/pdf"
          className="hidden"
          disabled={uploading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleUpload(file);
            e.target.value = ""; // reset so same file can be re-uploaded
          }}
        />
      </label>

      <button
        onClick={() => setTool("add")}
        className={`px-4 py-2 rounded ${
          tool === "add"
            ? "bg-pink-600 text-white"
            : "bg-pink-600 hover:bg-pink-500 text-white"
        }`}
      >
        Add Balloon
      </button>

      <button
        onClick={handleAutoDetect}
        disabled={!drawingId || detecting}
        className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-50 transition-colors"
      >
        {detecting ? "Detecting..." : "Auto Detect"}
      </button>

      <button
        onClick={() => setTool("pan")}
        className={`px-4 py-2 rounded ${
          tool === "pan"
            ? "bg-purple-600 text-white"
            : "bg-purple-700 hover:bg-purple-600 text-white"
        }`}
      >
        Pan
      </button>

      <button
        onClick={handleDeleteAll}
        disabled={balloons.length === 0}
        className="px-4 py-2 rounded bg-red-600 hover:bg-red-500 text-white disabled:opacity-50"
      >
        Delete All
      </button>

      <button
        onClick={handleExport}
        disabled={!drawingId}
        className="px-4 py-2 rounded bg-green-600 hover:bg-green-500 text-white disabled:opacity-50"
      >
        Export
      </button>
    </div>
  );
};

export default TopToolbar;
