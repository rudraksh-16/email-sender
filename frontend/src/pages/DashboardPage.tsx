import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { campaignsApi } from "@/api/campaigns";
import { smtpApi } from "@/api/smtp";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { fmtDate } from "@/lib/utils";
import type { Campaign } from "@/api/types";

function ProgressBar({ campaign }: { campaign: Campaign }) {
  const pct = campaign.total > 0 ? Math.round((campaign.sent_count / campaign.total) * 100) : 0;
  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 mb-0.5">
        <span>{campaign.sent_count}/{campaign.total}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-blue-500 rounded-full transition-all"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: campaigns, isLoading } = useQuery({
    queryKey: ["campaigns"],
    queryFn: campaignsApi.list,
    refetchInterval: (query) => {
      const running = query.state.data?.some((c) => c.status === "running");
      return running ? 2000 : false;
    },
  });
  const { data: accounts } = useQuery({ queryKey: ["smtp-accounts"], queryFn: smtpApi.list });

  const stats = {
    total: campaigns?.length ?? 0,
    running: campaigns?.filter((c) => c.status === "running").length ?? 0,
    done: campaigns?.filter((c) => c.status === "done").length ?? 0,
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: "Total campaigns", value: stats.total },
          { label: "Running", value: stats.running },
          { label: "Completed", value: stats.done },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white border border-gray-200 rounded-xl p-5">
            <p className="text-sm text-gray-500">{label}</p>
            <p className="text-3xl font-semibold text-gray-900 mt-1">{value}</p>
          </div>
        ))}
      </div>

      {!accounts?.length && (
        <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-800">
          No SMTP accounts configured.{" "}
          <Link to="/smtp" className="font-medium underline">
            Add one
          </Link>{" "}
          before sending.
        </div>
      )}

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-medium text-gray-900">Recent campaigns</h2>
          <Link to="/bulk" className="text-sm text-blue-600 hover:underline">
            New campaign
          </Link>
        </div>
        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner />
          </div>
        ) : campaigns?.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-12">No campaigns yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wide">
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Status</th>
                <th className="px-5 py-3 font-medium">Progress</th>
                <th className="px-5 py-3 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {campaigns?.map((c) => (
                <tr key={c.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3">
                    <Link to={`/campaigns/${c.id}`} className="font-medium text-blue-700 hover:underline">
                      {c.name}
                    </Link>
                  </td>
                  <td className="px-5 py-3">
                    <Badge label={c.status} variant={c.status} />
                  </td>
                  <td className="px-5 py-3 w-48">
                    <ProgressBar campaign={c} />
                  </td>
                  <td className="px-5 py-3 text-gray-500">{fmtDate(c.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
