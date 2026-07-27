import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Eye, Plus, Trash2, Download } from "lucide-react";
import Papa from "papaparse";
import { smtpApi } from "@/api/smtp";
import { templatesApi } from "@/api/templates";
import { campaignsApi } from "@/api/campaigns";
import { verifyApi, type VerifyReport } from "@/api/verify";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RichTextEditor } from "@/components/editor/RichTextEditor";
import { AttachmentDropzone } from "@/components/AttachmentDropzone";
import { Modal } from "@/components/ui/Modal";
import { downloadCsv } from "@/lib/utils";

type Row = Record<string, string>;

const DEFAULT_CSV = "email,first_name,last_name\n";

export function BulkSendPage() {
  const navigate = useNavigate();
  const { data: accounts } = useQuery({ queryKey: ["smtp-accounts"], queryFn: smtpApi.list });
  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: templatesApi.list });

  const [name, setName] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [accountId, setAccountId] = useState("");
  const [templateId, setTemplateId] = useState("");
  const [useTemplate, setUseTemplate] = useState(false);
  const [rows, setRows] = useState<Row[]>([]);
  const [csvText, setCsvText] = useState(DEFAULT_CSV);
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);
  const [previewModal, setPreviewModal] = useState(false);
  const [report, setReport] = useState<VerifyReport | null>(null);
  const [excluded, setExcluded] = useState<Set<number>>(new Set());

  const verify = useMutation({
    mutationFn: () => verifyApi.csv(csvText),
    onSuccess: (r) => {
      setReport(r);
      // Drop bad rows by default; user can re-include below.
      setExcluded(
        new Set(r.rows.filter((row) => row.verdict !== "valid").map((row) => row.index)),
      );
    },
  });

  const toggleExcluded = (index: number) =>
    setExcluded((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });

  const loadTemplate = (id: string) => {
    const t = templates?.find((t) => t.id === id);
    if (t) {
      setSubject(t.subject);
      setBodyHtml(t.body_html);
    }
    setTemplateId(id);
  };

  const handleToggleTemplate = (checked: boolean) => {
    setUseTemplate(checked);
    if (!checked) {
      setTemplateId("");
      setSubject("");
      setBodyHtml("");
    }
  };

  const handleCsvChange = (text: string) => {
    setCsvText(text);
    const result = Papa.parse<Row>(text.trim(), { header: true, skipEmptyLines: true });
    setRows(result.data.filter((r) => r.email));
    // List changed — stale verification no longer applies.
    setReport(null);
    setExcluded(new Set());
  };

  const keptRows = rows.filter((_, i) => !excluded.has(i));

  const create = useMutation({
    mutationFn: () =>
      campaignsApi.create({
        name,
        subject,
        body_html: bodyHtml,
        smtp_account_id: accountId,
        template_id: templateId || undefined,
        recipients: keptRows.map((r) => ({
          email: r.email,
          data: Object.fromEntries(Object.entries(r).filter(([k]) => k !== "email")),
        })),
        attachment_ids: attachmentIds,
      }),
    onSuccess: (campaign) => navigate(`/campaigns/${campaign.id}`),
  });

  const columns =
    rows.length > 0
      ? Object.keys(rows[0])
      : Papa.parse<Row>(csvText.trim(), { header: true }).meta.fields ?? ["email"];

  const verdictByIndex = new Map(report?.rows.map((r) => [r.index, r]) ?? []);

  const syncCsv = (next: Row[]) => setCsvText(Papa.unparse({ fields: columns, data: next }));

  const updateCell = (i: number, key: string, value: string) => {
    const next = rows.map((r, idx) => (idx === i ? { ...r, [key]: value } : r));
    setRows(next);
    syncCsv(next);
    setReport(null); // emails may have changed — old verdicts no longer apply
  };

  const deleteRow = (i: number) => {
    const next = rows.filter((_, idx) => idx !== i);
    setRows(next);
    syncCsv(next);
    setReport(null);
    setExcluded(new Set()); // row indices shifted
  };

  const addRow = () => {
    const blank = Object.fromEntries(columns.map((c) => [c, ""])) as Row;
    const next = [...rows, blank];
    setRows(next);
    syncCsv(next);
    setReport(null);
  };

  const exportCsv = () =>
    downloadCsv(`${name.trim() || "recipients"}-cleaned.csv`, Papa.unparse({ fields: columns, data: keptRows }));

  const previewRow = rows[0] ?? {};
  const canSubmit = keptRows.length > 0 && (!useTemplate || !!templateId);

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

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm font-medium text-gray-700">Template</label>
              <label className="flex items-center gap-1.5 text-xs text-gray-500 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={useTemplate}
                  onChange={(e) => handleToggleTemplate(e.target.checked)}
                  className="rounded"
                />
                Use template
              </label>
            </div>
            <Select
              value={templateId}
              onChange={(e) => loadTemplate(e.target.value)}
              disabled={!useTemplate}
            >
              <option value="">Select template…</option>
              {templates?.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </Select>
          </div>
        </div>

        {useTemplate && subject && (
          <div className="rounded-lg bg-blue-50 border border-blue-100 px-4 py-3 text-sm text-gray-700">
            <span className="font-medium text-gray-500 text-xs uppercase tracking-wide mr-2">Subject</span>
            {subject}
          </div>
        )}

        {useTemplate && !templateId && (
          <p className="text-xs text-amber-600 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
            Select a template above — subject and body will be loaded from it.
          </p>
        )}

        {!useTemplate && (
          <>
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
          </>
        )}

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm font-medium text-gray-700">
              Recipients
              {rows.length > 0 && (
                <span className="ml-2 text-xs font-normal text-gray-500">
                  {rows.length} row{rows.length !== 1 ? "s" : ""} · columns: {columns.join(", ")}
                </span>
              )}
            </label>
            <div className="flex items-center gap-1">
              {rows.length > 0 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  loading={verify.isPending}
                  onClick={() => verify.mutate()}
                >
                  Verify list
                </Button>
              )}
              {rows.length > 0 && (
                <Button type="button" variant="ghost" size="sm" onClick={() => setPreviewModal(true)}>
                  <Eye size={16} /> Preview row 1
                </Button>
              )}
            </div>
          </div>
          <textarea
            value={csvText}
            onChange={(e) => handleCsvChange(e.target.value)}
            spellCheck={false}
            rows={8}
            className="w-full font-mono text-sm border border-gray-200 rounded-lg p-3 resize-y focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-300"
            placeholder={DEFAULT_CSV}
          />
          <p className="text-xs text-gray-400 mt-1">
            Paste CSV rows below the header. <code className="bg-gray-100 px-1 rounded">email</code> column required.
            Add any extra columns to use as merge fields (e.g. <code className="bg-gray-100 px-1 rounded">{"{{first_name}}"}</code>).
          </p>

          {verify.isError && (
            <p className="text-sm text-red-600 mt-2">{String(verify.error)}</p>
          )}

          {rows.length > 0 && (
            <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
              {report && (
                <div className="flex flex-wrap gap-3 px-3 py-2 bg-gray-50 text-xs border-b border-gray-200">
                  <span className="text-green-700">{report.summary.valid} valid</span>
                  <span className="text-red-700">{report.summary.invalid} invalid</span>
                  <span className="text-amber-700">{report.summary.duplicate} duplicate</span>
                  <span className="ml-auto text-gray-500">{keptRows.length} will be sent</span>
                </div>
              )}
              <div className="max-h-72 overflow-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-white shadow-[0_1px_0_rgba(0,0,0,0.06)]">
                    <tr className="text-left text-xs text-gray-500">
                      <th className="px-2 py-2 w-8" />
                      {columns.map((c) => (
                        <th key={c} className="px-2 py-2 font-medium whitespace-nowrap">{c}</th>
                      ))}
                      {report && <th className="px-2 py-2 font-medium">status</th>}
                      <th className="px-2 py-2 w-8" />
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((row, i) => {
                      const kept = !excluded.has(i);
                      const v = verdictByIndex.get(i);
                      const color =
                        !v
                          ? ""
                          : v.verdict === "valid"
                            ? "text-green-700"
                            : v.verdict === "duplicate"
                              ? "text-amber-700"
                              : "text-red-700";
                      return (
                        <tr key={i} className={`border-t border-gray-50 ${kept ? "" : "opacity-40"}`}>
                          <td className="px-2 py-1 align-middle">
                            <input
                              type="checkbox"
                              checked={kept}
                              onChange={() => toggleExcluded(i)}
                              className="rounded"
                            />
                          </td>
                          {columns.map((c) => (
                            <td key={c} className="px-1 py-1">
                              <input
                                value={row[c] ?? ""}
                                onChange={(e) => updateCell(i, c, e.target.value)}
                                spellCheck={false}
                                className="w-full min-w-[8rem] font-mono text-xs bg-transparent border border-transparent hover:border-gray-200 focus:border-blue-400 focus:ring-1 focus:ring-blue-400 rounded px-1.5 py-1 focus:outline-none"
                              />
                            </td>
                          ))}
                          {report && (
                            <td className="px-2 py-1 text-xs whitespace-nowrap">
                              <span className={color}>{v?.verdict ?? "—"}</span>
                              {v?.reason && (
                                <span className="text-gray-400 ml-1" title={v.reason}>ⓘ</span>
                              )}
                            </td>
                          )}
                          <td className="px-2 py-1 text-right">
                            <button
                              type="button"
                              onClick={() => deleteRow(i)}
                              className="text-gray-400 hover:text-red-600"
                              title="Remove recipient"
                            >
                              <Trash2 size={14} />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-1 px-3 py-2 bg-gray-50 border-t border-gray-200">
                <Button type="button" variant="ghost" size="sm" onClick={addRow}>
                  <Plus size={14} /> Add recipient
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={exportCsv}>
                  <Download size={14} /> Export CSV ({keptRows.length})
                </Button>
              </div>
            </div>
          )}

          <p className="text-xs text-gray-400 mt-2">
            Verification checks syntax + domain (MX). It can&rsquo;t guarantee a Gmail/Outlook mailbox
            exists — those still need a test send — but it removes typos and dead domains.
          </p>
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Attachments</label>
          <AttachmentDropzone onChange={setAttachmentIds} />
        </div>

        {create.isError && <p className="text-sm text-red-600">{String(create.error)}</p>}

        <div className="flex justify-end">
          <Button type="submit" loading={create.isPending} disabled={!canSubmit}>
            {keptRows.length > 0 ? `Send to ${keptRows.length} recipient${keptRows.length !== 1 ? "s" : ""}` : "Send"}
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
