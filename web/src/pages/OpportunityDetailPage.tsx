import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

type Opportunity = {
  id: number;
  company_name?: string | null;
  person_name?: string | null;
  stage: string;
  estimated_value?: number | null;
  notes?: string | null;
};

type Activity = {
  id: number;
  activity_type: string;
  activity_at: string;
  notes?: string | null;
};

type Quote = {
  id: number;
  number: string;
  status: string;
  total?: number | null;
};

type Invoice = {
  id: number;
  number: string;
  status: string;
  total: number;
};

type Payment = {
  id: number;
  amount: number;
  date: string;
};

export default function OpportunityDetailPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [payments, setPayments] = useState<Record<number, Payment[]>>({});
  const ACTIVITY_LABELS: Record<string, string> = {
    call: "Llamada",
    reunion_online: "Reunión en línea",
    reunion_presencial: "Reunión presencial",
    email: "Correo electrónico",
    visit: "Visita",
    whatsapp: "WhatsApp",
    demo: "Demo"
  };

  function formatActivityType(value: string) {
    return ACTIVITY_LABELS[value] || value;
  }

  async function load() {
    if (!id) return;
    const opp = await apiFetch<Opportunity>(`/api/opportunities/${id}`, { token: token || undefined });
    const acts = await apiFetch<Activity[]>(`/api/activities?opportunity_id=${id}`, { token: token || undefined });
    const qs = await apiFetch<Quote[]>(`/api/quotes?opportunity_id=${id}`, { token: token || undefined });
    const invs = await apiFetch<Invoice[]>(`/api/invoices?opportunity_id=${id}`, { token: token || undefined });
    const paymentsByInvoice: Record<number, Payment[]> = {};
    for (const inv of invs) {
      paymentsByInvoice[inv.id] = await apiFetch<Payment[]>(`/api/payments?invoice_id=${inv.id}`, { token: token || undefined });
    }

    setOpportunity(opp);
    setActivities(acts);
    setQuotes(qs);
    setInvoices(invs);
    setPayments(paymentsByInvoice);
  }

  useEffect(() => {
    load();
  }, [id]);

  if (!opportunity) {
    return <div>Cargando...</div>;
  }

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-xl font-semibold">
          {opportunity.company_name || opportunity.person_name || `Oportunidad ${opportunity.id}`}
        </h2>
        <div className="text-sm text-slate-600">Etapa: {opportunity.stage}</div>
        {opportunity.notes ? <p className="mt-2 text-sm">{opportunity.notes}</p> : null}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-white p-4">
          <h3 className="text-sm font-semibold">Actividades</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {activities.map((act) => (
              <li key={act.id} className="rounded border px-2 py-2">
                <div className="font-medium">{formatActivityType(act.activity_type)}</div>
                <div className="text-xs text-slate-500">{act.activity_at}</div>
                {act.notes ? <div className="text-xs">{act.notes}</div> : null}
              </li>
            ))}
            {!activities.length ? <li className="text-xs text-slate-400">Sin actividades</li> : null}
          </ul>
        </div>

        <div className="rounded-lg border bg-white p-4">
          <h3 className="text-sm font-semibold">Cotizaciones</h3>
          <ul className="mt-2 space-y-2 text-sm">
            {quotes.map((quote) => (
              <li key={quote.id} className="rounded border px-2 py-2">
                <div className="font-medium">{quote.number}</div>
                <div className="text-xs text-slate-500">Estado: {quote.status}</div>
                <div className="text-xs">Total: {quote.total ?? 0}</div>
              </li>
            ))}
            {!quotes.length ? <li className="text-xs text-slate-400">Sin cotizaciones</li> : null}
          </ul>
        </div>

        <div className="rounded-lg border bg-white p-4 md:col-span-2">
          <h3 className="text-sm font-semibold">Facturas y pagos</h3>
          <div className="mt-2 space-y-3 text-sm">
            {invoices.map((inv) => (
              <div key={inv.id} className="rounded border px-3 py-2">
                <div className="font-medium">Factura {inv.number}</div>
                <div className="text-xs text-slate-500">Estado: {inv.status}</div>
                <div className="text-xs">Total: {inv.total}</div>
                <div className="mt-2 text-xs text-slate-600">Pagos</div>
                <ul className="mt-1 space-y-1">
                  {(payments[inv.id] || []).map((p) => (
                    <li key={p.id} className="rounded border px-2 py-1">
                      {p.date} - {p.amount}
                    </li>
                  ))}
                  {!payments[inv.id]?.length ? (
                    <li className="text-xs text-slate-400">Sin pagos</li>
                  ) : null}
                </ul>
              </div>
            ))}
            {!invoices.length ? <div className="text-xs text-slate-400">Sin facturas</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
