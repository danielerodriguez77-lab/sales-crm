import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { useAuth } from "../lib/AuthContext";

const BUCKETS = [
  { label: "0-30", min: 0, max: 30 },
  { label: "31-60", min: 31, max: 60 },
  { label: "61-90", min: 61, max: 90 },
  { label: "90+", min: 91, max: 10000 }
];

type Invoice = {
  id: number;
  sales_order_id: number;
  number: string;
  issue_date: string;
  due_date: string;
  total: number;
  status: string;
  invoice_type: string;
};

type SalesOrder = {
  id: number;
  opportunity_id: number;
  order_date?: string | null;
  total?: number | null;
};

type Opportunity = {
  id: number;
  company_name?: string | null;
  person_name?: string | null;
};

type Quote = {
  id: number;
  opportunity_id: number;
  status: string;
};

type Payment = {
  id: number;
  invoice_id: number;
  amount: number;
  date?: string;
  method?: string;
};

const PAYMENT_METHODS = [
  { value: "transfer", label: "Transferencia" },
  { value: "cash", label: "Efectivo" },
  { value: "card", label: "Tarjeta" },
  { value: "check", label: "Cheque" },
  { value: "other", label: "Otro" }
];

const INVOICE_TYPES = [
  { value: "total", label: "Total" },
  { value: "partial", label: "Parcial" },
  { value: "advance_reservation", label: "Adelanto (Reserva)" }
];

const INVOICE_STATUSES = [
  { value: "draft", label: "Borrador" },
  { value: "issued", label: "Emitida" },
  { value: "partial", label: "Parcial" },
  { value: "paid", label: "Pagada" },
  { value: "overdue", label: "Vencida" }
];

export default function InvoicesPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<Invoice[]>([]);
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTotal, setEditTotal] = useState(0);
  const [editOpportunityId, setEditOpportunityId] = useState<number | null>(null);
  const [editOrderId, setEditOrderId] = useState<number | null>(null);
  const [payingInvoiceId, setPayingInvoiceId] = useState<number | null>(null);
  const [paymentAmount, setPaymentAmount] = useState(0);
  const [paymentMethod, setPaymentMethod] = useState(PAYMENT_METHODS[0].value);
  const [paymentDate, setPaymentDate] = useState("");
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState<number | null>(null);
  const [editingPaymentId, setEditingPaymentId] = useState<number | null>(null);
  const [editPaymentAmount, setEditPaymentAmount] = useState(0);
  const [editPaymentDate, setEditPaymentDate] = useState("");
  const [editPaymentMethod, setEditPaymentMethod] = useState(PAYMENT_METHODS[0].value);
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const [createOrderOppId, setCreateOrderOppId] = useState<number | null>(null);
  const [createOrderError, setCreateOrderError] = useState<string | null>(null);
  const [createInvoiceOppId, setCreateInvoiceOppId] = useState<number | null>(null);
  const [createInvoiceOrderId, setCreateInvoiceOrderId] = useState<number | null>(null);
  const [createInvoiceType, setCreateInvoiceType] = useState(INVOICE_TYPES[0].value);
  const [createInvoiceStatus, setCreateInvoiceStatus] = useState(INVOICE_STATUSES[1].value);
  const [createInvoiceAmount, setCreateInvoiceAmount] = useState(0);
  const [createInvoiceIssueDate, setCreateInvoiceIssueDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [createInvoiceDueDate, setCreateInvoiceDueDate] = useState(
    new Date(Date.now() + 10 * 86400000).toISOString().slice(0, 10)
  );
  const [createInvoiceError, setCreateInvoiceError] = useState<string | null>(null);
  async function load() {
    const [invoicesData, ordersData, oppsData, quotesData, paymentsData] = await Promise.all([
      apiFetch<Invoice[]>("/api/invoices", { token: token || undefined }),
      apiFetch<SalesOrder[]>("/api/sales-orders", { token: token || undefined }),
      apiFetch<Opportunity[]>("/api/opportunities", { token: token || undefined }),
      apiFetch<Quote[]>("/api/quotes", { token: token || undefined }),
      apiFetch<Payment[]>("/api/payments", { token: token || undefined })
    ]);
    setItems(invoicesData);
    setOrders(ordersData);
    setOpps(oppsData);
    setQuotes(quotesData);
    setPayments(paymentsData);
  }

  useEffect(() => {
    load();
  }, []);

  const ordersById = useMemo(() => {
    return orders.reduce<Record<number, SalesOrder>>((acc, order) => {
      acc[order.id] = order;
      return acc;
    }, {});
  }, [orders]);

  const ordersByOpp = useMemo(() => {
    return orders.reduce<Record<number, SalesOrder[]>>((acc, order) => {
      acc[order.opportunity_id] = acc[order.opportunity_id] || [];
      acc[order.opportunity_id].push(order);
      return acc;
    }, {});
  }, [orders]);

  const oppsById = useMemo(() => {
    return opps.reduce<Record<number, Opportunity>>((acc, opp) => {
      acc[opp.id] = opp;
      return acc;
    }, {});
  }, [opps]);

  const oppsWithOrders = useMemo(() => {
    return opps.filter((opp) => (ordersByOpp[opp.id] || []).length > 0);
  }, [opps, ordersByOpp]);

  const oppsWithoutOrders = useMemo(() => {
    return opps.filter((opp) => (ordersByOpp[opp.id] || []).length === 0);
  }, [opps, ordersByOpp]);

  const sentQuotesByOpp = useMemo(() => {
    return quotes.reduce<Record<number, boolean>>((acc, quote) => {
      if (quote.status === "sent" || quote.status === "accepted") {
        acc[quote.opportunity_id] = true;
      }
      return acc;
    }, {});
  }, [quotes]);

  const paidByInvoice = useMemo(() => {
    return payments.reduce<Record<number, number>>((acc, p) => {
      acc[p.invoice_id] = (acc[p.invoice_id] || 0) + p.amount;
      return acc;
    }, {});
  }, [payments]);

  const ordersWithOpp = useMemo(() => {
    return orders.filter((order) => oppsById[order.opportunity_id]);
  }, [orders, oppsById]);

  const canCreateOrder =
    createOrderOppId !== null && Boolean(sentQuotesByOpp[createOrderOppId]);

  const selectedCreateOrder = ordersById[createInvoiceOrderId || 0];

  useEffect(() => {
    if (createInvoiceType === "total" && selectedCreateOrder?.total != null) {
      setCreateInvoiceAmount(Number(selectedCreateOrder.total));
    }
  }, [createInvoiceType, selectedCreateOrder]);

  useEffect(() => {
    if (!createInvoiceOppId) {
      setCreateInvoiceOrderId(null);
      return;
    }
    const ordersForOpp = ordersByOpp[createInvoiceOppId] || [];
    setCreateInvoiceOrderId(ordersForOpp[0]?.id ?? null);
  }, [createInvoiceOppId, ordersByOpp]);

  function opportunityLabel(invoice: Invoice) {
    const order = ordersById[invoice.sales_order_id];
    if (!order) return "-";
    const opp = oppsById[order.opportunity_id];
    if (!opp) return `Oportunidad ${order.opportunity_id}`;
    return opp.company_name || opp.person_name || `Oportunidad ${opp.id}`;
  }

  function opportunityId(invoice: Invoice) {
    const order = ordersById[invoice.sales_order_id];
    return order?.opportunity_id;
  }

  function invoiceTypeLabel(value: string) {
    return INVOICE_TYPES.find((type) => type.value === value)?.label || value;
  }

  function pendingAmount(inv: Invoice) {
    const paid = paidByInvoice[inv.id] || 0;
    return Math.max(inv.total - paid, 0);
  }

  const today = new Date();
  const agingTotals: Record<string, number> = { "0-30": 0, "31-60": 0, "61-90": 0, "90+": 0 };
  items.forEach((inv) => {
    const due = new Date(inv.due_date);
    const diffDays = Math.max(0, Math.floor((today.getTime() - due.getTime()) / 86400000));
    const bucket = BUCKETS.find((b) => diffDays >= b.min && diffDays <= b.max);
    if (bucket) agingTotals[bucket.label] += inv.total;
  });

  function startEdit(inv: Invoice) {
    if (inv.status === "paid") return;
    setEditingId(inv.id);
    setEditTotal(inv.total);
    const order = ordersById[inv.sales_order_id];
    if (order) {
      setEditOpportunityId(order.opportunity_id);
      setEditOrderId(order.id);
    }
  }

  async function saveEdit(inv: Invoice) {
    if (!token) return;
    await apiFetch(`/api/invoices/${inv.id}`, {
      method: "PATCH",
      token: token || undefined,
      body: JSON.stringify({ total: editTotal, sales_order_id: editOrderId })
    });
    setEditingId(null);
    await load();
  }

  function cancelEdit() {
    setEditingId(null);
  }

  async function createOrderForOpportunity() {
    if (!token || !createOrderOppId) return;
    setCreateOrderError(null);
    if (!sentQuotesByOpp[createOrderOppId]) {
      setCreateOrderError("Esta oportunidad no tiene cotización enviada.");
      return;
    }
    try {
      const currentEditingId = editingId;
      const created = await apiFetch<SalesOrder>(`/api/sales-orders/from-opportunity`, {
        method: "POST",
        token: token || undefined,
        body: JSON.stringify({ opportunity_id: createOrderOppId })
      });
      if (currentEditingId !== null) {
        setEditOpportunityId(created.opportunity_id);
        setEditOrderId(created.id);
      }
      setCreateOrderOppId(null);
      await load();
    } catch (err) {
      setCreateOrderError("No se pudo crear la orden (requiere cotización enviada).");
    }
  }

  async function createInvoice() {
    if (!token || !createInvoiceOrderId) return;
    setCreateInvoiceError(null);
    const order = ordersById[createInvoiceOrderId];
    if (!order) return;
    const orderTotal = Number(order.total ?? 0);
    if (createInvoiceType !== "total" && createInvoiceAmount <= 0) {
      setCreateInvoiceError("El monto debe ser mayor a 0.");
      return;
    }
    if (createInvoiceAmount > orderTotal) {
      setCreateInvoiceError("El monto no puede superar el total de la orden.");
      return;
    }
    const total =
      createInvoiceType === "total" ? orderTotal : Number(createInvoiceAmount);
    await apiFetch(`/api/invoices`, {
      method: "POST",
      token: token || undefined,
      body: JSON.stringify({
        sales_order_id: createInvoiceOrderId,
        issue_date: createInvoiceIssueDate,
        due_date: createInvoiceDueDate,
        total,
        status: createInvoiceStatus,
        invoice_type: createInvoiceType
      })
    });
    setCreateInvoiceOrderId(null);
    setCreateInvoiceOppId(null);
    setCreateInvoiceType(INVOICE_TYPES[0].value);
    setCreateInvoiceStatus(INVOICE_STATUSES[1].value);
    setCreateInvoiceAmount(0);
    await load();
  }

  function startPayment(inv: Invoice) {
    setPayingInvoiceId(inv.id);
    setPaymentAmount(pendingAmount(inv));
    setPaymentMethod(PAYMENT_METHODS[0].value);
    setPaymentDate(new Date().toISOString().slice(0, 10));
    setPaymentError(null);
  }

  async function submitPayment() {
    if (!token || !payingInvoiceId) return;
    const invoice = items.find((i) => i.id === payingInvoiceId);
    if (!invoice) return;
    const pending = pendingAmount(invoice);
    if (paymentAmount <= 0) {
      setPaymentError("El monto debe ser mayor a 0");
      return;
    }
    if (paymentAmount > pending) {
      setPaymentError("El monto no puede exceder el saldo pendiente");
      return;
    }

    await apiFetch(`/api/payments`, {
      method: "POST",
      token: token || undefined,
      body: JSON.stringify({
        invoice_id: payingInvoiceId,
        amount: paymentAmount,
        date: paymentDate,
        method: paymentMethod
      })
    });
    setPayingInvoiceId(null);
    await load();
  }

  function cancelPayment() {
    setPayingInvoiceId(null);
  }

  const invoicePayments = (invoiceId: number) =>
    payments.filter((p) => p.invoice_id === invoiceId);

  function startEditPayment(payment: Payment) {
    setEditingPaymentId(payment.id);
    setEditPaymentAmount(payment.amount);
    setEditPaymentDate(payment.date || new Date().toISOString().slice(0, 10));
    setEditPaymentMethod(payment.method || PAYMENT_METHODS[0].value);
  }

  async function saveEditPayment(payment: Payment) {
    if (!token) return;
    await apiFetch(`/api/payments/${payment.id}`, {
      method: "PATCH",
      token: token || undefined,
      body: JSON.stringify({
        amount: editPaymentAmount,
        date: editPaymentDate,
        method: editPaymentMethod
      })
    });
    setEditingPaymentId(null);
    await load();
  }

  function cancelEditPayment() {
    setEditingPaymentId(null);
  }

  async function deletePayment(paymentId: number) {
    if (!token) return;
    await apiFetch(`/api/payments/${paymentId}`, {
      method: "DELETE",
      token: token || undefined
    });
    setConfirmDeleteId(null);
    await load();
  }

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Facturas</h2>
        <button onClick={load} className="rounded border px-3 py-1 text-sm hover:bg-slate-100">
          Recargar
        </button>
      </div>

      <div className="mb-4 rounded-lg border bg-white p-3 text-sm">
        <div className="mb-2 font-semibold">Crear orden automática</div>
        <div className="grid gap-2 md:grid-cols-3">
          <select
            className="rounded border px-2 py-1"
            value={createOrderOppId ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              setCreateOrderOppId(value ? Number(value) : null);
              setCreateOrderError(null);
            }}
          >
            <option value="">Oportunidades sin orden</option>
            {oppsWithoutOrders.map((opp) => (
              <option key={opp.id} value={opp.id}>
                {opp.company_name || opp.person_name || `Oportunidad ${opp.id}`}
              </option>
            ))}
          </select>
          <button
            onClick={createOrderForOpportunity}
            className={`rounded border px-2 py-1 text-xs ${
              canCreateOrder ? "" : "cursor-not-allowed opacity-60"
            }`}
            disabled={!canCreateOrder}
          >
            Crear orden
          </button>
          {createOrderOppId && !sentQuotesByOpp[createOrderOppId] ? (
            <div className="text-xs text-red-600">
              Esta oportunidad no tiene cotización enviada.
            </div>
          ) : null}
          {createOrderError ? (
            <div className="text-xs text-red-600">{createOrderError}</div>
          ) : null}
        </div>
      </div>

      <div className="mb-4 rounded-lg border bg-white p-3 text-sm">
        <div className="mb-2 font-semibold">Crear factura (desde orden)</div>
        <div className="grid gap-2 md:grid-cols-3">
          <select
            className="rounded border px-2 py-1"
            value={createInvoiceOppId ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              setCreateInvoiceOppId(value ? Number(value) : null);
              setCreateInvoiceError(null);
            }}
          >
            <option value="">Seleccionar oportunidad</option>
            {oppsWithOrders.map((opp) => (
              <option key={opp.id} value={opp.id}>
                {opp.company_name || opp.person_name || `Oportunidad ${opp.id}`}
              </option>
            ))}
          </select>
          <select
            className="rounded border px-2 py-1"
            value={createInvoiceOrderId ?? ""}
            onChange={(e) => {
              const value = e.target.value;
              setCreateInvoiceOrderId(value ? Number(value) : null);
            }}
          >
            <option value="">Seleccionar orden</option>
            {(ordersByOpp[createInvoiceOppId || 0] || ordersWithOpp).map((order) => (
              <option key={order.id} value={order.id}>
                Orden #{order.id}
                {order.order_date ? ` (${order.order_date.slice(0, 10)})` : ""}
              </option>
            ))}
          </select>
          <select
            className="rounded border px-2 py-1"
            value={createInvoiceType}
            onChange={(e) => setCreateInvoiceType(e.target.value)}
          >
            {INVOICE_TYPES.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
        <div className="mt-2 grid gap-2 md:grid-cols-4">
          <input
            className="rounded border px-2 py-1"
            type="number"
            value={createInvoiceAmount}
            onChange={(e) => setCreateInvoiceAmount(Number(e.target.value))}
            disabled={createInvoiceType === "total"}
          />
          <input
            className="rounded border px-2 py-1"
            type="date"
            value={createInvoiceIssueDate}
            onChange={(e) => setCreateInvoiceIssueDate(e.target.value)}
          />
          <input
            className="rounded border px-2 py-1"
            type="date"
            value={createInvoiceDueDate}
            onChange={(e) => setCreateInvoiceDueDate(e.target.value)}
          />
          <select
            className="rounded border px-2 py-1"
            value={createInvoiceStatus}
            onChange={(e) => setCreateInvoiceStatus(e.target.value)}
          >
            {INVOICE_STATUSES.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>
        </div>
        {selectedCreateOrder?.total != null ? (
          <div className="mt-2 text-xs text-slate-500">
            Total orden: {Number(selectedCreateOrder.total)}
          </div>
        ) : null}
        {createInvoiceError ? (
          <div className="mt-2 text-xs text-red-600">{createInvoiceError}</div>
        ) : null}
        <div className="mt-2">
          <button
            onClick={createInvoice}
            className="rounded bg-indigo-600 px-3 py-1 text-xs text-white"
          >
            Crear factura
          </button>
        </div>
      </div>

      <div className="mb-4 grid gap-3 md:grid-cols-4">
        {BUCKETS.map((bucket) => (
          <div key={bucket.label} className="rounded border bg-white p-3">
            <div className="text-xs text-slate-500">Aging {bucket.label}</div>
            <div className="text-lg font-semibold">{agingTotals[bucket.label]}</div>
          </div>
        ))}
      </div>
      <div className="overflow-hidden rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-left">
            <tr>
              <th className="px-3 py-2">Número</th>
              <th className="px-3 py-2">Oportunidad</th>
              <th className="px-3 py-2">Emisión</th>
              <th className="px-3 py-2">Vence</th>
              <th className="px-3 py-2">Total</th>
              <th className="px-3 py-2">Pagado</th>
              <th className="px-3 py-2">Pendiente</th>
              <th className="px-3 py-2">Estado</th>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {items.map((inv) => (
              <tr key={inv.id} className="border-t">
                <td className="px-3 py-2">{inv.number}</td>
                <td className="px-3 py-2">
                  {editingId === inv.id ? (
                    <div className="space-y-2">
                      <select
                        className="w-full rounded border px-2 py-1 text-xs"
                        value={editOpportunityId ?? ""}
                        onChange={(e) => {
                          const value = Number(e.target.value);
                          setEditOpportunityId(value);
                          const ordersForOpp = ordersByOpp[value] || [];
                          setEditOrderId(ordersForOpp[0]?.id ?? null);
                        }}
                      >
                        <option value="">Seleccionar oportunidad</option>
                        {oppsWithOrders.map((opp) => (
                          <option key={opp.id} value={opp.id}>
                            {opp.company_name || opp.person_name || `Oportunidad ${opp.id}`}
                          </option>
                        ))}
                      </select>
                      <select
                        className="w-full rounded border px-2 py-1 text-xs"
                        value={editOrderId ?? ""}
                        onChange={(e) => setEditOrderId(Number(e.target.value))}
                      >
                        <option value="">Seleccionar orden</option>
                        {(ordersByOpp[editOpportunityId || 0] || []).map((order) => (
                          <option key={order.id} value={order.id}>
                            Orden #{order.id}
                            {order.order_date ? ` (${order.order_date.slice(0, 10)})` : ""}
                          </option>
                        ))}
                      </select>
                    </div>
                  ) : opportunityId(inv) ? (
                    <Link className="text-indigo-600" to={`/oportunidades/${opportunityId(inv)}`}>
                      {`${opportunityLabel(inv)} (Orden #${inv.sales_order_id}${
                        ordersById[inv.sales_order_id]?.order_date
                          ? ` · ${ordersById[inv.sales_order_id]?.order_date?.slice(0, 10)}`
                          : ""
                      })`}
                    </Link>
                  ) : (
                    opportunityLabel(inv)
                  )}
                </td>
                <td className="px-3 py-2">{inv.issue_date}</td>
                <td className="px-3 py-2">{inv.due_date}</td>
                <td className="px-3 py-2">
                  {editingId === inv.id ? (
                    <input
                      className="w-24 rounded border px-2 py-1 text-xs"
                      type="number"
                      value={editTotal}
                      onChange={(e) => setEditTotal(Number(e.target.value))}
                    />
                  ) : (
                    inv.total
                  )}
                </td>
                <td className="px-3 py-2">{paidByInvoice[inv.id] || 0}</td>
                <td className="px-3 py-2">{pendingAmount(inv)}</td>
                <td className="px-3 py-2">{inv.status}</td>
                <td className="px-3 py-2">{invoiceTypeLabel(inv.invoice_type)}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-2">
                    {editingId === inv.id ? (
                      <>
                        <button
                          onClick={() => saveEdit(inv)}
                          className="rounded border px-2 py-1 text-xs"
                        >
                          Guardar
                        </button>
                        <button
                          onClick={cancelEdit}
                          className="rounded border px-2 py-1 text-xs"
                        >
                          Cancelar
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => startEdit(inv)}
                        className={`rounded border px-2 py-1 text-xs ${
                          inv.status === "paid" ? "cursor-not-allowed opacity-50" : ""
                        }`}
                        disabled={inv.status === "paid"}
                      >
                        Editar monto
                      </button>
                    )}
                    <button
                      onClick={() => startPayment(inv)}
                      className="rounded border px-2 py-1 text-xs"
                    >
                      Registrar pago
                    </button>
                    <button
                      onClick={() => setSelectedInvoiceId(inv.id)}
                      className="rounded border px-2 py-1 text-xs"
                    >
                      Ver pagos
                    </button>
                  </div>
                  <div className="mt-2 text-[11px] text-slate-500">
                    {`Pagado ${paidByInvoice[inv.id] || 0} / Total ${inv.total}`}
                  </div>
                </td>
              </tr>
            ))}
            {!items.length ? (
              <tr>
                <td className="px-3 py-6 text-center text-slate-400" colSpan={10}>
                  Sin facturas
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      {payingInvoiceId ? (
        <div className="mt-4 rounded-lg border bg-white p-4 text-sm">
          <div className="mb-2 font-semibold">Registrar pago</div>
          {paymentError ? <div className="mb-2 text-xs text-red-600">{paymentError}</div> : null}
          <div className="grid gap-2 md:grid-cols-4">
            <input
              className="rounded border px-2 py-1"
              type="number"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(Number(e.target.value))}
            />
            <input
              className="rounded border px-2 py-1"
              type="date"
              value={paymentDate}
              onChange={(e) => setPaymentDate(e.target.value)}
            />
            <select
              className="rounded border px-2 py-1"
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
            >
              {PAYMENT_METHODS.map((method) => (
                <option key={method.value} value={method.value}>
                  {method.label}
                </option>
              ))}
            </select>
            <div className="flex gap-2">
              <button
                onClick={submitPayment}
                className="rounded bg-indigo-600 px-3 py-1 text-xs text-white"
              >
                Guardar pago
              </button>
              <button
                onClick={cancelPayment}
                className="rounded border px-3 py-1 text-xs"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {selectedInvoiceId ? (
        <div className="mt-4 rounded-lg border bg-white p-4 text-sm">
          <div className="mb-2 flex items-center justify-between">
            <div className="font-semibold">Pagos de factura #{selectedInvoiceId}</div>
            <button
              onClick={() => setSelectedInvoiceId(null)}
              className="rounded border px-2 py-1 text-xs"
            >
              Cerrar
            </button>
          </div>
          <div className="space-y-2">
            {invoicePayments(selectedInvoiceId).map((payment) => (
              <div key={payment.id} className="rounded border px-2 py-2">
                {editingPaymentId === payment.id ? (
                  <div className="grid gap-2 md:grid-cols-4">
                    <input
                      className="rounded border px-2 py-1"
                      type="number"
                      value={editPaymentAmount}
                      onChange={(e) => setEditPaymentAmount(Number(e.target.value))}
                    />
                    <input
                      className="rounded border px-2 py-1"
                      type="date"
                      value={editPaymentDate}
                      onChange={(e) => setEditPaymentDate(e.target.value)}
                    />
                    <select
                      className="rounded border px-2 py-1"
                      value={editPaymentMethod}
                      onChange={(e) => setEditPaymentMethod(e.target.value)}
                    >
                      {PAYMENT_METHODS.map((method) => (
                        <option key={method.value} value={method.value}>
                          {method.label}
                        </option>
                      ))}
                    </select>
                    <div className="flex gap-2">
                      <button
                        onClick={() => saveEditPayment(payment)}
                        className="rounded border px-2 py-1 text-xs"
                      >
                        Guardar
                      </button>
                      <button
                        onClick={cancelEditPayment}
                        className="rounded border px-2 py-1 text-xs"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{payment.amount}</div>
                      <div className="text-xs text-slate-500">
                        {payment.date || "-"} · {payment.method || "-"}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditPayment(payment)}
                        className="rounded border px-2 py-1 text-xs"
                      >
                        Editar
                      </button>
                      {confirmDeleteId === payment.id ? (
                        <div className="flex items-center gap-2">
                          <span className="text-[11px] text-slate-500">¿Eliminar?</span>
                          <button
                            onClick={() => deletePayment(payment.id)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            Sí
                          </button>
                          <button
                            onClick={() => setConfirmDeleteId(null)}
                            className="rounded border px-2 py-1 text-xs"
                          >
                            No
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setConfirmDeleteId(payment.id)}
                          className="rounded border px-2 py-1 text-xs"
                        >
                          Eliminar
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
            {!invoicePayments(selectedInvoiceId).length ? (
              <div className="text-xs text-slate-400">Sin pagos</div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
