import enum


class UserRole(str, enum.Enum):
    seller = "seller"
    supervisor = "supervisor"
    manager = "manager"
    admin = "admin"


class OpportunityType(str, enum.Enum):
    lead = "lead"
    opportunity = "opportunity"


class PipelineStage(str, enum.Enum):
    lead_nuevo = "lead_nuevo"
    calificado = "calificado"
    contacto_seguimiento = "contacto_seguimiento"
    oferta_enviada = "oferta_enviada"
    negociacion = "negociacion"
    ganado = "ganado"
    facturacion = "facturacion"
    cobro_parcial = "cobro_parcial"
    pagado_cerrado = "pagado_cerrado"
    perdido = "perdido"


class ActivityType(str, enum.Enum):
    call = "call"
    reunion_online = "reunion_online"
    reunion_presencial = "reunion_presencial"
    visit = "visit"
    whatsapp = "whatsapp"
    email = "email"
    demo = "demo"
    other = "other"


class QuoteStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    accepted = "accepted"
    rejected = "rejected"


class ApprovalStatus(str, enum.Enum):
    not_required = "not_required"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class SalesOrderStatus(str, enum.Enum):
    open = "open"
    cancelled = "cancelled"
    fulfilled = "fulfilled"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    issued = "issued"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class InvoiceType(str, enum.Enum):
    total = "total"
    partial = "partial"
    advance_reservation = "advance_reservation"


class PaymentMethod(str, enum.Enum):
    cash = "cash"
    transfer = "transfer"
    card = "card"
    check = "check"
    other = "other"


class TaskStatus(str, enum.Enum):
    open = "open"
    done = "done"


class TaskType(str, enum.Enum):
    sla_first_contact = "sla_first_contact"
    stale_opportunity = "stale_opportunity"
    payment_due = "payment_due"
    payment_overdue = "payment_overdue"


class AlertScope(str, enum.Enum):
    manager = "manager"
    seller = "seller"
    all = "all"


class AlertType(str, enum.Enum):
    sla_first_contact = "sla_first_contact"
    stale_opportunity = "stale_opportunity"
    payment_due = "payment_due"
    payment_overdue = "payment_overdue"
