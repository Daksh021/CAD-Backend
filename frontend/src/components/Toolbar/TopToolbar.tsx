import { autoDetectBalloons } from "../../services/balloons";
import { useStore } from "../../store/useStore";

const TopToolbar = () => {
  const drawingId = 1;
  const page = 1;

  const { setBalloons, tool, setTool } = useStore();

  const handleAutoDetect = async () => {
    const res = await autoDetectBalloons(drawingId, page);
    setBalloons(res.data.balloons);
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
            ? "bg-blue-600 text-white"
            : "bg-blue-700 hover:bg-blue-600 text-white"
        }`}
      >
        Add Balloon
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
        onClick={handleAutoDetect}
        className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 text-white"
      >
        Auto Detect
      </button>

      <button className="px-4 py-2 rounded bg-green-600 hover:bg-green-500 text-white">
        Export
      </button>
    </div>
  );
};

export default TopToolbar;
