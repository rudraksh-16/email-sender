import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, CheckCircle, XCircle } from "lucide-react";
import { smtpApi } from "@/api/smtp";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import type { SmtpAccountCreate } from "@/api/types";

const EMPTY: SmtpAccountCreate = {
  name: "",
  host: "",
  port: 587,
  username: "",
  password: "",
  use_tls: true,
  use_ssl: false,
  from_email: "",
  from_name: "",
  max_per_minute: 30,
  max_per_hour: 500,
  is_default: false,
};

export function SmtpSettingsPage() {
  const qc = useQueryClient();
  const { data: accounts, isLoading } = useQuery({
    queryKey: ["smtp-accounts"],
    queryFn: smtpApi.list,
  });

  const [modal, setModal] = useState<"add" | null>(null);
  const [form, setForm] = useState<SmtpAccountCreate>(EMPTY);
  const [testResult, setTestResult] = useState<Record<string, { ok: boolean; error?: string }>>({});

  const create = useMutation({
    mutationFn: smtpApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["smtp-accounts"] });
      setModal(null);
      setForm(EMPTY);
    },
  });

  const del = useMutation({
    mutationFn: smtpApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["smtp-accounts"] }),
  });

  const test = useMutation({
    mutationFn: (id: string) => smtpApi.test(id),
    onSuccess: (data, id) => setTestResult((prev) => ({ ...prev, [id]: data })),
  });

  const f = (field: keyof SmtpAccountCreate) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const val = e.target.type === "checkbox" ? (e.target as HTMLInputElement).checked : e.target.value;
    setForm((prev) => ({ ...prev, [field]: val }));
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">SMTP Settings</h1>
        <Button onClick={() => setModal("add")}>
          <Plus size={16} /> Add account
        </Button>
      </div>

      {isLoading ? (
        <Spinner />
      ) : accounts?.length === 0 ? (
        <div className="text-center py-16 text-gray-500">No SMTP accounts. Add one to start sending.</div>
      ) : (
        <div className="space-y-3">
          {accounts?.map((a) => (
            <div key={a.id} className="bg-white border border-gray-200 rounded-xl p-4 flex items-start gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="font-medium text-gray-900">{a.name}</span>
                  {a.is_default && (
                    <span className="text-xs bg-blue-100 text-blue-700 rounded-full px-2 py-0.5">default</span>
                  )}
                </div>
                <p className="text-sm text-gray-500">
                  {a.from_name ? `${a.from_name} <${a.from_email}>` : a.from_email}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {a.host}:{a.port} · {a.use_ssl ? "SSL" : a.use_tls ? "STARTTLS" : "plain"} ·
                  {a.max_per_minute}/min
                </p>
                {testResult[a.id] && (
                  <div className={`flex items-center gap-1 text-xs mt-1 ${testResult[a.id].ok ? "text-green-600" : "text-red-600"}`}>
                    {testResult[a.id].ok ? <CheckCircle size={12} /> : <XCircle size={12} />}
                    {testResult[a.id].ok ? "Connection OK" : testResult[a.id].error}
                  </div>
                )}
              </div>
              <div className="flex gap-2 shrink-0">
                <Button
                  variant="secondary"
                  size="sm"
                  loading={test.isPending}
                  onClick={() => test.mutate(a.id)}
                >
                  Test
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => {
                    if (confirm(`Delete "${a.name}"?`)) del.mutate(a.id);
                  }}
                >
                  <Trash2 size={14} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={modal === "add"} onClose={() => setModal(null)} title="Add SMTP account" className="max-w-xl">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            create.mutate(form);
          }}
          className="space-y-3"
        >
          <Input label="Name" value={form.name} onChange={f("name")} required />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Host" value={form.host} onChange={f("host")} required />
            <Input label="Port" type="number" value={form.port} onChange={f("port")} required />
          </div>
          <Input label="Username" value={form.username} onChange={f("username")} />
          <Input label="Password" type="password" value={form.password} onChange={f("password")} />
          <div className="grid grid-cols-2 gap-3">
            <Input label="From email" type="email" value={form.from_email} onChange={f("from_email")} required />
            <Input label="From name" value={form.from_name} onChange={f("from_name")} />
          </div>
          <Select
            label="Security"
            value={form.use_ssl ? "ssl" : form.use_tls ? "tls" : "none"}
            onChange={(e) =>
              setForm((prev) => ({
                ...prev,
                use_ssl: e.target.value === "ssl",
                use_tls: e.target.value === "tls",
              }))
            }
          >
            <option value="tls">STARTTLS</option>
            <option value="ssl">SSL/TLS (implicit)</option>
            <option value="none">None</option>
          </Select>
          <div className="grid grid-cols-2 gap-3">
            <Input label="Max per minute" type="number" value={form.max_per_minute} onChange={f("max_per_minute")} />
            <Input label="Max per hour" type="number" value={form.max_per_hour} onChange={f("max_per_hour")} />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_default} onChange={f("is_default")} />
            Set as default
          </label>
          {create.error && <p className="text-xs text-red-600">{String(create.error)}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" type="button" onClick={() => setModal(null)}>Cancel</Button>
            <Button type="submit" loading={create.isPending}>Save</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
