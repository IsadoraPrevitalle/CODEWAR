from fastapi import FastAPI, Depends, Request, HTTPException, status, Body, Query
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_400_BAD_REQUEST
from fastapi.encoders import jsonable_encoder
import schemas
from database import SessionLocal, engine, Base
from models import Usuario, Tarefa, Historico
from sqlalchemy.orm import Session
from dicttoxml import dicttoxml
from typing import Optional

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=HTTP_400_BAD_REQUEST,
        content={
            "status": "Status 400 - ERROR:",
            "errors": exc.errors()
        },
    )

def format_response(data: dict, request, status_code: int = 200):
    accept = request.headers.get("accept", "application/json").lower()
    if "application/xml" in accept:
        xml = dicttoxml(data, custom_root='response', attr_type=False)
        return Response(content=xml, media_type="application/xml", status_code=status_code)
    else:
        return JSONResponse(content=data, status_code=status_code)


#Inicio da API
@app.get("/")
async def root():
    return {'mensagem': 
                'Seja bem vindo a API de gestão de tarefas', 
            'descrição':
                'Essa API tem como objetivo lhe ajudar no gerenciamento de equipes e trabalhos com base em um sistema de pontuação'
                } 

# POST - Adicionar uma Tarefa
@app.post("/task/", status_code=status.HTTP_201_CREATED)
async def criar_tarefa(tarefa: schemas.TaskCreate, db: Session = Depends(get_db)):
    try:
        nova_tarefa = Tarefa(**tarefa.dict())
        db.add(nova_tarefa)
        db.commit()
        db.refresh(nova_tarefa)
        return nova_tarefa
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao criar tarefa: {str(e)}")
    
# GET - Buscar uma tarefa (Opcional ser por ID)    
@app.get("/task/", status_code=status.HTTP_200_OK)
async def buscar_tarefa(request: Request, id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    if id is not None:
        Busca_tarefa = db.query(Tarefa).filter(Tarefa.idtarefa == id).first()
        if not Busca_tarefa:
            return format_response({"mensage": "Essa tarefa não pode ser encontrada"}, request, status_code=404)
        task_out = schemas.TaskOut.from_orm(Busca_tarefa)
        task_dict = jsonable_encoder(task_out)
        
        return format_response(task_dict, request)
    else:
        Busca_tarefa = db.query(Tarefa).all()
        tarefas_out = [jsonable_encoder(schemas.TaskOut.from_orm(t)) for t in Busca_tarefa]
        return format_response(tarefas_out, request)

# DELETE - Apaga uma tarefa via ID
@app.delete("/task/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_tarefa(id: int, db: Session = Depends(get_db)):
    tarefa = db.query(Tarefa).filter(Tarefa.idtarefa == id).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Essa tarefa não pode ser deletada")
    
    db.delete(tarefa)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela tarefa
@app.patch("/task/{id}", status_code=status.HTTP_200_OK)
async def atualizar_tarefa(id: int, tarefa_update: schemas.TaskUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    tarefa_db = db.query(Tarefa).filter(Tarefa.idtarefa == id).first()
    if not tarefa_db:
        return format_response({"mensage": "Tarefa não pode ser editada"}, request, status_code=404)
    
    update_data = tarefa_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tarefa_db, key, value)

    db.commit()
    db.refresh(tarefa_db)

    task_out = schemas.TaskOut.from_orm(tarefa_db)
    task_dict = jsonable_encoder(task_out)
    return format_response(task_dict, request)
