
import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { AuthGate } from "./features/auth/AuthGate";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { ApplicationsPage } from "./features/applications/ApplicationsPage";
import { AutomationsPage } from "./features/automations/AutomationsPage";
import { CompaniesPage } from "./features/companies/CompaniesPage";
import { DiscoverPage } from "./features/discover/DiscoverPage";
import { IntegrationsPage } from "./features/integrations/IntegrationsPage";
import { OutreachPage } from "./features/outreach/OutreachPage";
import { OverviewPage } from "./features/overview/OverviewPage";
import { ProfilePage } from "./features/profile/ProfilePage";
import { SettingsPage } from "./features/settings/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AuthGate><AppShell /></AuthGate>}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/companies" element={<CompaniesPage />} />
        <Route path="/outreach" element={<OutreachPage />} />
        <Route path="/integrations" element={<IntegrationsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/automations" element={<AutomationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
