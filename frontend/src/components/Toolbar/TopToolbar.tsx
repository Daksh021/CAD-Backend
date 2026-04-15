import { autoDetectBalloons, deleteAllBalloons } from "../../services/balloons";
import { exportExcel } from "../../services/export";
import { useStore } from "../../store/useStore";

const TopToolbar = () => {
  const { balloons, setBalloons, tool, setTool, setSelectedBalloonId } =
    useStore();

  // Temporary fixed values until drawing/page are added to the store.
  const drawingId = 1;
  const pageNumber = 1;

  const handleAutoDetect = async () => {
    try {
      const res = await autoDetectBalloons(drawingId, pageNumber);
      setBalloons(res.data.balloons || []);
    } catch (error) {
      console.error("Auto detect failed:", error);
    }
  };

  const handleDeleteAll = async () => {
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
        className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white"
      >
        Auto Detect
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
        className="px-4 py-2 rounded bg-green-600 hover:bg-green-500 text-white"
      >
        Export
      </button>
    </div>
  );
};

export default TopToolbar;
