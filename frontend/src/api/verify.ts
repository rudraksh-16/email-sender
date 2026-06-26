import { api } from "./client";

export type Verdict = "valid" | "invalid" | "duplicate";

export interface VerifyRowResult {
  index: number;
  email: string;
  normalized: string | null;
  verdict: Verdict;
  reason: string | null;
  data: Record<string, string>;
}

export interface VerifyReport {
  summary: { total: number; valid: number; invalid: number; duplicate: number };
  rows: VerifyRowResult[];
}

export const verifyApi = {
  csv: (csvText: string) => {
    const form = new FormData();
    form.append("file", new Blob([csvText], { type: "text/csv" }), "list.csv");
    return api
      .post<VerifyReport>("/verify", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};
