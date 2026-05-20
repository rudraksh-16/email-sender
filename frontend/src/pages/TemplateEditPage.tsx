import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { templatesApi } from "@/api/templates";
import { smtpApi } from "@/api/smtp";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RichTextEditor } from "@/components/editor/RichTextEditor";
import { Modal } from "@/components/ui/Modal";

export function TemplateEditPage() {
  const { id } = useParams<{ id: string }>();
  const isNew = !id;
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { data: existing } = useQuery({
    queryKey: ["templates", id],
    queryFn: () => templatesApi.get(id!),
    enabled: !isNew,
  });
  const { data: accounts } = useQuery({ queryKey: ["smtp-accounts"], queryFn: smtpApi.list });

  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [accountId, setAccountId] = useState("");
  const [previewModal, setPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState("{}");
  const [previewResult, setPreviewResult] = useState<{ subject: string; body_html: string } | null>(null);

  useEffect(() => {
    if (existing) {
      setName(existing.name);
      setSubject(existing.subject);
      setBodyHtml(existing.body_html);
      setAccountId(existing.default_smtp_account_id ?? "");
    }
  }, [existing]);

  const save = useMutation({
    mutationFn: (data: object) =>
      isNew ? templatesApi.create(data) : templatesApi.update(id!, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["templates"] });
      navigate("/templates");
    },
  });

  const preview = useMutation({
    mutationFn: (data: Record<string, string>) => templatesApi.preview(id!, data),
    onSuccess: (r) => setPreviewResult(r),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    save.mutate({
      name,
      subject,
      body_html: bodyHtml,
      default_smtp_account_id: accountId || undefined,
    });
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">
        {isNew ? "New template" : "Edit template"}
      </h1>
      <form onSubmit={handleSubmit} className="space-y-4 bg-white border border-gray-200 rounded-xl p-6">
        <Input label="Template name" value={name} onChange={(e) => setName(e.target.value)} required />
        <Select
          label="Default SMTP account (optional)"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
        >
          <option value="">None</option>
          {accounts?.map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </Select>
        <Input label="Subject (supports {{placeholders}})" value={subject} onChange={(e) => setSubject(e.target.value)} required />
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Body</label>
          <RichTextEditor value={bodyHtml} onChange={setBodyHtml} />
        </div>
        {save.isError && <p className="text-xs text-red-600">{String(save.error)}</p>}
        <div className="flex justify-end gap-2">
          {!isNew && (
            <Button type="button" variant="secondary" onClick={() => setPreviewModal(true)}>
              Preview
            </Button>
          )}
          <Button type="submit" loading={save.isPending}>Save template</Button>
        </div>
      </form>

      <Modal open={previewModal} onClose={() => setPreviewModal(false)} title="Preview template" className="max-w-2xl">
        <div className="space-y-3">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Sample data (JSON)</label>
            <textarea
              value={previewData}
              onChange={(e) => setPreviewData(e.target.value)}
              className="w-full border border-gray-300 rounded-md p-2 text-xs font-mono"
              rows={4}
            />
          </div>
          <Button
            size="sm"
            loading={preview.isPending}
            onClick={() => {
              try { preview.mutate(JSON.parse(previewData)); }
              catch { alert("Invalid JSON"); }
            }}
          >
            Render
          </Button>
          {preview.isError && <p className="text-xs text-red-600">{String(preview.error)}</p>}
          {previewResult && (
            <div className="mt-3 space-y-2">
              <p className="text-sm font-medium text-gray-700">Subject: <span className="font-normal">{previewResult.subject}</span></p>
              <div
                className="border border-gray-200 rounded p-3 prose prose-sm max-w-none text-sm"
                dangerouslySetInnerHTML={{ __html: previewResult.body_html }}
              />
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}
