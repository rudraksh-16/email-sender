import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { campaignsApi } from "@/api/campaigns";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { fmtDate } from "@/lib/utils";

export function LogsPage() {
  const { data: campaigns, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: campaignsApi.list,
  });

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Campaign Logs</h1>

      {isLoading ? (
        <div className="flex justify-center py-12"><Spinner /></div>
      ) : campaigns?.length === 0 ? (
        <div className="text-center py-16 text-gray-500">No campaigns yet.</div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-5 py-3 font-medium">Campaign</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Sent</th>
                <th className="px-5 py-3 font-medium">Failed</th>
                <th className="px-5 py-3 font-medium">Total</th>
                <th className="px-5 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {campaigns?.map((c) => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-5 py-3">
                    <Link to={`/campaigns/${c.id}`} className="font-medium text-blue-700 hover:underline">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3"><Badge label={c.status} variant={c.status} /></td>
                  <td className="px-5 py-3 text-green-600">{c.sent_count}</td>
                  <td className="px-5 py-3 text-red-500">{c.failed_count}</td>
                  <td className="px-5 py-3 text-gray-500">{c.total}</td>
                  <td className="px-5 py-3 text-gray-500">{fmtDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
