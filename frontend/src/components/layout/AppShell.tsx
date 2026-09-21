import {
  Outlet,
  useLocation,
} from "react-router-dom";

import { IntelligenceBackground } from "../effects/IntelligenceBackground";
import { ScrollToTop } from "../effects/ScrollToTop";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell() {
  const location =
    useLocation();

  return (
    <div className="app-shell">
      <IntelligenceBackground />

      <ScrollToTop />

      <Sidebar />

      <div className="app-main">
        <Topbar />

        <main
          className="app-content"
          id="main-content"
        >
          <div
            key={
              location.pathname
            }
            className="route-transition"
          >
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
