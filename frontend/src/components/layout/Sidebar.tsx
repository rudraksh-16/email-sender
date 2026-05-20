import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Mail,
  Send,
  FileText,
  Users,
  UsersRound,
  Settings,
  ScrollText,
} from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/compose", icon: Mail, label: "Compose" },
  { to: "/bulk", icon: Send, label: "Bulk Send" },
  { to: "/templates", icon: FileText, label: "Templates" },
  { to: "/contacts", icon: Users, label: "Contacts" },
  { to: "/groups", icon: UsersRound, label: "Groups" },
  { to: "/logs", icon: ScrollText, label: "Logs" },
  { to: "/smtp", icon: Settings, label: "SMTP Settings" },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex w-[var(--sidebar-w)] flex-col border-r border-gray-200 bg-white">
      <div className="flex h-14 items-center px-4 border-b border-gray-200">
        <span className="font-semibold text-gray-900 tracking-tight">Email App</span>
      </div>
      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
