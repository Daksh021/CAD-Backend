import { useEffect, useRef, useState } from "react";
import {
  Circle,
  Group,
  Image as KonvaImage,
  Layer,
  Stage,
  Text,
} from "react-konva";
import useImage from "use-image";

import {
  createBalloon,
  getBalloons,
  updateBalloon,
} from "../../services/balloons";
import { getDrawingPageUrl } from "../../services/drawings";
import { useStore } from "../../store/useStore";

const DrawingCanvas = () => {
  const drawingId = 1;
  const page = 1;

  const containerRef = useRef<HTMLDivElement>(null);

  const [stageSize, setStageSize] = useState({
    width: 800,
    height: 600,
  });

  const [imageUrl, setImageUrl] = useState("");
  const [image] = useImage(imageUrl);
  const { zoom, setZoom } = useStore();
  const { stagePos, setStagePos } = useStore();

  const [scale, setScale] = useState(1);

  const {
    balloons,
    setBalloons,
    tool,
    selectedBalloonId,
    setSelectedBalloonId,
  } = useStore();

  // Load data
  useEffect(() => {
    const url = getDrawingPageUrl(drawingId, page);
    console.log("IMAGE URL:", url);
    setImageUrl(url);

    getBalloons(drawingId, page)
      .then((res) => {
        console.log("BALLOONS:", res.data);
        setBalloons(res.data);
      })
      .catch(() => {
        console.log("No balloons yet");
      });
  }, []);

  // Resize
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        setStageSize({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, []);

  // Fit image
  useEffect(() => {
    if (!image) return;

    const scaleX = stageSize.width / image.width;
    const scaleY = stageSize.height / image.height;

    setScale(Math.min(scaleX, scaleY));
  }, [image, stageSize]);

  // Center image
  const offsetX = image ? (stageSize.width - image.width * scale) / 2 : 0;

  const offsetY = image ? (stageSize.height - image.height * scale) / 2 : 0;

  const handleStageClick = (e: any) => {
    if (tool !== "add" || !image) return;

    const stage = e.target.getStage();
    const pointer = stage.getPointerPosition();

    const x = (pointer.x - offsetX) / (image.width * scale);
    const y = (pointer.y - offsetY) / (image.height * scale);

    if (x < 0 || y < 0 || x > 1 || y > 1) return;

    createBalloon({
      drawing_id: drawingId,
      page_number: page,
      x_pct: x,
      y_pct: y,
      balloon_type: "note",
    }).then((res) => {
      setBalloons([...balloons, res.data]);
    });
  };

  const handleWheel = (e: any) => {
  e.evt.preventDefault();

  const scaleBy = 1.05;
  const newZoom = e.evt.deltaY > 0 ? zoom / scaleBy : zoom * scaleBy;

  // limit zoom
  if (newZoom < 0.5 || newZoom > 5) return;

  setZoom(newZoom);
};

  return (
    <div ref={containerRef} className="absolute inset-0 bg-gray-800">
      {/* 🔥 Debug loader */}
      {!image && <div className="text-white p-4">Loading image...</div>}

      <Stage
  width={stageSize.width}
  height={stageSize.height}
  onClick={handleStageClick}
  onWheel={handleWheel}
  draggable={tool === "pan"}
  x={stagePos.x}
  y={stagePos.y}
  onDragEnd={(e) => {
    setStagePos({
      x: e.target.x(),
      y: e.target.y(),
    });
  }}
>
        {/* IMAGE */}
        <Layer>
          {image && (
            <KonvaImage
  image={image}
  x={offsetX}
  y={offsetY}
  scaleX={scale * zoom}
  scaleY={scale * zoom}
/>
          )}
        </Layer>

        {/* BALLOONS */}
        <Layer>
          {image &&
            balloons.map((b: any) => (
              <Group
                key={b.id}
                x={offsetX + b.x_pct * image.width * scale * zoom}
                y={offsetY + b.y_pct * image.height * scale * zoom}
                draggable={tool === "select"}
                onClick={(e) => {
                  e.cancelBubble = true;
                  setSelectedBalloonId(b.id);
                }}
                onDragEnd={(e) => {
                  const pos = e.target.position();

                  const x = (pos.x - offsetX) / (image.width * scale * zoom);
                  const y = (pos.y - offsetY) / (image.height * scale * zoom);

                  updateBalloon(b.id, { x_pct: x, y_pct: y }).then((res) => {
                    setBalloons(
                      balloons.map((balloon) =>
                        balloon.id === b.id ? res.data : balloon,
                      ),
                    );
                  });
                }}
              >
                <Circle
                  radius={14}
                  stroke={selectedBalloonId === b.id ? "red" : "cyan"}
                  strokeWidth={2}
                />

                <Text
                  text={String(b.balloon_number)}
                  fill="white"
                  fontSize={12}
                  offsetX={4}
                  offsetY={6}
                />
              </Group>
            ))}
        </Layer>
      </Stage>
    </div>
  );
};

export default DrawingCanvas;

// const DrawingCanvas = () => {
//   return (
//     <div className="w-full h-full bg-red-500 flex items-center justify-center text-white">
//       Canvas Loaded
//     </div>
//   );
// };

// export default DrawingCanvas;
