import type { KonvaEventObject } from "konva/lib/Node";
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

const DRAWING_ID = 1;
const PAGE_NUMBER = 1;
const MIN_ZOOM = 0.5;
const MAX_ZOOM = 5;

const DrawingCanvas = () => {
  const containerRef = useRef<HTMLDivElement>(null);

  const [stageSize, setStageSize] = useState({
    width: 800,
    height: 600,
  });

  const [imageUrl, setImageUrl] = useState("");
  const [image] = useImage(imageUrl);

  const [fitScale, setFitScale] = useState(1);

  const {
    balloons,
    setBalloons,
    tool,
    selectedBalloonId,
    setSelectedBalloonId,
    zoom,
    setZoom,
    stagePos,
    setStagePos,
  } = useStore();

  useEffect(() => {
    const url = getDrawingPageUrl(DRAWING_ID, PAGE_NUMBER);
    setImageUrl(url);

    getBalloons(DRAWING_ID, PAGE_NUMBER)
      .then((res) => {
        setBalloons(res.data);
      })
      .catch((err) => {
        console.log("No balloons yet or failed to load balloons:", err);
      });
  }, [setBalloons]);

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

  useEffect(() => {
    if (!image) return;

    const scaleX = stageSize.width / image.width;
    const scaleY = stageSize.height / image.height;
    setFitScale(Math.min(scaleX, scaleY));
  }, [image, stageSize]);

  const baseX = image ? (stageSize.width - image.width * fitScale) / 2 : 0;
  const baseY = image ? (stageSize.height - image.height * fitScale) / 2 : 0;

  const contentScale = fitScale * zoom;
  const contentX = baseX + stagePos.x;
  const contentY = baseY + stagePos.y;

  const handleWheel = (e: KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault();
    if (!image) return;

    const oldZoom = zoom;
    const zoomFactor = 1.08;
    const direction = e.evt.deltaY > 0 ? -1 : 1;

    const newZoom =
      direction > 0
        ? Math.min(MAX_ZOOM, oldZoom * zoomFactor)
        : Math.max(MIN_ZOOM, oldZoom / zoomFactor);

    const oldScale = fitScale * oldZoom;
    const newScale = fitScale * newZoom;

    // Zoom around the center of the visible canvas
    const centerX = stageSize.width / 2;
    const centerY = stageSize.height / 2;

    const pointTo = {
      x: (centerX - contentX) / oldScale,
      y: (centerY - contentY) / oldScale,
    };

    const newContentX = centerX - pointTo.x * newScale;
    const newContentY = centerY - pointTo.y * newScale;

    setZoom(newZoom);
    setStagePos({
      x: newContentX - baseX,
      y: newContentY - baseY,
    });
  };

  const handleStageClick = (e: any) => {
  if (tool !== "add" || !image) return;

  const stage = e.target.getStage();
  const pointer = stage.getPointerPosition();
  if (!pointer) return;

  // ✅ FIXED (remove stagePos subtraction)
  const x =
    (pointer.x - baseX) / (image.width * fitScale * zoom);

  const y =
    (pointer.y - baseY) / (image.height * fitScale * zoom);

  console.log("CLICK FIXED:", { x, y });

  if (x < 0 || y < 0 || x > 1 || y > 1) return;

  createBalloon({
    drawing_id: DRAWING_ID,
    page_number: PAGE_NUMBER,
    x_pct: x,
    y_pct: y,
    balloon_type: "note",
  })
    .then((res) => {
      // ✅ FIX stale state
      setBalloons([...balloons, res.data]);
    })
    .catch((err) => {
      console.log("Create balloon failed:", err.response?.data || err);
    });
};

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 bg-gray-800 overflow-hidden"
    >
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
        <Layer>
          {image && (
            <KonvaImage
              image={image}
              x={baseX}
              y={baseY}
              scaleX={contentScale}
              scaleY={contentScale}
            />
          )}
        </Layer>

        <Layer>
          {image &&
            balloons.map((b: any) => (
              <Group
                key={b.id}
                x={baseX + b.x_pct * image.width * contentScale}
                y={baseY + b.y_pct * image.height * contentScale}
                draggable={tool === "select"}
                onClick={(e) => {
                  e.cancelBubble = true;
                  setSelectedBalloonId(b.id);
                }}
                onDragEnd={(e) => {
                  const pos = e.target.position();

                  const x =
                    (pos.x - baseX - stagePos.x) / (image.width * contentScale);

                  const y =
                    (pos.y - baseY - stagePos.y) /
                    (image.height * contentScale);

                  updateBalloon(b.id, { x_pct: x, y_pct: y })
                    .then((res) => {
                      setBalloons(
                        balloons.map((balloon) =>
                          balloon.id === b.id ? res.data : balloon,
                        ),
                      );
                    })
                    .catch((err) => {
                      console.log("Update balloon failed:", err);
                    });
                }}
              >
                <Circle
                  radius={selectedBalloonId === b.id ? 19 : 16}
                  stroke={selectedBalloonId === b.id ? "red" : "blue"}
                  strokeWidth={3}
                  fill={selectedBalloonId === b.id ? "red" : "blue"}
                  shadowColor={
                    selectedBalloonId === b.id ? "#f14313" : "#0b758d"
                  }
                  shadowBlur={selectedBalloonId === b.id ? 10 : 9}
                  shadowOpacity={0.5}
                  shadowOffset={{ x: 0, y: 0 }}
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
