import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../lib/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/pipeline");
    } catch (err) {
      setError("Credenciales inválidas");
    }
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <div className="mx-auto flex min-h-screen max-w-md items-center px-6">
        <form onSubmit={handleSubmit} className="w-full rounded-xl bg-white/5 p-6">
          <h1 className="text-xl font-semibold">Ingresar</h1>
          <p className="mt-2 text-sm text-slate-300">Acceso al CRM de ventas</p>
          {error ? <div className="mt-3 text-sm text-red-300">{error}</div> : null}
          <div className="mt-4">
            <label className="text-sm text-slate-300">Email</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-white"
            />
          </div>
          <div className="mt-3">
            <label className="text-sm text-slate-300">Contraseña</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded border border-slate-700 bg-slate-900 px-3 py-2 text-white"
            />
          </div>
          <button className="mt-4 w-full rounded bg-indigo-500 py-2 text-sm font-semibold">
            Entrar
          </button>
        </form>
      </div>
    </div>
  );
}
