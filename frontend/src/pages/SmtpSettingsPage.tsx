import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, CheckCircle, XCircle, Pencil } from "lucide-react";
import { smtpApi } from "@/api/smtp";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import type { SmtpAccount, SmtpAccountCreate } from "@/api/types";

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
  max_per_day: 2000,
  is_default: false,
};

type ModalMode = "add" | "edit" | null;

function accountToForm(a: SmtpAccount): SmtpAccountCreate {
  return {
    name: a.name,
    host: a.host,
    port: a.port,
    username: a.username ?? "",
    password: "",
    use_tls: a.use_tls,
    use_ssl: a.use_ssl,
    from_email: a.from_email,
    from_name: a.from_name ?? "",
    max_per_minute: a.max_per_minute,
    max_per_hour: a.max_per_hour,
    max_per_day: a.max_per_day,
    is_default: a.is_default,
  };
}

interface SmtpFormProps {
  form: SmtpAccountCreate;
  onChange: (field: keyof SmtpAccountCreate, value: unknown) => void;
  isEdit?: boolean;
  error?: string;
  isPending?: boolean;
  onCancel: () => void;
}

function SmtpForm({ form, onChange, isEdit, error, isPending, onCancel }: SmtpFormProps) {
  const f = (field: keyof SmtpAccountCreate) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
      const val = e.target.type === "checkbox" ? (e.target as HTMLInputElement).checked : e.target.value;
      onChange(field, val);
    };

  return (
    <div className="space-y-3">
      <Input label="Name" value={form.name} onChange={f("name")} required />
      <div className="grid grid-cols-2 gap-3">
        <Input label="Host" value={form.host} onChange={f("host")} required />
        <Input label="Port" type="number" value={form.port} onChange={f("port")} required />
      </div>
      <Input label="Username" value={form.username} onChange={f("username")} />
      <Input
        label={isEdit ? "New password (leave blank to keep current)" : "Password"}
        type="password"
        value={form.password}
        onChange={f("password")}
        required={!isEdit}
      />
      <div className="grid grid-cols-2 gap-3">
        <Input label="From email" type="email" value={form.from_email} onChange={f("from_email")} required />
        <Input label="From name" value={form.from_name} onChange={f("from_name")} />
      </div>
      <Select
        label="Security"
        value={form.use_ssl ? "ssl" : form.use_tls ? "tls" : "none"}
        onChange={(e) => {
          onChange("use_ssl", e.target.value === "ssl");
          onChange("use_tls", e.target.value === "tls");
        }}
      >
        <option value="tls">STARTTLS</option>
        <option value="ssl">SSL/TLS (implicit)</option>
        <option value="none">None</option>
      </Select>
      <div className="grid grid-cols-3 gap-3">
        <Input label="Max / minute" type="number" value={form.max_per_minute} onChange={f("max_per_minute")} />
        <Input label="Max / hour" type="number" value={form.max_per_hour} onChange={f("max_per_hour")} />
        <Input label="Max / day" type="number" value={form.max_per_day} onChange={f("max_per_day")} />
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={form.is_default} onChange={f("is_default")} />
        Set as default
      </label>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" type="button" onClick={onCancel}>Cancel</Button>
        <Button type="submit" loading={isPending}>{isEdit ? "Save changes" : "Save"}</Button>
      </div>
    </div>
  );
}

export function SmtpSettingsPage() {
  const qc = useQueryClient();
  const { data: accounts, isLoading } = useQuery({
    queryKey: ["smtp-accounts"],
    queryFn: smtpApi.list,
  });

  const [modal, setModal] = useState<ModalMode>(null);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState<SmtpAccountCreate>(EMPTY);
  const [testResult, setTestResult] = useState<Record<string, { ok: boolean; error?: string }>>({});

  const setField = (field: keyof SmtpAccountCreate, value: unknown) =>
    setForm((prev) => ({ ...prev, [field]: value }));

  const openAdd = () => {
    setForm(EMPTY);
    setEditId(null);
    setModal("add");
  };

  const openEdit = (a: SmtpAccount) => {
    setForm(accountToForm(a));
    setEditId(a.id);
    setModal("edit");
  };

  const closeModal = () => {
    setModal(null);
    setEditId(null);
  };

  const create = useMutation({
    mutationFn: smtpApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["smtp-accounts"] });
      closeModal();
    },
  });

  const update = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SmtpAccountCreate> }) =>
      smtpApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["smtp-accounts"] });
      closeModal();
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (modal === "edit" && editId) {
      const payload: Partial<SmtpAccountCreate> = { ...form };
      if (!payload.password) delete payload.password;
      update.mutate({ id: editId, data: payload });
    } else {
      create.mutate(form);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">SMTP Settings</h1>
        <Button onClick={openAdd}>
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
                  {a.max_per_minute}/min · {a.max_per_hour}/hr · {a.max_per_day}/day
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
                  variant="secondary"
                  size="sm"
                  onClick={() => openEdit(a)}
                >
                  <Pencil size={14} />
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

      <Modal
        open={modal !== null}
        onClose={closeModal}
        title={modal === "edit" ? "Edit SMTP account" : "Add SMTP account"}
        className="max-w-xl"
      >
        <form onSubmit={handleSubmit}>
          <SmtpForm
            form={form}
            onChange={setField}
            isEdit={modal === "edit"}
            error={create.isError ? String(create.error) : update.isError ? String(update.error) : undefined}
            isPending={create.isPending || update.isPending}
            onCancel={closeModal}
          />
        </form>
      </Modal>
    </div>
  );
}
