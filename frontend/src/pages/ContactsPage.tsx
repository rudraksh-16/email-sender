import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Upload } from "lucide-react";
import { contactsApi } from "@/api/contacts";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { fmtDate } from "@/lib/utils";
import type { Contact } from "@/api/types";

function ContactForm({
  initial,
  onSubmit,
  loading,
  error,
}: {
  initial?: Partial<Contact>;
  onSubmit: (d: Partial<Contact>) => void;
  loading?: boolean;
  error?: string;
}) {
  const [email, setEmail] = useState(initial?.email ?? "");
  const [first, setFirst] = useState(initial?.first_name ?? "");
  const [last, setLast] = useState(initial?.last_name ?? "");

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ email, first_name: first || undefined, last_name: last || undefined });
      }}
      className="space-y-3"
    >
      <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      <div className="grid grid-cols-2 gap-3">
        <Input label="First name" value={first} onChange={(e) => setFirst(e.target.value)} />
        <Input label="Last name" value={last} onChange={(e) => setLast(e.target.value)} />
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
      <div className="flex justify-end">
        <Button type="submit" loading={loading}>Save</Button>
      </div>
    </form>
  );
}

export function ContactsPage() {
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [modal, setModal] = useState<"add" | "import" | null>(null);
  const [importMsg, setImportMsg] = useState<string>();

  const { data, isLoading } = useQuery({
    queryKey: ["contacts", q],
    queryFn: () => contactsApi.list({ q: q || undefined, limit: 100 }),
  });

  const create = useMutation({
    mutationFn: contactsApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["contacts"] }); setModal(null); },
  });
  const del = useMutation({
    mutationFn: contactsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["contacts"] }),
  });
  const doImport = useMutation({
    mutationFn: contactsApi.import,
    onSuccess: (r) => {
      qc.invalidateQueries({ queryKey: ["contacts"] });
      setImportMsg(`Created ${r.created}, updated ${r.updated}, skipped ${r.skipped}.`);
      setModal(null);
    },
  });

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Contacts</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setModal("import")}><Upload size={16} /> Import CSV</Button>
          <Button onClick={() => setModal("add")}><Plus size={16} /> Add contact</Button>
        </div>
      </div>

      {importMsg && (
        <div className="mb-4 p-3 bg-green-50 text-green-700 text-sm rounded-lg">{importMsg}</div>
      )}

      <Input
        placeholder="Search by email or name…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className="mb-4 max-w-sm"
      />

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-16 text-gray-500">No contacts found.</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Added</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {data?.items.map((c) => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-900">{c.email}</td>
                  <td className="px-5 py-3 text-gray-600">
                    {[c.first_name, c.last_name].filter(Boolean).join(" ") || "—"}
                  </td>
                  <td className="px-5 py-3 text-gray-500">{fmtDate(c.created_at)}</td>
                  <td className="px-5 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => { if (confirm(`Delete ${c.email}?`)) del.mutate(c.id); }}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {data && <p className="text-xs text-gray-400 px-5 py-2">{data.total} total</p>}
        </div>
      )}

      <Modal open={modal === "add"} onClose={() => setModal(null)} title="Add contact">
        <ContactForm
          onSubmit={(d) => create.mutate(d)}
          loading={create.isPending}
          error={create.isError ? String(create.error) : undefined}
        />
      </Modal>

      <Modal open={modal === "import"} onClose={() => setModal(null)} title="Import contacts (CSV)">
        <div className="space-y-3">
          <p className="text-sm text-gray-600">CSV must have an <code>email</code> column. Optional: <code>first_name</code>, <code>last_name</code>.</p>
          <Input
            type="file"
            accept=".csv"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) doImport.mutate(file);
            }}
          />
          {doImport.isError && <p className="text-xs text-red-600">{String(doImport.error)}</p>}
        </div>
      </Modal>
    </div>
  );
}
