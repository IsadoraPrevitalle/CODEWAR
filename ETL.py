import re
from config_log import logger
from sqlalchemy.orm import Session
from models import Recompensa
import requests

def Extract_API(pontuacao: int):
    logger.info(f"Iniciando extração da API - pontuação: {pontuacao}")
    url = f"https://pokeapi.co/api/v2/pokemon/{pontuacao}"

    info = requests.get(url, timeout = 10)
    if info.status_code != 200:
        logger.error(f"Erro ao acessar URL: {info.status_code}")
        return None, None
    informacao = info.json()
    
    species_url = informacao['species']['url']
    logger.info(f"Buscando dados de espécie: {species_url}")
    
    species = requests.get(species_url, timeout = 10)
    if species.status_code != 200:
        logger.error(f"Erro ao buscar espécie: {species.status_code}")
        return informacao, None

    return informacao, species.json()


def Transform_API(info, esp):
    if not info or not esp:
        logger.warning("info ou esp estão nulos.")
        return None, None, None

    nome = str(info['name']).title() if info['name'] is not None else None
    foto = str(info['sprites']['front_default']) if str(info['sprites']['front_default']).startswith("https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/") else None

    for entry in esp['flavor_text_entries']:
        descricao = str(entry['flavor_text'].replace('\n', ' ').replace('\f', ' ')).capitalize()

    logger.info(f"Transform_API concluída para: {nome}")
    return nome, foto, descricao

def Load_API(result, db: Session):
    logger.debug(f"Criando recompensa para hist: {result.idhist}")

    total_pontos = result.pontos or 0
    if total_pontos == 0 or result.idhist is None:
        logger.warning(f"Usuário não pode ser cadastrado com falta de informações.")
        return None

    exst = db.query(Recompensa).filter(Recompensa.idhist == result.idhist).first()

    if exst:
        logger.info(f"Recompensa já existe para id {result.idhist}")
        return exst
    
    db.add(result)
    db.commit()
    db.refresh(result)
    logger.info(f"Recompensa criada para histórico {result.idhist}")
    return result