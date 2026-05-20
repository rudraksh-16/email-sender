import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Upload, Eye } from "lucide-react";
import Papa from "papaparse";
import { smtpApi } from "@/api/smtp";
import { templatesApi } from "@/api/templates";
import { campaignsApi } from "@/api/campaigns";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RichTextEditor } from "@/components/editor/RichTextEditor";
import { AttachmentDropzone } from "@/components/AttachmentDropzone";
import { Modal } from "@/components/ui/Modal";

type Row = Record<string, string>;

export function BulkSendPage() {
  const navigate = useNavigate();
  const { data: accounts } = useQuery({ queryKey: ["smtp-accounts"], queryFn: smtpApi.list });
  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: templatesApi.list });

  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [accountId, setAccountId] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [rows, setRows] = useState<Row[]>([]);
  const [csvFileName, setCsvFileName] = useState("");
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [previewModal, setPreviewModal] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const loadTemplate = (id: string) => {
    const t = templates?.find((t) => t.id === id);
    if (t) {
      setSubject(t.subject);
      setBodyHtml(t.body_html);
    }
    setTemplateId(id);
  };

  const handleCsv = (file: File) => {
    setCsvFileName(file.name);
    Papa.parse<Row>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (result) => setRows(result.data),
    });
  };

  const create = useMutation({
    mutationFn: () =>
      campaignsApi.create({
        name,
        subject,
        body_html: bodyHtml,
        smtp_account_id: accountId,
        template_id: templateId || undefined,
        recipients: rows.map((r) => ({
          email: r.email,
          data: Object.fromEntries(Object.entries(r).filter(([k]) => k !== "email")),
        })),
        attachment_ids: attachmentIds,
      }),
    onSuccess: (campaign) => navigate(`/campaigns/${campaign.id}`),
  });

  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];
  const previewRow = rows[0] ?? {};

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Bulk Send</h1>
      <form
        onSubmit={(e) => { e.preventDefault(); create.mutate(); }}
        className="space-y-5 bg-white border border-gray-200 rounded-xl p-6"
      >
        <Input label="Campaign name" value={name} onChange={(e) => setName(e.target.value)} required />

        <div className="grid grid-cols-2 gap-4">
          <Select label="SMTP account" value={accountId} onChange={(e) => setAccountId(e.target.value)} required>
            <option value="">Select account…</option>
            {accounts?.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}
          </Select>
          <Select
            label="Template (optional)"
            value={templateId}
            onChange={(e) => loadTemplate(e.target.value)}
          >
            <option value="">None — compose below</option>
            {templates?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
        </div>

        <Input
          label="Subject (use {{column}} for merge fields)"
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          required
        />

        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Body</label>
          <RichTextEditor value={bodyHtml} onChange={setBodyHtml} placeholder="Use {{first_name}} etc. for merge fields…" />
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">
            Recipients CSV
            {csvFileName && <span className="ml-2 text-xs text-gray-500">({csvFileName}, {rows.length} rows)</span>}
          </label>
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => fileRef.current?.click()}
            >
              <Upload size={16} /> Upload CSV
            </Button>
            {rows.length > 0 && (
              <Button type="button" variant="ghost" size="sm" onClick={() => setPreviewModal(true)}>
                <Eye size={16} /> Preview row 1
              </Button>
            )}
            <input
              ref={fileRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) handleCsv(f); }}
            />
          </div>
          {rows.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Columns: {columns.join(", ")}
            </p>
          )}
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Attachments</label>
          <AttachmentDropzone onChange={setAttachmentIds} />
        </div>

        {create.isError && <p className="text-sm text-red-600">{String(create.error)}</p>}

        <div className="flex justify-end">
          <Button type="submit" loading={create.isPending} disabled={!rows.length}>
            Send to {rows.length} recipients
          </Button>
        </div>
      </form>

      <Modal open={previewModal} onClose={() => setPreviewModal(false)} title="Preview — row 1" className="max-w-xl">
        <div className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(previewRow).map(([k, v]) => (
              <div key={k} className="bg-gray-50 rounded p-2">
                <p className="text-xs text-gray-500 font-medium">{k}</p>
                <p className="text-gray-900 truncate">{v}</p>
              </div>
            ))}
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1 font-medium">Subject (rendered)</p>
            <p>{subject.replace(/{{(\w+)}}/g, (_, k) => previewRow[k] ?? `{{${k}}}`)}</p>
          </div>
        </div>
      </Modal>
    </div>
  );
}
