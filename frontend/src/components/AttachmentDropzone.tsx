import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { Paperclip, X } from "lucide-react";
import { attachmentsApi } from "@/api/campaigns";
import { fmtBytes, cn } from "@/lib/utils";

interface UploadedAttachment {
  id: string;
  filename: string;
  size_bytes: number;
}

interface AttachmentDropzoneProps {
  onChange: (ids: string[]) => void;
}

export function AttachmentDropzone({ onChange }: AttachmentDropzoneProps) {
  const [attachments, setAttachments] = useState<UploadedAttachment[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string>();

  const onDrop = useCallback(
    async (files: File[]) => {
      setUploading(true);
      setError(undefined);
      const newItems: UploadedAttachment[] = [];
      for (const file of files) {
        try {
          const result = await attachmentsApi.upload(file);
          newItems.push({ id: result.id, filename: result.filename, size_bytes: result.size_bytes });
        } catch (e: unknown) {
          setError(e instanceof Error ? e.message : "Upload failed");
        }
      }
      const updated = [...attachments, ...newItems];
      setAttachments(updated);
      onChange(updated.map((a) => a.id));
      setUploading(false);
    },
    [attachments, onChange],
  );

  const remove = async (id: string) => {
    await attachmentsApi.delete(id).catch(() => {});
    const updated = attachments.filter((a) => a.id !== id);
    setAttachments(updated);
    onChange(updated.map((a) => a.id));
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop });

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors",
          isDragActive ? "border-blue-400 bg-blue-50" : "border-gray-300 hover:border-gray-400",
        )}
      >
        <input {...getInputProps()} />
        <Paperclip className="mx-auto mb-1 text-gray-400" size={20} />
        <p className="text-sm text-gray-500">
          {uploading ? "Uploading…" : "Drop files or click to attach"}
        </p>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      {attachments.length > 0 && (
        <ul className="space-y-1">
          {attachments.map((a) => (
            <li key={a.id} className="flex items-center justify-between text-sm bg-gray-50 rounded px-3 py-1.5">
              <span className="truncate text-gray-700">{a.filename}</span>
              <span className="text-gray-400 ml-2 shrink-0">{fmtBytes(a.size_bytes)}</span>
              <button onClick={() => remove(a.id)} className="ml-2 text-gray-400 hover:text-red-500">
                <X size={14} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
