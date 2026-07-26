import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { campaignsApi } from "@/api/campaigns";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { fmtDate } from "@/lib/utils";

export function EmailSearchPage() {
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");

  const { data: matches, isFetching } = useQuery({
    queryKey: ["campaign-search", query],
    queryFn: () => campaignsApi.searchByEmail(query),
    enabled: query.length > 0,
  });

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    setQuery(input.trim());
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Find Campaigns by Email</h1>

      <form onSubmit={onSubmit} className="flex items-end gap-3 mb-6">
        <div className="flex-1">
          <Input
            label="Email address"
            type="email"
            placeholder="person@example.com"
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
        </div>
        <Button type="submit" disabled={!input.trim()} loading={isFetching}>
          <Search size={16} />
          Search
        </Button>
      </form>

      {query && !isFetching && matches?.length === 0 && (
        <div className="text-center py-16 text-gray-500">
          No campaigns include <span className="font-medium">{query}</span>.
        </div>
      )}

      {matches && matches.length > 0 && (
        <>
          <p className="text-sm text-gray-500 mb-3">
            Found in {matches.length} campaign{matches.length === 1 ? "" : "s"}.
          </p>
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-left text-xs text-gray-500 uppercase tracking-wide">
                  <th className="px-5 py-3 font-medium">Campaign</th>
                  <th className="px-5 py-3 font-medium">Campaign Status</th>
                  <th className="px-5 py-3 font-medium">Delivery</th>
                  <th className="px-5 py-3 font-medium">Sent</th>
                </tr>
              </thead>
              <tbody>
                {matches.map((m) => (
                  <tr key={m.campaign_id} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <Link
                        to={`/campaigns/${m.campaign_id}`}
                        className="font-medium text-blue-700 hover:underline"
                      >
                        {m.campaign_name}
                      </Link>
                      <div className="text-xs text-gray-400">{m.subject}</div>
                    </td>
                    <td className="px-5 py-3">
                      <Badge label={m.campaign_status} variant={m.campaign_status} />
                    </td>
                    <td className="px-5 py-3">
                      <Badge label={m.email_status} variant={m.email_status} />
                      {m.error_message && (
                        <div className="text-xs text-red-500 mt-1">{m.error_message}</div>
                      )}
                    </td>
                    <td className="px-5 py-3 text-gray-500">
                      {m.sent_at ? fmtDate(m.sent_at) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
