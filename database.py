from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

url_db = "sqlite:///./tarefas.db"

engine = create_engine(
    url_db,
    connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()