"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, FileCode, ArrowRight, Check, Loader2 } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { uploadModel, type Model } from "@/lib/api";

const frameworks = [
  { id: "pytorch", label: "PyTorch", ext: ".pt" },
  { id: "onnx", label: "ONNX", ext: ".onnx" },
  { id: "tensorflow", label: "TensorFlow", ext: ".pb, .h5" },
] as const;

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [framework, setFramework] = useState<string>("pytorch");
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadedModel, setUploadedModel] = useState<Model | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const model = await uploadModel(file, framework);
      setUploadedModel(model);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  if (uploadedModel) {
    return (
      <div className="min-h-full flex items-center justify-center p-8">
        <div className="max-w-md w-full text-center space-y-8">
          <div className="w-16 h-16 mx-auto rounded-full border border-[#10b981]/30 bg-[#10b981]/5 flex items-center justify-center">
            <svg
              className="w-7 h-7"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#10b981"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <polyline points="20 6 9 17 4 12" className="check-draw" />
            </svg>
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-light tracking-tight text-[#0f0f0f]">
              Model Uploaded
            </h1>
            <p className="text-sm text-[#1a1a2e]/50 font-light">
              Your model is ready for optimization.
            </p>
          </div>
          <div className="border border-[#e8e4e1] rounded-lg p-6 text-left space-y-3 summary-animate">
            <div className="flex justify-between items-baseline">
              <span className="text-xs uppercase tracking-widest text-[#1a1a2e]/40">Name</span>
              <span className="text-sm text-[#0f0f0f]">{uploadedModel.name}</span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-xs uppercase tracking-widest text-[#1a1a2e]/40">Framework</span>
              <span className="text-sm text-[#0f0f0f]">{uploadedModel.framework}</span>
            </div>
            <div className="flex justify-between items-baseline">
              <span className="text-xs uppercase tracking-widest text-[#1a1a2e]/40">Size</span>
              <span className="text-sm text-[#0f0f0f]">{uploadedModel.size_mb.toFixed(1)} MB</span>
            </div>
          </div>
          <Link
            href={`/optimize?modelId=${uploadedModel.id}`}
            className="inline-flex items-center gap-2 px-8 py-3 text-sm tracking-wide text-[#fafaf9] bg-[#0f0f0f] hover:bg-[#1a1a2e] transition-colors duration-200 rounded btn-pulse-glow"
          >
            Continue
            <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-full p-8 md:p-16 max-w-3xl mx-auto">
      <div className="space-y-2 mb-12">
        <h1 className="text-3xl font-light tracking-tight text-[#0f0f0f]">
          Upload
        </h1>
        <p className="text-sm text-[#1a1a2e]/50 font-light">
          Provide your model for hardware-aware optimization.
        </p>
      </div>

      <div
        className={cn(
          "relative border border-dashed rounded-lg p-16 text-center transition-colors duration-200 cursor-pointer",
          dragActive
            ? "border-[#c0392b]/40 bg-[#c0392b]/[0.02]"
            : file
            ? "border-[#0f0f0f]/20"
            : "drag-zone-idle hover:border-[#1a1a2e]/20"
        )}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".pt,.onnx,.pb,.h5"
          onChange={handleFileChange}
        />
        {file ? (
          <div className="space-y-3">
            <FileCode className="w-8 h-8 mx-auto text-[#0f0f0f]/40" strokeWidth={1} />
            <div>
              <p className="text-sm font-medium text-[#0f0f0f]">{file.name}</p>
              <p className="text-xs text-[#1a1a2e]/40 mt-1">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
            <p className="text-xs text-[#1a1a2e]/30">Click to replace</p>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className="w-8 h-8 mx-auto text-[#1a1a2e]/20" strokeWidth={1} />
            <div>
              <p className="text-sm text-[#0f0f0f]">
                Drag & drop your model file
              </p>
              <p className="text-xs text-[#1a1a2e]/40 mt-1">
                or click to browse
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-12 space-y-4">
        <label className="text-xs uppercase tracking-widest text-[#1a1a2e]/40 block">
          Framework
        </label>
        <div className="grid grid-cols-3 gap-3">
          {frameworks.map((fw, i) => (
            <button
              key={fw.id}
              onClick={() => setFramework(fw.id)}
              className={cn(
                "p-4 rounded-lg border text-left transition-all duration-200 framework-card",
                framework === fw.id
                  ? "border-[#0f0f0f]/20 bg-[#0f0f0f]/[0.02]"
                  : "border-[#e8e4e1] hover:border-[#1a1a2e]/15"
              )}
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <span className="text-sm font-medium text-[#0f0f0f] block">{fw.label}</span>
              <span className="text-xs text-[#1a1a2e]/30 mt-1 block">{fw.ext}</span>
            </button>
          ))}
        </div>
      </div>

      {error && (
        <p className="mt-4 text-xs text-[#c0392b]">{error}</p>
      )}

      <div className="mt-12 flex justify-end">
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className={cn(
            "inline-flex items-center gap-2 px-8 py-3 text-sm tracking-wide rounded transition-colors duration-200",
            file && !uploading
              ? "text-[#fafaf9] bg-[#0f0f0f] hover:bg-[#1a1a2e]"
              : "text-[#1a1a2e]/30 bg-[#e8e4e1]/50 cursor-not-allowed"
          )}
        >
          {uploading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" strokeWidth={1.5} />
              Uploading...
            </>
          ) : (
            <>
              Upload Model
              <ArrowRight className="w-4 h-4" strokeWidth={1.5} />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
