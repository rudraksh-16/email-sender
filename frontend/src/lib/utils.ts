import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function fmtDate(iso?: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

/**
 * Save CSV text to a file.
 *
 * In the desktop shell (pywebview / WKWebView) the `<a download>` trick just
 * navigates the window to the blob and unmounts the app, so we call the native
 * save dialog exposed by the Python side. In a plain browser (dev) we fall back
 * to the blob-anchor download.
 */
export async function downloadCsv(filename: string, csv: string): Promise<void> {
  const api = (window as unknown as { pywebview?: { api?: { save_csv?: (f: string, c: string) => Promise<unknown> } } })
    .pywebview?.api;
  if (api?.save_csv) {
    await api.save_csv(filename, csv);
    return;
  }
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function fmtBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export const STATUS_COLOR: Record<string, string> = {
  queued: "bg-gray-100 text-gray-700",
  running: "bg-blue-100 text-blue-700",
  done: "bg-green-100 text-green-700",
  sent: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  cancelled: "bg-gray-200 text-gray-500",
  sending: "bg-yellow-100 text-yellow-700",
  retrying: "bg-orange-100 text-orange-700",
};
