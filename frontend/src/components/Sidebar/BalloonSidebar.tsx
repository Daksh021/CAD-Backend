import { deleteBalloon } from "../../services/balloons";
import { useStore } from "../../store/useStore";

const BalloonSidebar = () => {
  const { balloons, setSelectedBalloonId, selectedBalloonId } = useStore();

  return (
    <div className="p-4 space-y-3 overflow-y-auto h-full">
      <h2 className="text-lg font-semibold mb-2">Balloon List</h2>

      {balloons.map((b: any) => {
        const isSelected = selectedBalloonId === b.id;

        return (
          <div
            key={b.id}
            onClick={() => setSelectedBalloonId(b.id)}
            className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 relative
  ${
    isSelected
      ? "bg-gray-700 border-2 border-gray-300 shadow-lg shadow-gray-400/40 scale-[1.05]"
      : "bg-gray-800 border border-gray-700 hover:border-gray-500"
  }`}
          >
            {/* 🔥 Left highlight bar */}
            {isSelected && (
              <div className="absolute left-0 top-0 h-full w-1 bg-shadow-gray-400 rounded-l-lg" />
            )}

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
                  const updated = balloons.filter(
                    (balloon) => balloon.id !== b.id,
                  );
                  useStore.getState().setBalloons(updated);
                });
              }}
              className="text-red-400 text-xs mt-2"
            >
              Delete
            </button>
          </div>
        );
      })}
    </div>
  );
};

export default BalloonSidebar;
