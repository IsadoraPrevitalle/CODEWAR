from fastapi import FastAPI, Depends, Request, HTTPException, status, Body, Query
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.status import HTTP_400_BAD_REQUEST
from fastapi.encoders import jsonable_encoder
import schemas
from database import SessionLocal, engine, Base
from config_log import logger
from models import Usuario, Tarefa, Historico, Recompensa
import ETL
from sqlalchemy.orm import Session
from dicttoxml import dicttoxml
from typing import Optional
from datetime import datetime
import requests
from sqlalchemy import func

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        logger.info("A sessão com o banco de dados foi inicializada com suceso")
        yield db
    finally:
        logger.info('A sessão com o banco de dados foi finalizada com sucesso')
        db.close()

@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Erro de validação na requisição {request.url}: {exc.errors}")
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
def root():
    return {'mensagem': 
                'Seja bem vindo a API de gestão de tarefas', 
            'descrição':
                'Essa API tem como objetivo lhe ajudar no gerenciamento de equipes e trabalhos com base em um sistema de pontuação'
                } 

#-------------------------------------------------------------- TAREFA ------------------------------------------------------
# POST - Adicionar uma Tarefa
@app.post("/task/", status_code=status.HTTP_201_CREATED)
def criar_tarefa(tarefa: schemas.TaskCreate, db: Session = Depends(get_db)):
    logger.debug(f"Dados para nova tarefa foram recebidos com sucesso: {tarefa.dict()}")
    try:
        nova_tarefa = Tarefa(**tarefa.dict())
        db.add(nova_tarefa)
        db.commit()
        db.refresh(nova_tarefa)
        logger.info(f"Tarefa {nova_tarefa.idtarefa} foi criada com sucesso")
        return nova_tarefa
    except Exception as e:
        logger.error(f"Erro ao criar tarefa: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao criar tarefa: {str(e)}")
    
# GET - Buscar uma tarefa (Opcional ser por ID)    
from typing import List

@app.get("/task/", status_code=status.HTTP_200_OK)
def buscar_tarefa(request: Request, id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    busca_tarefa = db.query(Tarefa).all()
    if id is not None:
        logger.info(f"Realizando busca da tarefa {id}")
        busca_tarefa = db.query(Tarefa).filter(Tarefa.idtarefa == id, Tarefa.dt_exclusao == None).first()
        if not busca_tarefa:
            logger.warning(f"Tarefa {id} não foi encontrada")
            return format_response({"mensage": "Essa tarefa não pode ser encontrada"}, request, status_code=404)
        logger.info(f"Tarefa {id} encontrada com sucesso")
        task_out = schemas.TaskOut.from_orm(busca_tarefa)
        task_dict = jsonable_encoder(task_out)
        return format_response(task_dict, request)
    else:
        logger.debug("Realizando a busca de todas as tarefas")
        busca_tarefa = db.query(Tarefa).filter(Tarefa.dt_exclusao == None).all()
        tarefas_out = [jsonable_encoder(schemas.TaskOut.from_orm(t)) for t in busca_tarefa]
        logger.info(f"{len(busca_tarefa)} tarefas encontradas com sucesso")
        return format_response(tarefas_out, request)

# DELETE - Apaga uma tarefa via ID
@app.delete("/task/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tarefa(id: int, db: Session = Depends(get_db)):
    logger.debug(f"Deletando tarefa {id}")
    tarefa = db.query(Tarefa).filter(Tarefa.idtarefa == id, Tarefa.dt_exclusao == None).first()
    if not tarefa:
        logger.warning(f"Tarefa {id} não foi encontrada")
        raise HTTPException(status_code=404, detail="Essa tarefa não pode ser deletada")
    tarefa.dt_exclusao = datetime.utcnow()
    db.commit()
    logger.info(f"Tarefa {id} foi marcada como deletada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela tarefa
@app.patch("/task/{id}", status_code=status.HTTP_200_OK)
def atualizar_tarefa(id: int, tarefa_update: schemas.TaskUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    logger.debug(f"Atualizando tarefa {id} com novos dados: {tarefa_update.dict(exclude_unset=True)}")
    tarefa_db = db.query(Tarefa).filter(Tarefa.idtarefa == id, Tarefa.dt_exclusao == None).first()
    if not tarefa_db:
        logger.warning(f"tarefa {id} não foi encontrada")
        return format_response({"mensage": "Tarefa não pode ser editada"}, request, status_code=404)
    
    update_data = tarefa_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(tarefa_db, key, value)

    db.commit()
    db.refresh(tarefa_db)
    task_out = schemas.TaskOut.from_orm(tarefa_db)
    task_dict = jsonable_encoder(task_out)
    logger.info(f"Tarefa {id} atualizada com sucesso")
    return format_response(task_dict, request)

#-------------------------------------------------------------- USUÁRIO ------------------------------------------------------                                             
    

# POST - Adicionar um usuário
@app.post("/user/", status_code=status.HTTP_201_CREATED)
def criar_usuario(usuario: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.debug(f"Dados para novo usário foram recebidos com sucesso: {usuario.dict()}")
    try:
        novo_usuario = Usuario(**usuario.dict())
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        logger.info(f"Usuário {novo_usuario.idusuario} foi criado com sucesso")
        return novo_usuario
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar usuário: {str(e)}")
    
# GET - Buscar um usuário (Opcional ser por ID)    
@app.get("/user/", status_code=status.HTTP_200_OK)
def buscar_usuario(request: Request, id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    if id is not None:
        logger.info(f"Realizando busca do usuário {id}")
        Busca_usuario = db.query(Usuario).filter(Usuario.idusuario == id, Usuario.dt_exclusao == None).first()
        if not Busca_usuario:
            logger.warning(f"Usuário {id} não foi encontrado")
            return format_response({"mensage": "Esse usuário não pode ser encontrado"}, request, status_code=404)
        logger.info(f"Usuário {id} encontrado com sucesso")
        user_out = schemas.UserOut.from_orm(Busca_usuario)
        user_dict = jsonable_encoder(user_out)
        return format_response(user_dict, request)
    else:
        logger.debug("Realizando a busca de todos os usuários")
        busca_usuario = db.query(Usuario).filter(Usuario.dt_exclusao == None).all()
        user_out = [jsonable_encoder(schemas.UserOut.from_orm(u)) for u in busca_usuario]
        logger.info(f"{len(busca_usuario)} usuários encontrados com sucesso")
        return format_response(user_out, request)

# DELETE - Apaga o cadastro de um usuário via ID
@app.delete("/user/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_usuario(id: int, db: Session = Depends(get_db)):
    logger.debug(f"Deletando usuário {id}")
    usuario = db.query(Usuario).filter(Usuario.idusuario == id, Usuario.dt_exclusao == None).first()
    if not usuario:
        logger.warning(f"Usuário {id} não foi encontrado")
        raise HTTPException(status_code=404, detail="Esse usuário não pode ser deletado")
    usuario.dt_exclusao = datetime.utcnow()
    db.commit()
    logger.info(f"usuário {id} foi marcado como deletado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela usuário
@app.patch("/user/{id}", status_code=status.HTTP_200_OK)
def atualizar_usuario(id: int, usuario_update: schemas.UserUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    logger.debug(f"Atualizando usuário {id} com novos dados: {usuario_update.dict(exclude_unset=True)}")
    usuario_db = db.query(Usuario).filter(Usuario.idusuario == id, Usuario.dt_exclusao == None).first()
    if not usuario_db:
        logger.warning(f"usuário {id} não foi encontrado")
        return format_response({"mensage": "Usuário não pode ser editado"}, request, status_code=404)
    
    update_user = usuario_update.dict(exclude_unset=True)

    for key, value in update_user.items():
        setattr(usuario_db, key, value)

    db.commit()
    db.refresh(usuario_db)

    user_out = schemas.UserOut.from_orm(usuario_db)
    user_dict = jsonable_encoder(user_out)
    logger.info(f"Usuário {id} atualizado com sucesso")
    return format_response(user_dict, request)    

#-------------------------------------------------------------- HISTÓRICO ------------------------------------------------------


# POST - Adicionar um histórico
@app.post("/hist/", status_code=status.HTTP_201_CREATED)
def criar_historico(historico: schemas.HistCreate, db: Session = Depends(get_db)):
    logger.debug(f"Dados para novo histórico foram recebidos com sucesso: {historico.dict()}")
    
    usuario = db.query(Usuario).filter(
        Usuario.idusuario == historico.idusuario,
        Usuario.dt_exclusao == None
    ).first()
    if not usuario:
        logger.warning(f"Esse usuário não existe: {historico.idusuario}")
        raise HTTPException(status_code=400, detail="Usuário não encontrado ou excluído")

    tarefa = db.query(Tarefa).filter(
        Tarefa.idtarefa == historico.idtarefa,
        Tarefa.dt_exclusao == None
    ).first()
    if not tarefa:
        logger.warning(f"Essa tarefa não existe: {historico.idtarefa}")
        raise HTTPException(status_code=400, detail="Tarefa não encontrada ou excluída")

    try:
        novo_historico = Historico(**historico.dict())
        db.add(novo_historico)
        db.commit()
        db.refresh(novo_historico)
        logger.info(f"Histórico {novo_historico.idhist} foi criado com sucesso")
    
        if novo_historico.finalizada == 1:
            pontos = (
            db.query(
                func.sum(Tarefa.pontos).label("total_pontos")
            )
                .select_from(Historico)
                .join(Tarefa, Historico.idtarefa == Tarefa.idtarefa) 
                .filter(Historico.finalizada == True, 
                        Historico.dt_exclusao == None, 
                        Tarefa.dt_exclusao == None,
                        Historico.idusuario == novo_historico.idusuario
                        )
                .group_by(Historico.idusuario)
                .scalar()
            )
        
        criar_recom(pontos=pontos, db=db, idhist=novo_historico.idhist)

        return Historico(**historico.dict())
    
    except Exception as e:
        logger.error(f"Erro ao criar histórico: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar histórico: {str(e)}")
    
# GET - Buscar um histórico (Opcional ser por ID)    
@app.get("/hist/", status_code=status.HTTP_200_OK)
def buscar_historico(request: Request, id: Optional[int] = Query(default=None), db: Session = Depends(get_db)):
    if id is not None:
        logger.info(f"Realizando busca do histórico {id}")
        busca_historico = db.query(Historico).filter(Historico.idhist == id, Historico.dt_exclusao == None).first()
        if not busca_historico:
            logger.warning(f"Histórico {id} não foi encontrado")
            return format_response({"mensage": "Esse histórico não pode ser encontrado"}, request, status_code=404)
        logger.info(f"Histórico {id} encontrado com sucesso")
        hist_out = schemas.HistOut.from_orm(busca_historico)
        hist_dict = jsonable_encoder(hist_out)
        return format_response(hist_dict, request)
    else:
        logger.debug("Realizando a busca de todos os históricos")
        busca_historico = db.query(Historico).filter(Historico.dt_exclusao == None).all()
        hist_out = [jsonable_encoder(schemas.HistOut.from_orm(h)) for h in busca_historico]
        logger.info(f"{len(busca_historico)} históricos encontrados com sucesso")
        return format_response(hist_out, request)

# DELETE - Apaga o cadastro de um histórico via ID
@app.delete("/hist/{id}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_historico(id: int, db: Session = Depends(get_db)):
    logger.debug(f"Deletando histórico {id}")
    historico = db.query(Historico).filter(Historico.idhist == id, Historico.dt_exclusao == None).first()
    if not historico:
        logger.warning(f"Histórico {id} não foi encontrado")
        raise HTTPException(status_code=404, detail="Esse histórico não pode ser deletado")
    historico.dt_exclusao = datetime.utcnow()
    db.commit()
    logger.info(f"Histórico {id} foi marcado como deletado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# UPDATE - Altera campos da tabela histórico
@app.patch("/hist/{id}", status_code=status.HTTP_200_OK)
def atualizar_historico(id: int, historico_update: schemas.HistUpdate = Body(...), db: Session = Depends(get_db),request: Request = None):
    logger.debug(f"Atualizando histórico {id} com novos dados: {historico_update.dict(exclude_unset=True)}")
    historico_db = db.query(Historico).filter(Historico.idhist == id, Historico.dt_exclusao == None).first()
    if not historico_db:
        logger.warning(f"Histórico {id} não foi encontrado")
        return format_response({"mensage": "Histórico não pode ser editado"}, request, status_code=404)
    
    finalizada = historico_db.finalizada
    update_hist = historico_update.dict(exclude_unset=True)

    for key, value in update_hist.items():
        setattr(historico_db, key, value)

    db.commit()
    db.refresh(historico_db)

    if not finalizada and historico_db.finalizada:
        pontos = (
        db.query(
            func.sum(Tarefa.pontos).label("total_pontos")
        )
            .join(Tarefa, Historico.idtarefa == Tarefa.idtarefa) 
            .filter(Historico.finalizada == True, 
                    Historico.dt_exclusao == None, 
                    Tarefa.dt_exclusao == None,
                    Historico.idusuario == historico_db.idusuario
                    )
            .group_by(Historico.idusuario)
            .scalar()
        )
        
        criar_recom(pontos=pontos, db=db, idhist=historico_db.idhist)

    hist_out = schemas.HistOut.from_orm(historico_db)
    hist_dict = jsonable_encoder(hist_out)
    logger.info(f"Histórico {id} atualizado com sucesso")
    return format_response(hist_dict, request)    

#-------------------------------------------------------------- API ------------------------------------------------------

# criar uma recompensa 
def criar_recom(pontos, db: Session, idhist: int):
    logger.info(f"Realizando etapa de extração na recompensa de idhist {id}")
    info, especie = ETL.Extract_API(pontos)
    logger.info(f"Realizando etapa de transformação ne recompensa de idhist {id}")
    nome, foto, descricao = ETL.Transform_API(info, especie)
    new_result = Recompensa(
            idhist=idhist,
            nome=nome,
            descricao=descricao,
            imagem_url=foto,
            pontos=pontos
        )
    logger.info(f"Realizando etapa de carregamento na recompensa de idhist {id}")
    ETL.Load_API(new_result, db)

# GET - Buscar recompensa
@app.get("/recom/", status_code=status.HTTP_200_OK)
def buscar_recom(request: Request, id: Optional[int] = None, db: Session = Depends(get_db)):
    if id is not None:
        logger.info(f"Realizando busca na recompensa cujo id de histórico é {id}")
        busca_recom = db.query(Recompensa).filter(Recompensa.idhist == id).first()
        if not busca_recom:
            logger.warning(f"Recompensa de histórico com id: {id} não foi encontrado")
            return format_response({"mensage": "A recompensa desse histórico não pode ser encontrado"}, request, status_code=404)
        logger.info(f"Recompensa do histórico {id} encontrada com sucesso")
        recom_out = schemas.RecomOut.from_orm(busca_recom)
        recom_dict = jsonable_encoder(recom_out)
        return format_response(recom_dict, request)
        
    else:
        logger.debug("Realizando a busca de todas as recompensas")
        busca_recom = db.query(Recompensa).all()
        recom_out = [jsonable_encoder(schemas.RecomOut.from_orm(r)) for r in busca_recom]
        logger.info(f"{len(busca_recom)} recompensas encontradas com sucesso")
        return format_response(recom_out, request)