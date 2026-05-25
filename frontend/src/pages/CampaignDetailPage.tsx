import { useParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { campaignsApi } from "@/api/campaigns";
import type { Page, EmailLog } from "@/api/types";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { fmtDate } from "@/lib/utils";

export function CampaignDetailPage() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();

  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["campaign-logs", id] });
    qc.invalidateQueries({ queryKey: ["campaigns", id] });
  };

  const retry = useMutation({
    mutationFn: (logId: string) => campaignsApi.retryLog(logId),
    onSuccess: invalidate,
  });

  const retryAll = useMutation({
    mutationFn: () => campaignsApi.retryFailed(id!),
    onSuccess: invalidate,
  });

  const busy = retry.isPending || retryAll.isPending;

  const { data: campaign, isLoading } = useQuery({
    queryKey: ["campaigns", id],
    queryFn: () => campaignsApi.get(id!),
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      if (s === "running" || s === "queued") return 1500;
      if (busy) return 1000;
      const logsCache = qc.getQueryData<Page<EmailLog>>(["campaign-logs", id]);
      if (logsCache?.items.some((l) => l.status === "retrying")) return 1000;
      return false;
    },
    enabled: !!id,
  });

  const { data: logs } = useQuery({
    queryKey: ["campaign-logs", id],
    queryFn: () => campaignsApi.logs(id!, { limit: 200 }),
    refetchInterval: (q) => {
      if (campaign?.status === "running" || campaign?.status === "queued") return 2000;
      if (busy) return 1000;
      if (q.state.data?.items.some((l) => l.status === "retrying")) return 1000;
      return false;
    },
    enabled: !!id,
  });

  const cancel = useMutation({
    mutationFn: () => campaignsApi.cancel(id!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["campaigns", id] }),
  });

  if (isLoading || !campaign) {
    return <div className="flex justify-center py-16"><Spinner /></div>;
  }

  const pct = campaign.total > 0 ? Math.round((campaign.sent_count / campaign.total) * 100) : 0;

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">{campaign.name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">{campaign.subject}</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge label={campaign.status} variant={campaign.status} />
          {!["queued", "running"].includes(campaign.status) && campaign.failed_count > 0 && (
            <Button
              variant="primary"
              size="sm"
              loading={retryAll.isPending}
              onClick={() => retryAll.mutate()}
            >
              Retry failed ({campaign.failed_count})
            </Button>
          )}
          {["queued", "running"].includes(campaign.status) && (
            <Button variant="danger" size="sm" loading={cancel.isPending} onClick={() => cancel.mutate()}>
              Cancel
            </Button>
          )}
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>{campaign.sent_count} sent · {campaign.failed_count} failed · {campaign.total} total</span>
          <span>{pct}%</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div className="h-full bg-blue-500 rounded-full transition-all duration-500" style={{ width: `${pct}%` }} />
        </div>
        <div className="grid grid-cols-3 gap-4 mt-4 text-sm text-gray-500">
          <div>Started: {fmtDate(campaign.started_at)}</div>
          <div>Finished: {fmtDate(campaign.finished_at)}</div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100">
          <h2 className="font-medium text-gray-900 text-sm">Recipients ({logs?.total ?? 0})</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wide">
              <th className="px-5 py-3 font-medium">Email</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Attempts</th>
              <th className="px-5 py-3 font-medium">Sent</th>
              <th className="px-5 py-3 font-medium">Error</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {logs?.items.map((log) => (
              <tr key={log.id} className="border-b border-gray-50 hover:bg-gray-50">
                <td className="px-5 py-3 font-medium text-gray-900">{log.to_email}</td>
                <td className="px-5 py-3"><Badge label={log.status} variant={log.status} /></td>
                <td className="px-5 py-3 text-gray-500">{log.attempts}</td>
                <td className="px-5 py-3 text-gray-500">{fmtDate(log.sent_at)}</td>
                <td className="px-5 py-3 text-red-500 text-xs max-w-xs truncate">{log.error_message ?? "—"}</td>
                <td className="px-5 py-3 text-right">
                  {log.status === "failed" && (
                    <Button
                      size="sm"
                      variant="secondary"
                      loading={retry.isPending}
                      onClick={() => retry.mutate(log.id)}
                    >
                      Retry
                    </Button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
