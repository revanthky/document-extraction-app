import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

const tabClass = ({ isActive }: { isActive: boolean }) =>
  `px-4 py-2 text-sm font-medium rounded-md transition-colors ${
    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
  }`;

export function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <h1 className="text-lg font-semibold text-slate-900">Document Extraction</h1>
          <nav className="flex gap-2">
            <NavLink to="/" end className={tabClass}>
              Settings
            </NavLink>
            <NavLink to="/extract" className={tabClass}>
              Document Extraction
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-6">{children}</main>
    </div>
  );
}
