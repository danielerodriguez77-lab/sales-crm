import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

type Task = {
  id: number;
  title: string;
  status: string;
  due_at?: string | null;
  task_type: string;
};

export default function TasksPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Task[]>([]);

  async function load() {
    const data = await apiFetch<Task[]>("/api/tasks", { token: token || undefined });
    setItems(data);
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Tareas y Recordatorios</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>
      <div className="space-y-2">
        {items.map((task) => (
          <div key={task.id} className="rounded border bg-white p-3 text-sm">
            <div className="font-medium">{task.title}</div>
            <div className="text-xs text-slate-500">{task.task_type}</div>
            <div className="text-xs">{task.due_at || "-"}</div>
            <div className="text-xs">Estado: {task.status}</div>
          </div>
        ))}
        {!items.length ? <div className="text-sm text-slate-400">Sin tareas</div> : null}
      </div>
    </div>
  );
}
