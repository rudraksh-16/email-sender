import { api } from "./client";
import type { SmtpAccount, SmtpAccountCreate } from "./types";

export const smtpApi = {
  list: () => api.get<SmtpAccount[]>("/smtp-accounts").then((r) => r.data),
  create: (data: SmtpAccountCreate) =>
    api.post<SmtpAccount>("/smtp-accounts", data).then((r) => r.data),
  update: (id: string, data: Partial<SmtpAccountCreate>) =>
    api.patch<SmtpAccount>(`/smtp-accounts/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/smtp-accounts/${id}`),
  test: (id: string) =>
    api.post<{ ok: boolean; error?: string }>(`/smtp-accounts/${id}/test`).then((r) => r.data),
};
