from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from database import Base
from datetime import datetime, timezone

class Recompensa(Base):
    __tablename__ = "recompensa"
    idrecom = Column(Integer, primary_key=True, index=True)
    idhist = Column(Integer, ForeignKey("historico.idhist"), nullable=False)
    nome = Column(String(30), nullable=False)
    descricao = Column(String(100), nullable=False)
    imagem_url = Column(String, nullable=True)
    pontos = Column(Integer, nullable=False)

class Historico(Base):
    __tablename__ = "historico"
    idhist = Column(Integer, primary_key=True, index=True)
    nome = Column(String(30), nullable=False)
    descricao = Column(String(100), nullable=False)
    idusuario = Column(Integer, ForeignKey("usuario.idusuario"), nullable=False)
    idtarefa =  Column(Integer, ForeignKey("tarefa.idtarefa"), nullable=False)
    finalizada = Column(Boolean, nullable=False) 
    dt_inclusao = Column(DateTime, default=datetime.now(timezone.utc))
    dt_edicao = Column(DateTime, nullable=True, default=None, onupdate=datetime.now(timezone.utc))
    dt_exclusao = Column(DateTime, nullable=True, default=None)
    
class Usuario(Base):
    __tablename__ = "usuario"
    idusuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(30), nullable=False)
    idade = Column(Integer, nullable=False)
    sexo = Column(String(20), nullable=False)
    dt_inclusao = Column(DateTime, default=datetime.now(timezone.utc))
    dt_edicao = Column(DateTime, nullable=True, default=None, onupdate=datetime.now(timezone.utc))
    dt_exclusao = Column(DateTime, nullable=True, default=None)
    
class Tarefa(Base):
    __tablename__ = "tarefa"
    idtarefa = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(100), nullable=False)
    descricao = Column(String(300), nullable=False) 
    pontos = Column(Integer, nullable=False)
    dt_inclusao = Column(DateTime, default=datetime.now(timezone.utc))
    dt_edicao = Column(DateTime, nullable=True, default=None, onupdate=datetime.now(timezone.utc))
    dt_exclusao = Column(DateTime, nullable=True, default=None)
    