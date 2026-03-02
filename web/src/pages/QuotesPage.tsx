import { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

type Quote = {
  id: number;
  number: string;
  status: string;
  total?: number | null;
  pdf_path?: string | null;
};

type Opportunity = {
  id: number;
  company_name?: string | null;
  person_name?: string | null;
};

type QuoteItem = {
  id: string;
  name: string;
  quantity: number;
  price: number;
};

function uuid() {
  return Math.random().toString(36).slice(2);
}

export default function QuotesPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Quote[]>([]);
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [opportunityId, setOpportunityId] = useState("");
  const [quoteItems, setQuoteItems] = useState<QuoteItem[]>([
    { id: uuid(), name: "", quantity: 1, price: 0 }
  ]);
  const [tax, setTax] = useState(0);
  const [discount, setDiscount] = useState(0);

  async function load() {
    const data = await apiFetch<Quote[]>("/api/quotes", { token: token || undefined });
    setItems(data);
    const opps = await apiFetch<Opportunity[]>("/api/opportunities", { token: token || undefined });
    setOpportunities(opps);
  }

  const subtotal = useMemo(() => {
    return quoteItems.reduce((sum, item) => sum + item.quantity * item.price, 0);
  }, [quoteItems]);

  const total = useMemo(() => {
    const discountAmount = subtotal * (discount / 100);
    return subtotal + tax - discountAmount;
  }, [subtotal, tax, discount]);

  function opportunityLabel(id: number) {
    const opp = opportunities.find((o) => o.id === id);
    if (!opp) return `Oportunidad ${id}`;
    return opp.company_name || opp.person_name || `Oportunidad ${id}`;
  }

  function addItem() {
    setQuoteItems((prev) => [...prev, { id: uuid(), name: "", quantity: 1, price: 0 }]);
  }

  function removeItem(id: string) {
    setQuoteItems((prev) => prev.filter((item) => item.id !== id));
  }

  function updateItem(id: string, field: keyof QuoteItem, value: string | number) {
    setQuoteItems((prev) =>
      prev.map((item) => (item.id === id ? { ...item, [field]: value } : item))
    );
  }

  async function generatePdf(id: number) {
    setLoading(true);
    await apiFetch(`/api/quotes/${id}/pdf`, {
      method: "POST",
      token: token || undefined
    });
    await load();
    setLoading(false);
  }

  async function sendQuote(id: number) {
    setLoading(true);
    await apiFetch(`/api/quotes/${id}/send`, {
      method: "POST",
      token: token || undefined
    });
    await load();
    setLoading(false);
  }

  async function createQuote(e: React.FormEvent) {
    e.preventDefault();
    if (!token) return;
    if (!opportunityId) return;

    const payloadItems = quoteItems
      .filter((item) => item.name.trim())
      .map((item) => ({
        name: item.name,
        quantity: item.quantity,
        price: item.price,
        subtotal: item.quantity * item.price
      }));

    await apiFetch("/api/quotes", {
      method: "POST",
      token,
      body: JSON.stringify({
        opportunity_id: Number(opportunityId),
        items: payloadItems,
        subtotal,
        tax,
        total,
        discount_percent: discount
      })
    });

    setOpportunityId("");
    setQuoteItems([{ id: uuid(), name: "", quantity: 1, price: 0 }]);
    setTax(0);
    setDiscount(0);
    await load();
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Cotizaciones</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>
      <form onSubmit={createQuote} className="mb-4 rounded-lg border bg-white p-3 text-sm">
        <div className="mb-2 font-semibold">Nueva cotización</div>
        <div className="grid gap-2 md:grid-cols-3">
          <select
            className="rounded border px-2 py-1"
            value={opportunityId}
            onChange={(e) => setOpportunityId(e.target.value)}
            required
          >
            <option value="">Seleccionar oportunidad</option>
            {opportunities.map((opp) => (
              <option key={opp.id} value={opp.id}>
                {opportunityLabel(opp.id)}
              </option>
            ))}
          </select>
          <input
            className="rounded border px-2 py-1"
            type="number"
            placeholder="Impuestos"
            value={tax}
            onChange={(e) => setTax(Number(e.target.value))}
          />
          <input
            className="rounded border px-2 py-1"
            type="number"
            placeholder="% Descuento"
            value={discount}
            onChange={(e) => setDiscount(Number(e.target.value))}
          />
        </div>

        <div className="mt-3 space-y-2">
          {quoteItems.map((item, idx) => (
            <div key={item.id} className="grid gap-2 md:grid-cols-4">
              <input
                className="rounded border px-2 py-1"
                placeholder={`Producto ${idx + 1}`}
                value={item.name}
                onChange={(e) => updateItem(item.id, "name", e.target.value)}
                required
              />
              <input
                className="rounded border px-2 py-1"
                type="number"
                placeholder="Cantidad"
                value={item.quantity}
                onChange={(e) => updateItem(item.id, "quantity", Number(e.target.value))}
              />
              <input
                className="rounded border px-2 py-1"
                type="number"
                placeholder="Precio"
                value={item.price}
                onChange={(e) => updateItem(item.id, "price", Number(e.target.value))}
              />
              <div className="flex items-center gap-2">
                <div className="text-xs text-slate-500">
                  Subtotal: {item.quantity * item.price}
                </div>
                {quoteItems.length > 1 ? (
                  <button
                    type="button"
                    onClick={() => removeItem(item.id)}
                    className="rounded border px-2 py-1 text-xs"
                  >
                    Quitar
                  </button>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-slate-600">
          <button type="button" onClick={addItem} className="rounded border px-2 py-1">
            Agregar producto
          </button>
          <div>
            Subtotal: {subtotal} | Total: {total}
          </div>
        </div>

        <button className="mt-3 rounded bg-indigo-600 px-3 py-1 text-xs text-white">
          Crear
        </button>
      </form>
      <div className="overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Número</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2">Total</th>
              <th className="px-3 py-2">PDF</th>
              <th className="px-3 py-2">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((quote) => (
              <tr key={quote.id} className="border-t">
                <td className="px-3 py-2">{quote.number}</td>
                <td className="px-3 py-2">{quote.status}</td>
                <td className="px-3 py-2">{quote.total ?? 0}</td>
                <td className="px-3 py-2 text-xs text-slate-500">
                  {quote.pdf_path ? "Generado" : "-"}
                </td>
                <td className="px-3 py-2">
                  <div className="flex gap-2">
                    <button
                      disabled={loading}
                      onClick={() => generatePdf(quote.id)}
                      className="rounded border px-2 py-1 text-xs"
                    >
                      PDF
                    </button>
                    <button
                      disabled={loading}
                      onClick={() => sendQuote(quote.id)}
                      className="rounded border px-2 py-1 text-xs"
                    >
                      Enviar
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-400" colSpan={5}>
                  Sin cotizaciones
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
