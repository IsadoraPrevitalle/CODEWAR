# 🚀 API de Gestão de Tarefas

Este projeto faz parte de um **desafio interno entre os membros do time de Apache AirFlow**, cujo objetivo principal é **aprimorar os conhecimentos em Python, criação de APIs RESTful, manipulação de requisições HTTP, integração com banco de dados e boas práticas no desenvolvimento backend**.

---

## 📌 Objetivo da API

A proposta é desenvolver uma **API de gestão de tarefas** que permita controlar e organizar o progresso de atividades de usuários, com base em um sistema de pontuação. A ideia é simular um ambiente real de desenvolvimento, onde cada endpoint tem um propósito específico e se comunica com o banco de dados de maneira estruturada.

---

## 🛠️ Funcionalidades Implementadas na Primeira Etapa

Nesta primeira fase do desafio, foram implementadas as seguintes funcionalidades:

### ✅ Métodos HTTP suportados

* `POST` – Criar novos registros (tarefas, usuários, histórico)
* `GET` – Buscar registros (por ID ou todos)
* `PATCH` – Atualizar parcialmente registros existentes
* `DELETE` – Remover registros

---

### 🔁 Retorno dinâmico em JSON ou XML

A API permite que o cliente defina o tipo de retorno esperado via **header `Accept`**:

### 🧩 Conexão com Banco de Dados

A aplicação utiliza **SQLAlchemy** para fazer a ponte com o banco de dados relacional (SQLite). Foram criadas as seguintes tabelas:

* `Tarefa` – Título, descrição, pontos, datas de inclusão, edição e alteração
* `Usuario` – Nome, idade, sexo, datas de inclusão, edição e alteração
* `Historico` – Nome da tarefa, usuário responsável, finalização, datas
* `Recompensa` – Nome do pokemon, descrição, imagem, pontos

---

### 🎁 Sistema de Recompensas com API Pública (Pokémon)

A API conta com uma funcionalidade exclusiva de recompensa por desempenho, onde seu funcionamento verifica quando um histórico de tarefa é finalizado.
Sempre que o histórico for concluído é realizado uma soma dos pontos de todas as tarefas finalizadas por aquele usuário e realizada uma requisição à PokéAPI (API pública de Pokémon), que retorna um Pokémon como recompensa, cotendo:
* `Nome`
* `Descrição`
* `Imagem`
* `Pontuação acumulada`

---

### 🧱 Schemas com Pydantic

Foram definidos esquemas (`schemas`) com `Pydantic` para validação de entrada e padronização da saída de dados, com suporte ao modelo `from_attributes=True` para integração com ORM.

---

### 🧪 Tratativas e validações

* Utilização de `status code` apropriados (ex: `201 Created`, `204 No Content`, `404 Not Found`, `400 Bad Request`)
* Handler global para erros de validação com `@app.exception_handler(RequestValidationError)`

### 🧾 Registro de Logs
A fim de gravar e validar o comportamento da API, foi implementado um sistema de logs por meio da logging, com os seguintes niveis:

| 🔍 **Nível** | ✨ **Função**                                                                 |
|--------------|-------------------------------------------------------------------------------|
| `DEBUG`      | Informações detalhadas para desenvolvedores                                  |
| `INFO`       | Ações bem-sucedidas                                                          |
| `WARNING`    | Algo inesperado, mas que não quebra a API                                     |
| `ERROR`      | Falhas que impedem alguma operação                                            |
| `CRITICAL`   | Erros graves que comprometem a aplicação como um todo                         |

### 📈 Gráficos e Relatórios

Foi implementado um dashboard interativo utilizando Streamlit que apresenta os principais gráficos de desempenho das tarefas e usuários, incluindo:

* Quantidade total de tarefas por usuário
* Número de tarefas finalizadas por usuário
* Pontuação total de cada usuário
* Quantidade por tipos de recompensas (Pokémons)
* Quantidade e tipos de Logs por data

Além do dashboard, também é possível gerar relatórios em formato PDF contendo os log's detalhados da API com níveis variados (INFO, DEBUG, WARNING, ERROR)
