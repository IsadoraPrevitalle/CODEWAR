from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config_log import logger

url_db = "sqlite:///./tarefas.db"

engine = create_engine(
    url_db,
    connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        logger.info("A sessão com o banco de dados foi inicializada com suceso")
        yield db
    finally:
        logger.info('A sessão com o banco de dados foi finalizada com sucesso')
        db.close()