import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  active: boolean;
  team?: string | null;
};

const ROLE_OPTIONS = [
  { value: "manager", label: "Gerente" },
  { value: "supervisor", label: "Supervisor" },
  { value: "seller", label: "Vendedor" }
];

const TEAM_OPTIONS = [
  { value: "", label: "Sin equipo" },
  { value: "Agras", label: "Agras" },
  { value: "Enterprise", label: "Enterprise" }
];

export default function UsersPage() {
  const { token, user } = useAuth();
  const [items, setItems] = useState<User[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formName, setFormName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formRole, setFormRole] = useState(ROLE_OPTIONS[2].value);
  const [formTeam, setFormTeam] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    const data = await apiFetch<User[]>("/api/users", { token });
    setItems(data);
  }

  useEffect(() => {
    load();
  }, []);

  function resetForm() {
    setEditingId(null);
    setFormName("");
    setFormEmail("");
    setFormRole(ROLE_OPTIONS[2].value);
    setFormTeam("");
    setFormPassword("");
    setError(null);
  }

  function startEdit(u: User) {
    setEditingId(u.id);
    setFormName(u.name);
    setFormEmail(u.email);
    setFormRole(u.role);
    setFormTeam(u.team || "");
    setFormPassword("");
  }

  async function submit() {
    if (!token) return;
    setError(null);
    const payload = {
      name: formName,
      email: formEmail,
      role: formRole,
      team: formTeam || null,
      password: formPassword || undefined
    };
    try {
      if (editingId) {
        await apiFetch(`/api/users/${editingId}`, {
          method: "PATCH",
          token,
          body: JSON.stringify(payload)
        });
      } else {
        if (!formPassword) {
          setError("Debe definir una contraseña");
          return;
        }
        await apiFetch(`/api/users`, {
          method: "POST",
          token,
          body: JSON.stringify(payload)
        });
      }
      resetForm();
      await load();
    } catch (err) {
      setError("No se pudo guardar el usuario.");
    }
  }

  if (user?.role !== "manager") {
    return <div className="text-sm text-slate-500">No autorizado</div>;
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Usuarios</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>

      <div className="mb-6 rounded-lg border bg-white p-4 text-sm">
        <div className="mb-2 font-semibold">
          {editingId ? "Editar usuario" : "Nuevo usuario"}
        </div>
        {error ? <div className="mb-2 text-xs text-red-600">{error}</div> : null}
        <div className="grid gap-2 md:grid-cols-3">
          <input
            className="rounded border px-2 py-1"
            placeholder="Nombre"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />
          <input
            className="rounded border px-2 py-1"
            placeholder="Email"
            value={formEmail}
            onChange={(e) => setFormEmail(e.target.value)}
          />
          <select
            className="rounded border px-2 py-1"
            value={formRole}
            onChange={(e) => setFormRole(e.target.value)}
          >
            {ROLE_OPTIONS.map((role) => (
              <option key={role.value} value={role.value}>
                {role.label}
              </option>
            ))}
          </select>
          <select
            className="rounded border px-2 py-1"
            value={formTeam}
            onChange={(e) => setFormTeam(e.target.value)}
          >
            {TEAM_OPTIONS.map((team) => (
              <option key={team.value} value={team.value}>
                {team.label}
              </option>
            ))}
          </select>
          <input
            className="rounded border px-2 py-1"
            placeholder={editingId ? "Nueva contraseña (opcional)" : "Contraseña"}
            type="password"
            value={formPassword}
            onChange={(e) => setFormPassword(e.target.value)}
          />
          <div className="flex items-center gap-2">
            <button
              onClick={submit}
              className="rounded bg-indigo-600 px-3 py-1 text-xs text-white"
            >
              Guardar
            </button>
            {editingId ? (
              <button onClick={resetForm} className="rounded border px-3 py-1 text-xs">
                Cancelar
              </button>
            ) : null}
          </div>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Nombre</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Rol</th>
              <th className="px-3 py-2">Equipo</th>
              <th className="px-3 py-2">Activo</th>
              <th className="px-3 py-2">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id} className="border-t">
                <td className="px-3 py-2">{u.name}</td>
                <td className="px-3 py-2">{u.email}</td>
                <td className="px-3 py-2">{u.role}</td>
                <td className="px-3 py-2">{u.team || "-"}</td>
                <td className="px-3 py-2">{u.active ? "Sí" : "No"}</td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => startEdit(u)}
                    className="rounded border px-2 py-1 text-xs"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-400" colSpan={6}>
                  Sin usuarios
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
