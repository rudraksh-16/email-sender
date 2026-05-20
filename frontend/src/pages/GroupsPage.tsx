import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { groupsApi } from "@/api/contacts";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";

export function GroupsPage() {
  const qc = useQueryClient();
  const { data: groups, isLoading } = useQuery({ queryKey: ["groups"], queryFn: groupsApi.list });
  const [modal, setModal] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");

  const create = useMutation({
    mutationFn: groupsApi.create,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["groups"] }); setModal(false); setName(""); setDesc(""); },
  });
  const del = useMutation({
    mutationFn: groupsApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["groups"] }),
  });

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Groups</h1>
        <Button onClick={() => setModal(true)}><Plus size={16} /> New group</Button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : groups?.length === 0 ? (
        <div className="text-center py-16 text-gray-500">No groups yet.</div>
      ) : (
        <div className="space-y-2">
          {groups?.map((g) => (
            <div key={g.id} className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{g.name}</p>
                {g.description && <p className="text-sm text-gray-500">{g.description}</p>}
                <p className="text-xs text-gray-400 mt-0.5">{g.contact_count} contacts</p>
              </div>
              <Button variant="ghost" size="sm" onClick={() => { if (confirm(`Delete "${g.name}"?`)) del.mutate(g.id); }}>
                <Trash2 size={14} />
              </Button>
            </div>
          ))}
        </div>
      )}

      <Modal open={modal} onClose={() => setModal(false)} title="New group">
        <form onSubmit={(e) => { e.preventDefault(); create.mutate({ name, description: desc || undefined }); }} className="space-y-3">
          <Input label="Group name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Description (optional)" value={desc} onChange={(e) => setDesc(e.target.value)} />
          {create.isError && <p className="text-xs text-red-600">{String(create.error)}</p>}
          <div className="flex justify-end"><Button type="submit" loading={create.isPending}>Create</Button></div>
        </form>
      </Modal>
    </div>
  );
}
