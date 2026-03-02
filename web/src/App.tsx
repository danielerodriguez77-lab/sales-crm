import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./lib/AuthContext";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import PipelinePage from "./pages/PipelinePage";
import OpportunitiesPage from "./pages/OpportunitiesPage";
import OpportunityDetailPage from "./pages/OpportunityDetailPage";
import ActivitiesPage from "./pages/ActivitiesPage";
import QuotesPage from "./pages/QuotesPage";
import InvoicesPage from "./pages/InvoicesPage";
import TasksPage from "./pages/TasksPage";
import DashboardPage from "./pages/DashboardPage";
import ReportsPage from "./pages/ReportsPage";
import UsersPage from "./pages/UsersPage";

function ProtectedRoutes() {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-6">Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/pipeline" element={<PipelinePage />} />
        <Route path="/oportunidades" element={<OpportunitiesPage />} />
        <Route path="/oportunidades/:id" element={<OpportunityDetailPage />} />
        <Route path="/actividades" element={<ActivitiesPage />} />
        <Route path="/cotizaciones" element={<QuotesPage />} />
        <Route path="/facturas" element={<InvoicesPage />} />
        <Route path="/tareas" element={<TasksPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/reportes" element={<ReportsPage />} />
        <Route path="/usuarios" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/pipeline" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
