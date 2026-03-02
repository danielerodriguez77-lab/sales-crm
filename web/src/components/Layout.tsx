import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <div className="text-lg font-semibold">Sales CRM</div>
            <nav className="flex flex-wrap gap-3 text-sm text-slate-600">
              <Link to="/pipeline">Pipeline</Link>
              <Link to="/oportunidades">Oportunidades</Link>
              <Link to="/actividades">Actividades</Link>
              <Link to="/cotizaciones">Cotizaciones</Link>
              <Link to="/facturas">Facturas</Link>
              <Link to="/tareas">Tareas</Link>
              <Link to="/dashboard">Dashboard</Link>
              {user?.role !== "seller" ? <Link to="/reportes">Reportes</Link> : null}
              {user?.role === "manager" ? <Link to="/usuarios">Usuarios</Link> : null}
            </nav>
          </div>
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">{user?.name}</span>
            <button
              onClick={logout}
              className="rounded border px-3 py-1 text-sm hover:bg-slate-100"
            >
              Salir
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  );
}
