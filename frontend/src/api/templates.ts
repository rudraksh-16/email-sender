import { api } from "./client";
import type { Template } from "./types";

export const templatesApi = {
  list: () => api.get<Template[]>("/templates").then((r) => r.data),
  get: (id: string) => api.get<Template>(`/templates/${id}`).then((r) => r.data),
  create: (data: Partial<Template>) => api.post<Template>("/templates", data).then((r) => r.data),
  update: (id: string, data: Partial<Template>) =>
    api.patch<Template>(`/templates/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/templates/${id}`),
  preview: (id: string, data: Record<string, string>) =>
    api
      .post<{ subject: string; body_html: string; body_text: string }>(`/templates/${id}/preview`, {
        data,
      })
      .then((r) => r.data),
};
