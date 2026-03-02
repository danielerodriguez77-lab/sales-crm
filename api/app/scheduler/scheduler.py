from apscheduler.schedulers.background import BackgroundScheduler

from app.scheduler.jobs import (
    payment_reminder_check,
    sla_first_contact_check,
    stale_opportunity_check,
)


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(sla_first_contact_check, "interval", minutes=15, id="sla_first_contact")
    scheduler.add_job(stale_opportunity_check, "interval", hours=6, id="stale_opps")
    scheduler.add_job(payment_reminder_check, "interval", hours=12, id="payment_reminders")
    scheduler.start()
    return scheduler
