import {
  Activity,
  BarChart3,
  BriefcaseBusiness,
  Building2,
  Compass,
  MessageSquareText,
  Radar,
  Settings,
  UserRound,
  Workflow,
} from "lucide-react";
import {
  NavLink,
} from "react-router-dom";

const navigation = [
  {
    label: "Overview",
    path: "/overview",
    icon: Radar,
  },
  {
    label: "Discover",
    path: "/discover",
    icon: Compass,
  },
  {
    label: "Applications",
    path: "/applications",
    icon: BriefcaseBusiness,
  },
  {
    label: "Companies",
    path: "/companies",
    icon: Building2,
  },
  {
    label: "Outreach",
    path: "/outreach",
    icon: MessageSquareText,
  },
  {
    label: "Profile",
    path: "/profile",
    icon: UserRound,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
  {
    label: "Automations",
    path: "/automations",
    icon: Workflow,
  },
  {
    label: "Settings",
    path: "/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  return (
    <aside
      className="sidebar"
      aria-label="Application navigation"
    >
      <div className="brand">
        <div
          className="brand-mark"
          aria-hidden="true"
        >
          <Activity
            size={20}
            strokeWidth={2.4}
          />
        </div>

        <div>
          <div className="brand-name">
            Job Intelligence
          </div>

          <div className="brand-version">
            v2 workspace
          </div>
        </div>
      </div>

      <nav
        className="sidebar-nav"
        aria-label="Primary navigation"
      >
        {navigation.map(
          (
            item,
          ) => {
            const Icon =
              item.icon;

            return (
              <NavLink
                key={
                  item.path
                }
                to={
                  item.path
                }
                title={
                  item.label
                }
                className={({
                  isActive,
                }) =>
                  isActive
                    ? "nav-item nav-item-active"
                    : "nav-item"
                }
              >
                <Icon
                  size={18}
                  aria-hidden="true"
                />

                <span>
                  {item.label}
                </span>
              </NavLink>
            );
          },
        )}
      </nav>

      <div className="sidebar-footer">
        <div
          className="system-pill"
          role="status"
          aria-label="System online"
        >
          <span
            className="system-dot"
            aria-hidden="true"
          />

          System online
        </div>
      </div>
    </aside>
  );
}
