from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class HistBase(BaseModel):
    nome: str
    descricao: str
    idusuario: int
    idtarefa: int
    finalizada: bool

class HistCreate(HistBase):
    pass

class HistUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    finalizada: Optional[bool] = None

class HistOut(HistBase):
    idhist: int
    dt_inclusao: datetime
    dt_edicao: datetime
    dt_alteracao: datetime

    model_config = {
        "from_attributes": True
        }

class UserBase(BaseModel):
    nome: str
    idade: int
    sexo: str

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    nome: Optional[str] = None
    idade: Optional[int] = None
    sexo: Optional[str] = None

class UserOut(UserBase):
    idusuario: int
    dt_inclusao: datetime
    dt_edicao: datetime
    dt_alteracao: datetime

    model_config = {
        "from_attributes": True
        }

class TaskBase(BaseModel):
    titulo: str
    descricao: str
    pontos: int

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    pontos: Optional[int] = None

class TaskOut(TaskBase):
    idtarefa: int
    dt_inclusao: datetime
    dt_edicao: Optional[datetime] = None
    dt_alteracao: Optional[datetime] = None

    model_config = {
        "from_attributes": True
        }