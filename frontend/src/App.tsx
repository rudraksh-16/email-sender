import { Routes, Route } from "react-router-dom";
import { Shell } from "@/components/layout/Shell";
import { DashboardPage } from "@/pages/DashboardPage";
import { ComposePage } from "@/pages/ComposePage";
import { BulkSendPage } from "@/pages/BulkSendPage";
import { CampaignDetailPage } from "@/pages/CampaignDetailPage";
import { TemplatesPage } from "@/pages/TemplatesPage";
import { TemplateEditPage } from "@/pages/TemplateEditPage";
import { ContactsPage } from "@/pages/ContactsPage";
import { GroupsPage } from "@/pages/GroupsPage";
import { SmtpSettingsPage } from "@/pages/SmtpSettingsPage";
import { LogsPage } from "@/pages/LogsPage";
import { EmailSearchPage } from "@/pages/EmailSearchPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/compose" element={<ComposePage />} />
        <Route path="/bulk" element={<BulkSendPage />} />
        <Route path="/campaigns/:id" element={<CampaignDetailPage />} />
        <Route path="/templates" element={<TemplatesPage />} />
        <Route path="/templates/new" element={<TemplateEditPage />} />
        <Route path="/templates/:id" element={<TemplateEditPage />} />
        <Route path="/contacts" element={<ContactsPage />} />
        <Route path="/groups" element={<GroupsPage />} />
        <Route path="/logs" element={<LogsPage />} />
        <Route path="/email-search" element={<EmailSearchPage />} />
        <Route path="/smtp" element={<SmtpSettingsPage />} />
      </Route>
    </Routes>
  );
}
