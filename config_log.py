import logging

logging.basicConfig(
    filename='Tarefas.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger("Tarefas_logger")