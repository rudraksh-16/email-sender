export interface SmtpAccount {
  id: string;
  name: string;
  host: string;
  port: number;
  username?: string;
  use_tls: boolean;
  use_ssl: boolean;
  from_email: string;
  from_name?: string;
  max_per_minute: number;
  max_per_hour: number;
  max_per_day: number;
  is_default: boolean;
  has_password: boolean;
  created_at: string;
  updated_at: string;
}

export interface SmtpAccountCreate {
  name: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
  use_tls?: boolean;
  use_ssl?: boolean;
  from_email: string;
  from_name?: string;
  max_per_minute?: number;
  max_per_hour?: number;
  max_per_day?: number;
  is_default?: boolean;
}

export interface Contact {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  extra: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ContactGroup {
  id: string;
  name: string;
  description?: string;
  contact_count: number;
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  body_text?: string;
  default_smtp_account_id?: string;
  created_at: string;
  updated_at: string;
}

export type CampaignStatus = "queued" | "running" | "done" | "failed" | "cancelled";
export type EmailLogStatus = "queued" | "sending" | "sent" | "failed" | "retrying";

export interface Campaign {
  id: string;
  name: string;
  subject: string;
  body_html: string;
  smtp_account_id: string;
  template_id?: string;
  status: CampaignStatus;
  total: number;
  sent_count: number;
  failed_count: number;
  started_at?: string;
  finished_at?: string;
  created_at: string;
  updated_at: string;
}

export interface EmailLog {
  id: string;
  campaign_id?: string;
  to_email: string;
  merge_data?: Record<string, string>;
  subject_rendered?: string;
  body_html_rendered?: string;
  status: EmailLogStatus;
  error_message?: string;
  attempts: number;
  sent_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CampaignEmailMatch {
  campaign_id: string;
  campaign_name: string;
  subject: string;
  campaign_status: CampaignStatus;
  to_email: string;
  email_status: EmailLogStatus;
  error_message?: string;
  sent_at?: string;
  created_at: string;
}

export interface Attachment {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  campaign_id?: string;
  template_id?: string;
  created_at: string;
  updated_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}
