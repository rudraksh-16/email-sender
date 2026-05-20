import { api } from "./client";
import type { Contact, ContactGroup, Page } from "./types";

export const contactsApi = {
  list: (params?: { q?: string; limit?: number; offset?: number }) =>
    api.get<Page<Contact>>("/contacts", { params }).then((r) => r.data),
  create: (data: Partial<Contact>) => api.post<Contact>("/contacts", data).then((r) => r.data),
  update: (id: string, data: Partial<Contact>) =>
    api.patch<Contact>(`/contacts/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/contacts/${id}`),
  import: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<{ created: number; updated: number; skipped: number; errors: string[] }>(
        "/contacts/import",
        form,
        { headers: { "Content-Type": "multipart/form-data" } },
      )
      .then((r) => r.data);
  },
};

export const groupsApi = {
  list: () => api.get<ContactGroup[]>("/groups").then((r) => r.data),
  get: (id: string) => api.get<ContactGroup>(`/groups/${id}`).then((r) => r.data),
  create: (data: { name: string; description?: string }) =>
    api.post<ContactGroup>("/groups", data).then((r) => r.data),
  update: (id: string, data: Partial<{ name: string; description: string }>) =>
    api.patch<ContactGroup>(`/groups/${id}`, data).then((r) => r.data),
  delete: (id: string) => api.delete(`/groups/${id}`),
  addMember: (groupId: string, contactId: string) =>
    api.post(`/groups/${groupId}/members/${contactId}`),
  removeMember: (groupId: string, contactId: string) =>
    api.delete(`/groups/${groupId}/members/${contactId}`),
};
