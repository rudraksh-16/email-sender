import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function Shell() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 ml-[var(--sidebar-w)] min-h-screen overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
