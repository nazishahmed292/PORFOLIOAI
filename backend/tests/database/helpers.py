from sqlalchemy import func, select
from sqlalchemy.orm import Session


def count(db: Session, model) -> int:
    return db.execute(select(func.count()).select_from(model)).scalar_one()
