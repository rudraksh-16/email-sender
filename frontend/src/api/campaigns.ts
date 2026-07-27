import { api } from "./client";
import type { Campaign, CampaignEmailMatch, EmailLog, Page } from "./types";

export const campaignsApi = {
  list: () => api.get<Campaign[]>("/campaigns").then((r) => r.data),
  searchByEmail: (email: string) =>
    api
      .get<CampaignEmailMatch[]>("/campaigns/search-by-email", { params: { email } })
      .then((r) => r.data),
  get: (id: string) => api.get<Campaign>(`/campaigns/${id}`).then((r) => r.data),
  create: (data: object) => api.post<Campaign>("/campaigns", data).then((r) => r.data),
  fromCsv: (form: FormData) =>
    api
      .post<Campaign>("/campaigns/from-csv", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data),
  cancel: (id: string) => api.post<Campaign>(`/campaigns/${id}/cancel`).then((r) => r.data),
  duplicate: (id: string, body: { recipients: "all" | "sent" | "failed"; name?: string }) =>
    api.post<Campaign>(`/campaigns/${id}/duplicate`, body).then((r) => r.data),
  delete: (id: string) => api.delete(`/campaigns/${id}`),
  retryFailed: (id: string) =>
    api.post<Campaign>(`/campaigns/${id}/retry-failed`).then((r) => r.data),
  logs: (id: string, params?: { limit?: number; offset?: number }) =>
    api.get<Page<EmailLog>>(`/campaigns/${id}/logs`, { params }).then((r) => r.data),
  retryLog: (logId: string) =>
    api.post<EmailLog>(`/campaigns/logs/${logId}/retry`).then((r) => r.data),
};

export const sendApi = {
  single: (data: object) =>
    api
      .post<{ accepted: boolean; message_id?: string; info?: string }>("/send", data)
      .then((r) => r.data),
};

export const attachmentsApi = {
  upload: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<{ id: string; filename: string; mime_type: string; size_bytes: number }>(
        "/attachments",
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      )
      .then((r) => r.data);
  },
  delete: (id: string) => api.delete(`/attachments/${id}`),
};
