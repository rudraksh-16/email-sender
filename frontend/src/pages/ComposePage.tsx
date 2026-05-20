import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { CheckCircle, XCircle } from "lucide-react";
import { smtpApi } from "@/api/smtp";
import { sendApi } from "@/api/campaigns";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { RichTextEditor } from "@/components/editor/RichTextEditor";
import { AttachmentDropzone } from "@/components/AttachmentDropzone";

export function ComposePage() {
  const { data: accounts } = useQuery({ queryKey: ["smtp-accounts"], queryFn: smtpApi.list });

  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [bodyHtml, setBodyHtml] = useState("");
  const [accountId, setAccountId] = useState("");
  const [replyTo, setReplyTo] = useState("");
  const [attachmentIds, setAttachmentIds] = useState<string[]>([]);

  const send = useMutation({ mutationFn: sendApi.single });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send.mutate({
      smtp_account_id: accountId,
      to,
      subject,
      body_html: bodyHtml,
      reply_to: replyTo || undefined,
      attachment_ids: attachmentIds,
    });
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Compose</h1>

      {send.isSuccess && (
        <div className={`flex items-center gap-2 rounded-lg p-3 mb-4 text-sm ${send.data.accepted ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
          {send.data.accepted ? <CheckCircle size={16} /> : <XCircle size={16} />}
          {send.data.accepted ? "Message sent successfully." : send.data.info ?? "Send failed."}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 bg-white border border-gray-200 rounded-xl p-6">
        <Select
          label="From account"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
          required
        >
          <option value="">Select SMTP account…</option>
          {accounts?.map((a) => (
            <option key={a.id} value={a.id}>
              {a.name} ({a.from_email})
            </option>
          ))}
        </Select>
        <Input label="To" type="email" value={to} onChange={(e) => setTo(e.target.value)} required />
        <Input label="Reply-to (optional)" type="email" value={replyTo} onChange={(e) => setReplyTo(e.target.value)} />
        <Input label="Subject" value={subject} onChange={(e) => setSubject(e.target.value)} required />
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Body</label>
          <RichTextEditor value={bodyHtml} onChange={setBodyHtml} placeholder="Write your message…" />
        </div>
        <div>
          <label className="text-sm font-medium text-gray-700 block mb-1">Attachments</label>
          <AttachmentDropzone onChange={setAttachmentIds} />
        </div>
        {send.isError && <p className="text-sm text-red-600">{String(send.error)}</p>}
        <div className="flex justify-end">
          <Button type="submit" loading={send.isPending}>Send email</Button>
        </div>
      </form>
    </div>
  );
}
