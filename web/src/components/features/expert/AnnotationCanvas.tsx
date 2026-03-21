/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Expert review annotation canvas (draw corrections on analysis output). */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export interface Annotation {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label?: string;
}

export interface AnnotationCanvasProps {
  imageSrc: string;
  annotations: Annotation[];
  onAnnotationAdd: (annotation: Annotation) => void;
}

interface DrawState {
  startX: number;
  startY: number;
  currentX: number;
  currentY: number;
}

export function AnnotationCanvas({
  imageSrc,
  annotations,
  onAnnotationAdd,
}: AnnotationCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const [drawing, setDrawing] = useState<DrawState | null>(null);
  const [imageLoaded, setImageLoaded] = useState(false);

  /* Load the image */
  useEffect(() => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      imageRef.current = img;
      setImageLoaded(true);
    };
    img.src = imageSrc;
  }, [imageSrc]);

  /* Draw the canvas */
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    const img = imageRef.current;
    if (!canvas || !ctx || !img) return;

    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    /* Draw existing annotations */
    for (const ann of annotations) {
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 2;
      ctx.strokeRect(ann.x, ann.y, ann.width, ann.height);

      if (ann.label) {
        ctx.fillStyle = "rgba(16, 185, 129, 0.8)";
        ctx.font = "14px sans-serif";
        const textWidth = ctx.measureText(ann.label).width;
        ctx.fillRect(ann.x, ann.y - 20, textWidth + 8, 20);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(ann.label, ann.x + 4, ann.y - 6);
      }
    }

    /* Draw current selection box */
    if (drawing) {
      const x = Math.min(drawing.startX, drawing.currentX);
      const y = Math.min(drawing.startY, drawing.currentY);
      const w = Math.abs(drawing.currentX - drawing.startX);
      const h = Math.abs(drawing.currentY - drawing.startY);

      ctx.strokeStyle = "#f59e0b";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.strokeRect(x, y, w, h);
      ctx.setLineDash([]);

      ctx.fillStyle = "rgba(245, 158, 11, 0.1)";
      ctx.fillRect(x, y, w, h);
    }
  }, [annotations, drawing]);

  useEffect(() => {
    if (imageLoaded) draw();
  }, [imageLoaded, draw]);

  /* Convert mouse event to canvas coordinates */
  const toCanvasCoords = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const canvas = canvasRef.current;
      if (!canvas) return { x: 0, y: 0 };
      const rect = canvas.getBoundingClientRect();
      const scaleX = canvas.width / rect.width;
      const scaleY = canvas.height / rect.height;
      return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY,
      };
    },
    [],
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      const { x, y } = toCanvasCoords(e);
      setDrawing({ startX: x, startY: y, currentX: x, currentY: y });
    },
    [toCanvasCoords],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!drawing) return;
      const { x, y } = toCanvasCoords(e);
      setDrawing((prev) =>
        prev ? { ...prev, currentX: x, currentY: y } : null,
      );
    },
    [drawing, toCanvasCoords],
  );

  const handleMouseUp = useCallback(() => {
    if (!drawing) return;

    const x = Math.min(drawing.startX, drawing.currentX);
    const y = Math.min(drawing.startY, drawing.currentY);
    const width = Math.abs(drawing.currentX - drawing.startX);
    const height = Math.abs(drawing.currentY - drawing.startY);

    /* Ignore tiny accidental clicks (less than 10px in either dimension) */
    if (width > 10 && height > 10) {
      const annotation: Annotation = {
        id: `ann-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        x: Math.round(x),
        y: Math.round(y),
        width: Math.round(width),
        height: Math.round(height),
      };
      onAnnotationAdd(annotation);
    }

    setDrawing(null);
  }, [drawing, onAnnotationAdd]);

  return (
    <div className="relative overflow-auto rounded-lg border border-slate-200 bg-slate-900">
      {!imageLoaded && (
        <div className="flex h-64 items-center justify-center">
          <p className="text-sm text-slate-400">Görsel yükleniyor...</p>
        </div>
      )}
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className={`max-w-full cursor-crosshair ${imageLoaded ? "block" : "hidden"}`}
      />
      {imageLoaded && (
        <div className="absolute bottom-2 right-2 rounded bg-black/60 px-2 py-1 text-xs text-white">
          {annotations.length} alan isaretlendi
        </div>
      )}
    </div>
  );
}
