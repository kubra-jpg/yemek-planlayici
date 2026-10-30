from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "yemek.db"

engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db():
    """Tablolar yoksa oluşturur."""
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    """Bir işlem oturumu açar; hata yoksa kaydeder, varsa geri alır."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()