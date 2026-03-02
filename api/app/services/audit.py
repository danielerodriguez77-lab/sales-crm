from datetime import datetime, timezone

from fastapi.encoders import jsonable_encoder

from app.models.audit_log import AuditLog


def _model_to_dict(obj) -> dict:
    data = {}
    for key, value in obj.__dict__.items():
        if key.startswith("_"):
            continue
        data[key] = value
    return jsonable_encoder(data)


def log_action(
    db,
    actor_id: int | None,
    entity: str,
    entity_id: str,
    action: str,
    before=None,
    after=None,
):
    entry = AuditLog(
        actor_id=actor_id,
        entity=entity,
        entity_id=str(entity_id),
        action=action,
        before=before,
        after=after,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(entry)


def snapshot(obj) -> dict:
    return _model_to_dict(obj)
