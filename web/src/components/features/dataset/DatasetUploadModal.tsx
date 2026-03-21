/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR: Pilot dataset upload modal component (after flight complete). */

"use client";

import { useCallback, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { getApiBaseUrl, getTokenFromCookie } from "@/lib/api";

export interface DatasetUploadModalProps {
  open: boolean;
  onClose: () => void;
  missionId: string;
}

type UploadStatus = "idle" | "uploading" | "success" | "error";

export function DatasetUploadModal({
  open,
  onClose,
  missionId,
}: DatasetUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const reset = useCallback(() => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
    setErrorMsg(null);
    setDragging(false);
  }, []);

  const handleClose = useCallback(() => {
    reset();
    onClose();
  }, [reset, onClose]);

  const handleFileSelect = useCallback((f: File) => {
    setFile(f);
    setStatus("idle");
    setErrorMsg(null);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFileSelect(droppedFile);
    },
    [handleFileSelect],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0];
      if (selected) handleFileSelect(selected);
    },
    [handleFileSelect],
  );

  const handleUpload = useCallback(async () => {
    if (!file) return;

    const token = getTokenFromCookie();
    if (!token) {
      setErrorMsg("Oturum bulunamadı. Lütfen tekrar giriş yapın.");
      setStatus("error");
      return;
    }

    setStatus("uploading");
    setProgress(0);
    setErrorMsg(null);

    try {
      const baseUrl = getApiBaseUrl();
      const formData = new FormData();
      formData.append("file", file);

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${baseUrl}/missions/${missionId}/dataset`);
      xhr.setRequestHeader("Authorization", `Bearer ${token}`);

      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          setProgress(Math.round((e.loaded / e.total) * 100));
        }
      });

      await new Promise<void>((resolve, reject) => {
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error(xhr.statusText || "Yükleme başarısız"));
          }
        };
        xhr.onerror = () => reject(new Error("Ağ hatası"));
        xhr.send(formData);
      });

      setStatus("success");
      setProgress(100);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Yükleme başarısız";
      setErrorMsg(msg);
      setStatus("error");
    }
  }, [file, missionId]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            Dataset Yükle
          </h2>
          <button
            type="button"
            onClick={handleClose}
            className="text-slate-400 hover:text-slate-600"
            aria-label="Kapat"
          >
            &times;
          </button>
        </div>

        <div className="mt-4">
          {/* Drop zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition ${
              dragging
                ? "border-emerald-400 bg-emerald-50"
                : "border-slate-300 bg-slate-50 hover:border-slate-400"
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={handleInputChange}
              accept=".zip,.tif,.tiff,.jpg,.jpeg,.png"
            />
            {file ? (
              <p className="text-sm font-medium text-slate-700">{file.name}</p>
            ) : (
              <>
                <p className="text-sm text-slate-500">
                  Dosyayı sürükleyip bırakın veya tıklayın
                </p>
                <p className="mt-1 text-xs text-slate-400">
                  ZIP, TIFF, JPG, PNG
                </p>
              </>
            )}
          </div>

          {/* Progress bar */}
          {status === "uploading" && (
            <div className="mt-4">
              <div className="h-2 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="mt-1 text-center text-xs text-slate-500">
                %{progress} yüklendi
              </p>
            </div>
          )}

          {/* Success */}
          {status === "success" && (
            <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
              Dosya başarıyla yüklendi.
            </div>
          )}

          {/* Error */}
          {status === "error" && errorMsg && (
            <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              {errorMsg}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" onClick={handleClose}>
            {status === "success" ? "Kapat" : "İptal"}
          </Button>
          {status !== "success" && (
            <Button
              onClick={handleUpload}
              disabled={!file || status === "uploading"}
            >
              {status === "uploading" ? "Yükleniyor..." : "Yükle"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
