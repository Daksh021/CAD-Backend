import { useStore } from "../../store/useStore";
import { deleteBalloon } from "../../services/balloons";

const BalloonSidebar = () => {
  const { balloons, setSelectedBalloonId } = useStore();

  return (
    <div className="p-4 space-y-3 overflow-y-auto h-full">
      <h2 className="text-lg font-semibold mb-2">Balloon List</h2>

      {balloons.map((b: any) => (
  <div
    key={b.id}
    onClick={() => setSelectedBalloonId(b.id)}
    className="p-3 bg-gray-800 rounded-lg border border-gray-700 cursor-pointer"
  >
    <div className="font-bold">Balloon {b.balloon_number}</div>
    <div className="text-sm text-gray-400">{b.balloon_type}</div>
    <div className="text-xs text-gray-500">
      x: {b.x_pct.toFixed(2)}, y: {b.y_pct.toFixed(2)}
    </div>

    {/* ✅ DELETE BUTTON */}
    <button
      onClick={(e) => {
        e.stopPropagation();

        deleteBalloon(b.id).then(() => {
          const updated = balloons.filter((balloon) => balloon.id !== b.id);
          useStore.getState().setBalloons(updated);
        });
      }}
      className="text-red-400 text-xs mt-2"
    >
      Delete
    </button>
  </div>
))}
    </div>
  );
};

export default BalloonSidebar;
