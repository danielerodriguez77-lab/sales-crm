from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.opportunities import router as opportunities_router
from app.api.routes.activities import router as activities_router
from app.api.routes.quotes import router as quotes_router
from app.api.routes.sales_orders import router as sales_orders_router
from app.api.routes.invoices import router as invoices_router
from app.api.routes.payments import router as payments_router
from app.api.routes.tasks import router as tasks_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.contacts import router as contacts_router
from app.api.routes.products import router as products_router
from app.api.routes.dashboards import router as dashboards_router
from app.api.routes.reports import router as reports_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(opportunities_router)
api_router.include_router(activities_router)
api_router.include_router(quotes_router)
api_router.include_router(sales_orders_router)
api_router.include_router(invoices_router)
api_router.include_router(payments_router)
api_router.include_router(tasks_router)
api_router.include_router(alerts_router)
api_router.include_router(contacts_router)
api_router.include_router(products_router)
api_router.include_router(dashboards_router)
api_router.include_router(reports_router)


@api_router.get("/ping")
def ping():
    return {"message": "pong"}
