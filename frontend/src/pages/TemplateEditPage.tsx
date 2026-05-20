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

function extractPlaceholders(subject: string, bodyHtml: string): string[] {
  const matches = [...subject.matchAll(/{{(\w+)}}/g), ...bodyHtml.matchAll(/{{(\w+)}}/g)];
  return [...new Set(matches.map((m) => m[1]))];
}

function PreviewModalBody({
  subject, bodyHtml, fields, onFieldChange, onRender, isPending, isError, error, result,
}: {
  subject: string;
  bodyHtml: string;
  fields: Record<string, string>;
  onFieldChange: (key: string, value: string) => void;
  onRender: () => void;
  isPending: boolean;
  isError: boolean;
  error?: string;
  result: { subject: string; body_html: string } | null;
}) {
  const placeholders = extractPlaceholders(subject, bodyHtml);
  return (
    <div className="space-y-4">
      {placeholders.length > 0 ? (
        <div className="grid grid-cols-2 gap-3">
          {placeholders.map((key) => (
            <div key={key}>
              <label className="text-xs font-medium text-gray-500 block mb-1">{`{{${key}}}`}</label>
              <input
                type="text"
                value={fields[key] ?? ""}
                onChange={(e) => onFieldChange(key, e.target.value)}
                placeholder={key}
                className="w-full border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-gray-500">No <code>{"{{placeholders}}"}</code> found in subject or body.</p>
      )}
      <Button size="sm" loading={isPending} onClick={onRender}>Render</Button>
      {isError && <p className="text-xs text-red-600">{error}</p>}
      {result && (
        <div className="mt-1 space-y-2">
          <p className="text-sm font-medium text-gray-700">Subject: <span className="font-normal">{result.subject}</span></p>
          <div
            className="border border-gray-200 rounded p-3 prose prose-sm max-w-none text-sm"
            dangerouslySetInnerHTML={{ __html: result.body_html }}
          />
        </div>
      )}
    </div>
  );
}

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
  const [previewFields, setPreviewFields] = useState<Record<string, string>>({});
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

      <Modal open={previewModal} onClose={() => { setPreviewModal(false); setPreviewResult(null); }} title="Preview template" className="max-w-2xl">
        <PreviewModalBody
          subject={subject}
          bodyHtml={bodyHtml}
          fields={previewFields}
          onFieldChange={(k, v) => setPreviewFields((prev) => ({ ...prev, [k]: v }))}
          onRender={() => preview.mutate(previewFields)}
          isPending={preview.isPending}
          isError={preview.isError}
          error={preview.isError ? String(preview.error) : undefined}
          result={previewResult}
        />
      </Modal>
    </div>
  );
}
