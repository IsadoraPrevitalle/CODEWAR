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
from datetime import datetime

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

#-------------------------------------------------------------- TAREFA ------------------------------------------------------
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
        busca_tarefa = db.query(Tarefa).filter(Tarefa.idtarefa == id, Tarefa.dt_exclusao == None).first()
        if not busca_tarefa:
            return format_response({"mensage": "Essa tarefa não pode ser encontrada"}, request, status_code=404)
        task_out = schemas.TaskOut.from_orm(busca_tarefa)
        task_dict = jsonable_encoder(task_out)
        
        return format_response(task_dict, request)
    else:
        busca_tarefa = db.query(Tarefa).all()
        tarefas_out = [jsonable_encoder(schemas.TaskOut.from_orm(t)) for t in busca_tarefa]
        return format_response(tarefas_out, request)

# DELETE - Apaga uma tarefa via ID
@app.delete("/task/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_tarefa(id: int, db: Session = Depends(get_db)):
    tarefa = db.query(Tarefa).filter(Tarefa.idtarefa == id, Tarefa.dt_exclusao == None).first()
    if not tarefa:
        raise HTTPException(status_code=404, detail="Essa tarefa não pode ser deletada")
    
    tarefa.dt_exclusao = datetime.utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela tarefa
@app.patch("/task/{id}", status_code=status.HTTP_200_OK)
async def atualizar_tarefa(id: int, tarefa_update: schemas.TaskUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    tarefa_db = db.query(Tarefa).filter(Tarefa.idtarefa == id, Tarefa.dt_exclusao == None).first()
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

#-------------------------------------------------------------- USUÁRIO ------------------------------------------------------                                             
    

# POST - Adicionar um usuário
@app.post("/user/", status_code=status.HTTP_201_CREATED)
async def criar_usuario(usuario: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        novo_usuario = Usuario(**usuario.dict())
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar usuário: {str(e)}")
    
# GET - Buscar um usuário (Opcional ser por ID)    
@app.get("/user/", status_code=status.HTTP_200_OK)
async def buscar_usuario(request: Request, id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    if id is not None:
        Busca_usuario = db.query(Usuario).filter(Usuario.idusuario == id, Usuario.dt_exclusao == None).first()
        if not Busca_usuario:
            return format_response({"mensage": "Esse usuário não pode ser encontrado"}, request, status_code=404)
        user_out = schemas.UserOut.from_orm(Busca_usuario)
        user_dict = jsonable_encoder(user_out)
        
        return format_response(user_dict, request)
    else:
        busca_usuario = db.query(Usuario).all()
        user_out = [jsonable_encoder(schemas.UserOut.from_orm(u)) for u in busca_usuario]
        return format_response(user_out, request)

# DELETE - Apaga o cadastro de um usuário via ID
@app.delete("/user/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_usuario(id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.idusuario == id, Usuario.dt_exclusao == None).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Esse usuário não pode ser deletado")
    
    usuario.dt_exclusao = datetime.utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela usuário
@app.patch("/user/{id}", status_code=status.HTTP_200_OK)
async def atualizar_usuario(id: int, usuario_update: schemas.UserUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    usuario_db = db.query(Usuario).filter(Usuario.idusuario == id, Usuario.dt_exclusao == None).first()
    if not usuario_db:
        return format_response({"mensage": "Usuário não pode ser editado"}, request, status_code=404)
    
    update_user = usuario_update.dict(exclude_unset=True)

    for key, value in update_user.items():
        setattr(usuario_db, key, value)

    db.commit()
    db.refresh(usuario_db)

    user_out = schemas.UserOut.from_orm(usuario_db)
    user_dict = jsonable_encoder(user_out)
    return format_response(user_dict, request)    

#-------------------------------------------------------------- HISTÓRICO ------------------------------------------------------


# POST - Adicionar um histórico
@app.post("/hist/", status_code=status.HTTP_201_CREATED)
async def criar_historico(historico: schemas.HistCreate, db: Session = Depends(get_db)):
    try:
        novo_historico = Historico(**historico.dict())
        db.add(novo_historico)
        db.commit()
        db.refresh(novo_historico)
        return novo_historico
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar histórico: {str(e)}")
    
# GET - Buscar um histórico (Opcional ser por ID)    
@app.get("/hist/", status_code=status.HTTP_200_OK)
async def buscar_historico(request: Request, id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    if id is not None:
        busca_historico = db.query(Historico).filter(Historico.idhistorico == id, Historico.dt_exclusao == None).first()
        if not busca_historico:
            return format_response({"mensage": "Esse histórico não pode ser encontrado"}, request, status_code=404)
        hist_out = schemas.HistOut.from_orm(busca_historico)
        hist_dict = jsonable_encoder(hist_out)
        
        return format_response(hist_dict, request)
    else:
        busca_historico = db.query(Historico).all()
        hist_out = [jsonable_encoder(schemas.HistOut.from_orm(u)) for u in busca_historico]
        return format_response(hist_out, request)

# DELETE - Apaga o cadastro de um histórico via ID
@app.delete("/hist/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_historico(id: int, db: Session = Depends(get_db)):
    historico = db.query(Historico).filter(Historico.idhistorico == id, Historico.dt_exclusao == None).first()
    if not historico:
        raise HTTPException(status_code=404, detail="Esse histórico não pode ser deletado")
    
    historico.dt_exclusao = datetime.utcnow()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela histórico
@app.patch("/hist/{id}", status_code=status.HTTP_200_OK)
async def atualizar_historico(id: int, historico_update: schemas.HistUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    historico_db = db.query(Historico).filter(Historico.idhistorico == id, Historico.dt_exclusao == None).first()
    if not historico_db:
        return format_response({"mensage": "Histórico não pode ser editado"}, request, status_code=404)
    
    update_hist = historico_update.dict(exclude_unset=True)

    for key, value in update_hist.items():
        setattr(historico_db, key, value)

    db.commit()
    db.refresh(historico_db)

    hist_out = schemas.HistOut.from_orm(historico_db)
    hist_dict = jsonable_encoder(hist_out)
    return format_response(hist_dict, request)    