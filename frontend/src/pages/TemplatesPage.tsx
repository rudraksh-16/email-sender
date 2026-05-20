import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, Trash2 } from "lucide-react";
import { templatesApi } from "@/api/templates";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { fmtDate } from "@/lib/utils";

export function TemplatesPage() {
  const qc = useQueryClient();
  const { data: templates, isLoading } = useQuery({
    queryKey: ["templates"],
    queryFn: templatesApi.list,
  });

  const del = useMutation({
    mutationFn: templatesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Templates</h1>
        <Link to="/templates/new">
          <Button><Plus size={16} /> New template</Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : templates?.length === 0 ? (
        <div className="text-center py-16 text-gray-500">No templates yet.</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Subject</th>
                <th className="px-5 py-3 font-medium">Updated</th>
                <th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody>
              {templates?.map((t) => (
                <tr key={t.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-3">
                    <Link to={`/templates/${t.id}`} className="font-medium text-blue-700 hover:underline">{t.name}</Link>
                  </td>
                  <td className="px-5 py-3 text-gray-600 truncate max-w-xs">{t.subject}</td>
                  <td className="px-5 py-3 text-gray-500">{fmtDate(t.updated_at)}</td>
                  <td className="px-5 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => { if (confirm(`Delete "${t.name}"?`)) del.mutate(t.id); }}
                    >
                      <Trash2 size={14} />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
