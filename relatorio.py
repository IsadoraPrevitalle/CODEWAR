import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from models import Usuario, Historico, Tarefa, Recompensa
from sqlalchemy import select, func
from database import get_db
import requests
import re
from collections import defaultdict
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image
import urllib.request
import numpy as np
from fpdf import FPDF

st.set_page_config(page_title="Dash Tarefas", layout="wide")

st.markdown("""
    <style>
        .main {
            background-color: #0e1117;
            color: #F7F5F5;
        }
        header, .css-18e3th9, .css-1d391kg {
            background-color: #0e1117;
        }
    </style>
""", unsafe_allow_html=True)

def read_log(caminho="Tarefas.log"):
    with open(caminho, "r", encoding="latin-1") as f:
        text = f.readlines()
    return text

def pdf_log(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(0, 0, 128)
    pdf.cell(0, 10, "Relatório dos Logs da API", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)

    for t in text:
        pdf.multi_cell(0, 8, t.strip())

    return pdf.output(dest='S').encode('latin1')

def load_log(path="Tarefas.log"):
    pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}):\d{2}:\d{2},\d+\s-\s(\w+)")
    counts = defaultdict(lambda: {"INFO": 0, "DEBUG": 0, "WARNING": 0, "ERROR": 0})

    with open(path, "r", encoding="latin-1") as f:
        for line in f:
            m = pattern.match(line)
            if m:
                hour, level = m.groups()
                if level in counts[hour]:
                    counts[hour][level] += 1

    df = pd.DataFrame.from_dict(counts, orient="index").sort_index()
    df.index.name = "datetime_hour"
    return df

def img_fundo(img_url, cor=(14, 17, 23)):
    with urllib.request.urlopen(img_url) as response:
        img = Image.open(response).convert("RGBA")
        fundo = Image.new("RGBA", img.size, cor + (255,))
        img = Image.alpha_composite(fundo, img)
        return np.array(img.convert("RGB"))
        
def get_recom(session):
    stmt = select(
            func.lower(Recompensa.nome).label("pokemon"),
            Recompensa.imagem_url.label("img"),
            func.count(Recompensa.idrecom).label("qtd")
        ).group_by(func.lower(Recompensa.nome))
    return pd.read_sql(stmt, session.bind)

def get_task(session):
    stmt = select(
        Tarefa.titulo,
        Tarefa.pontos
    ).where(Tarefa.dt_exclusao == None)
    return pd.read_sql(stmt, session.bind)

def get_pts_user(session):
    stmt = (
        select(
            Usuario.nome.label("user"),
            func.sum(Tarefa.pontos).label("pontos")
        )
        .join(Historico, Historico.idusuario == Usuario.idusuario)
        .join(Tarefa, Tarefa.idtarefa == Historico.idtarefa)
        .where(Historico.finalizada == True, Historico.dt_exclusao == None)
        .group_by(Usuario.idusuario)
    )
    return pd.read_sql(stmt, session.bind)

def get_ttl_task_user(session):
    stmt = (
        select(
            Usuario.nome.label("user"),
            func.count(Historico.idhist).label("tarefas")
        )
        .join(Historico, Historico.idusuario == Usuario.idusuario)
        .where(Historico.dt_exclusao == None)
        .group_by(Usuario.idusuario)
    )
    return pd.read_sql(stmt, session.bind)

def get_task_fin_user(session):
    stmt = (
        select(
            Usuario.nome.label("user"),
            func.count(Historico.idhist).label("finalizadas")
        )
        .join(Historico, Historico.idusuario == Usuario.idusuario)
        .where(Historico.dt_exclusao == None, Historico.finalizada == True)
        .group_by(Usuario.idusuario)
    )
    return pd.read_sql(stmt, session.bind)

def carregar_dados(session):
    t_finalizada = get_task_fin_user(session)
    t_total = get_ttl_task_user(session)
    t_pontos = get_pts_user(session)
    tarefa = get_task(session)
    pokemon = get_recom(session)
    return t_finalizada, t_total, t_pontos, tarefa, pokemon

def Dash():

    with next(get_db()) as session:
        hist_final, hist_total, pontos, task, pok = carregar_dados(session)

    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("https://i.gifer.com/bf0.gif", width=100)
    with col2:
        st.markdown(
            """
            <style>
            .title {
                color: White;
                font-size: 35px;
                font-family: 'Times New Roman', serif;
                white-space: nowrap;
                margin-top: 5px
            }
            </style>
            <h1 class="title">Gerenciador de Tarefas</h1>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(hist_total["user"], hist_total["tarefas"], color="#A51CE9")
        ax.set_xlabel("Quantidade de Tarefas")
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.set_title("Tarefas por Usuário", color="#F7F5F5", fontsize=16)
        ax.set_xlabel("tarefas", color="#F7F5F5", fontsize=12)
        ax.set_ylabel("usuários", color="#F7F5F5", fontsize=12)
        ax.tick_params(axis='x', colors='#F7F5F5')
        ax.tick_params(axis='y', colors='#F7F5F5')

        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh(hist_final["user"], hist_final["finalizadas"], color="#2374B3")
        ax.set_xlabel("Quantidade de Tarefas Finalizadas")
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.set_title("Tarefas Finalizadas por Usuário", color="#F8FDFD", fontsize=16)
        ax.set_xlabel("tarefas", color="#F7F5F5", fontsize=12)
        ax.set_ylabel("usuários", color="#F7F5F5", fontsize=12)
        ax.tick_params(axis='x', colors='#F7F5F5')
        ax.tick_params(axis='y', colors='#F7F5F5')

        st.pyplot(fig)

    with col3:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(pontos["user"], pontos["pontos"], color="#E710BC")
        ax.set_xlabel("Pontuação por usuário")
        fig.patch.set_facecolor("#0e1117")
        ax.set_facecolor("#0e1117")

        ax.set_title("Pontuação por Usuário", color="#F7F5F5", fontsize=16)
        ax.set_ylabel("pontos", color="#F7F5F5", fontsize=12)
        ax.set_xlabel("usuários", color="#F7F5F5", fontsize=12)
        ax.tick_params(axis='x', colors='#F7F5F5')
        ax.tick_params(axis='y', colors='#F7F5F5')

        st.pyplot(fig)

    st.markdown("<br><br>", unsafe_allow_html=True)

    fig, ax = plt.subplots(figsize=(20, 5))
    bars = ax.bar(pok['pokemon'], pok['qtd'], color="#3E4DF5")

    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")
    ax.set_title("Quantidade de Pokémons", color="white", fontsize=13)
    ax.set_ylabel("Quantidade", color="white")
    ax.set_xlabel("Pokémon", color="white")
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')

    for bar, img_url in zip(bars, pok['img']):
        altura = bar.get_height()
        x = bar.get_x() + bar.get_width() / 2
        img_np = img_fundo(img_url)
        imagebox = OffsetImage(img_np, zoom=0.6)
        ab = AnnotationBbox(imagebox, (x, altura + 0.5), frameon=False)
        ax.add_artist(ab)

    y_max = max(pok['qtd']) + 1
    ax.set_ylim(0, y_max)
    st.pyplot(fig)

    st.markdown("<br>", unsafe_allow_html=True)
    
    df = load_log("Tarefas.log")
    fig, ax = plt.subplots(figsize=(18, 5))
    colors = {"DEBUG": "#FF00D0", "INFO": "#2374B3", "WARNING": "#00FFB3", "ERROR": "#FF0202"}
    df.plot(kind="line", ax=ax, color=colors)
    fig.patch.set_facecolor("#0e1117")
    ax.set_facecolor("#0e1117")

    ax.set_title("Log's - API tarefas", color="white", fontsize=13)
    ax.set_ylabel("Quantidade", color="white")
    ax.set_xlabel("Data", color="white")
    ax.tick_params(axis="x", rotation=0, colors="white")
    ax.tick_params(axis="y", colors="white")

    ax.legend(
        title_fontsize=10,
        fontsize=10,
        loc='upper right',
        labelcolor="white",
        facecolor="#0e1117",
        edgecolor="#0e1117"
    )

    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("<br><br>", unsafe_allow_html=True)

    cor = ["#F029B8", "#D137D1", "#843DFF", "#056AF7", "#F84681", "#3A0C90", "#ED8AED", "#0A1353"]

    col1_2, col2_2, col3_2 = st.columns([2, 0.3, 1])

    with col1_2:
        fig, ax = plt.subplots(figsize=(2, 2))

        ax.set_title("Pontos por tarefa", color="#F8FDFD", fontsize=4)

        wedges, texts, autotexts = ax.pie(
            task['pontos'],
            autopct='%1.1f%%',
            startangle=140,
            textprops={'color': 'white', 'fontsize': 4},
            colors=cor,
            pctdistance=0.6,
            labels=None
        )

        ax.legend(
            wedges,
            task['titulo'],
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=4,
            frameon=False,
            labelcolor='white'
        )

        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')

        st.pyplot(fig)

    with col2_2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)

    with col3_2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.image("https://i.gifer.com/BRyx.gif", width=250)

def buscar(tabela, tipo, id):
    base_url = "https://codewar-apitask.onrender.com/"
    if id == '':
        new_url = f'{base_url}{tabela}/'
    else:
        new_url = f'{base_url}{tabela}/?id={id}'
    headers = {
        "Accept": f'application/{tipo}'
    }
    response = requests.get(new_url, headers=headers)
    if response.status_code != 200:
        st.error(f"Erro na busca: {response.status_code} - {response.text}")
        return None
    if tipo.lower() == 'json':
        return response.json()
    else:
        return response.text

def criar(tabela, dados):
    base_url = "https://codewar-apitask.onrender.com/"
    new_url = f'{base_url}{tabela}/'
    response = requests.post(new_url, json=dados)
    if response.status_code in (200, 201):
        st.success("Dados enviados com sucesso!")
        return response.json()
    else:
        st.error(f"Erro ao enviar dados: {response.status_code}")
        st.text(response.text)
        return None

def atualizar(tabela, id, dados):
    base_url = "https://codewar-apitask.onrender.com/"
    new_url = f"{base_url}{tabela}/{id}"
    response = requests.patch(new_url, json=dados)
    if response.status_code == 200:
        st.success(f"{tabela} atualizada com sucesso!")
        return response.json()
    else:
        st.error(f"Erro ao atualizar: {response.status_code}")
        st.text(response.text)
        return None

def deletar(tabela, id):
    base_url = "https://codewar-apitask.onrender.com/"
    new_url = f"{base_url}{tabela}/{id}"
    response = requests.delete(new_url)
    if response.status_code == 204:
        st.success(f"{tabela} deletada com sucesso!")
    else:
        st.error(f"Erro ao deletar: {response.status_code}")
        st.text(response.text)

def API():

    col1, col2 = st.columns([1, 10])
    with col1:
        st.image("https://i.gifer.com/bf0.gif", width=100)
    with col2:
        st.markdown(
            """
            <style>
            .title {
                color: White;
                font-size: 35px;
                font-family: 'Times New Roman', serif;
                white-space: nowrap;
                margin-top: 5px
            }
            </style>
            <h1 class="title">Gerenciador de Tarefas</h1>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br><br>", unsafe_allow_html=True)

    tabelas_disponiveis = ["task", "user", "hist"]

    menu = st.selectbox("Menu Principal:", ["Realizar uma busca", "Realizar um novo cadastro", "Realizar uma alteração", "Realizar uma exclusão"])
    tabela = st.selectbox("Selecione a tabela:", tabelas_disponiveis)

    if menu == "Realizar uma busca":
        tipo = st.radio("Escolha o tipo de retorno que desja da API:", ["json", "xml"])
        id = st.text_input("Entre com o ID da tabela caso deseje fazer uma busca especifica:")
        if st.button("Realizar uma busca"):
            resultado = buscar(tabela, tipo, id)
            if resultado:
                if tipo == "json":
                    st.json(resultado)
                else:
                    st.code(resultado)

    elif menu == "Realizar um novo cadastro":
        colunas = {
            "task": ["titulo", "descricao", "pontos"],
            "user": ["nome", "idade", "sexo"],
            "hist": ["nome", "descricao", "idusuario", "idtarefa", "finalizada"]
        }
        st.write(f"Digite os dados para criar um novo cadastro na tabela de {tabela}:")
        dados = {}
        for coluna in colunas[tabela]:
            valor = st.text_input(f"{coluna}")
            if valor:
                if valor.lower() in ['true', 'false']:
                    valor = valor.lower() == 'true'
                else:
                    try:
                        valor = int(valor)
                    except:
                        pass
                dados[coluna] = valor
        if st.button("Realizar um novo cadastro"):
            if dados:
                criar(tabela, dados)
            else:
                st.warning("Preencha pelo menos um campo")

    elif menu == "Realizar uma alteração":
        id = st.text_input("Entre com o ID do registro que deseja alterar:")
        colunas_str = st.text_input("Forneça os nomes das colunas que deseja alterar o valor, separadas por vírgula:")
        if id and colunas_str:
            colunas = [c.strip() for c in colunas_str.split(",")]
            dados = {}
            for coluna in colunas:
                valor = st.text_input(f"Novo valor para {coluna}")
                if valor:
                    if valor.lower() in ['true', 'false']:
                        valor = valor.lower() == 'true'
                    else:
                        try:
                            valor = int(valor)
                        except:
                            pass
                    dados[coluna] = valor
            if st.button("Realizar uma alteração"):
                if dados:
                    atualizar(tabela, id, dados)
                else:
                    st.warning("Informe ao menos um valor para atualizar.")

    elif menu == "Realizar uma exclusão":
        id = st.text_input("Entre com o ID do registro que deseja excluir:")
        if st.button("Realizar uma exclusão"):
            if id:
                deletar(tabela, id)
            else:
                st.warning("Informe um ID para deletar.")

    texto = read_log("Tarefas.log")

    pdf_bytes = pdf_log(texto)

    st.download_button(
        label="Baixar Relatório de Logs",
        data=pdf_bytes,
        file_name="relatorio_logs_api.pdf",
        mime="application/pdf"
    )

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        background-image: url('https://i.pinimg.com/1200x/cd/70/88/cd70884f895b6addd44a56870a4569d4.jpg');
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)
pagina = st.sidebar.selectbox("Menu:", ["Gráficos e relatórios de Tarefas", "API de Tarefas"])

if pagina == "Gráficos e relatórios de Tarefas":
    Dash()
elif pagina == "API de Tarefas":
    API()
