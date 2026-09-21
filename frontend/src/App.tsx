import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { OverviewPage } from "./features/overview/OverviewPage";
import { DiscoverPage } from "./features/discover/DiscoverPage";
import { ApplicationsPage } from "./features/applications/ApplicationsPage";
import { CompaniesPage } from "./features/companies/CompaniesPage";
import { OutreachPage } from "./features/outreach/OutreachPage";
import { ProfilePage } from "./features/profile/ProfilePage";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";
import { AutomationsPage } from "./features/automations/AutomationsPage";
import { SettingsPage } from "./features/settings/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<Navigate to="/overview" replace />} />
        <Route path="/overview" element={<OverviewPage />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/applications" element={<ApplicationsPage />} />
        <Route path="/companies" element={<CompaniesPage />} />
        <Route path="/outreach" element={<OutreachPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/automations" element={<AutomationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
