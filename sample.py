import requests
import json

url = "http://localhost:8000/"

def Buscar(tabela, tipo, id):
    if id == '':
        new_url = f'{url}{tabela}/'
    else:
        new_url = f'{url}{tabela}/?id={id}'
    
    headers = {
        "Accept": f'application/{tipo}'
    }

    response = requests.get(new_url, headers=headers)
    if tipo == 'json':
        print(json.dumps(response.json(), indent= 4, ensure_ascii=False))
    else:
        print(response.text) #melhoria - formatar

def Criar(tabela):
    new_url = f'{url}{tabela}/'
    colunas = {
    "task": ["titulo", "descricao", "pontos"],
    "user": ["nome", "idade", "sexo"],
    "hist": ["nome", "descricao", "idusuario", "idtarefa", "finalizada"]
    }
    dados = {}
    for coluna in colunas[tabela]:
        valor = input(f"Entre com o valor para {coluna}: ")
        
        if valor.lower() in ['true', 'false']:
            valor = valor.lower() == 'true'
        else:
            try:
                valor = int(valor)
            except ValueError:
                pass

        dados[coluna] = valor
        
    response = requests.post(new_url, json=dados)

    if response.status_code == 200 or response.status_code == 201:
        print("Dados enviados com sucesso!")
        print("Resposta:", response.json())
    else:
        print(f"Erro ao enviar dados: {response.status_code}")
        print("Detalhes:", response.text)

def Atualizar(tabela, id, colunas):
    new_valor = {}
    new_url = f"{url}/{tabela}/{id}"
    for coluna in colunas:
        valor = input(f'Digite o novo valor para {coluna} ')
        new_valor[coluna] = valor  

    response = requests.patch(new_url, json=new_valor)

    if response.status_code == 200:
        print(f"{tabela} atualizada com sucesso!")
        print("Resposta:", response.json())
    else:
        print(f"Erro ao atualizar: {response.status_code}")
        print("Detalhes:", response.text)

def Deletar(tabela, id):
    new_url = f"{url}/{tabela}/{id}"
    response = requests.delete(new_url)

    if response.status_code == 204:
        print(f"{tabela} deletada com sucesso!")
    else:
        print(f"Erro ao deletar: {response.status_code}")
        print("Detalhes:", response.text)

if __name__ == "__main__":
    response = requests.get(url)
    print(json.dumps(response.json(), indent= 4, ensure_ascii=False))
    menu = ('''\n\n------------------ MENU PRINCIPAL-------------: 
                 \n 🟢 1 - Realizar uma busca 
                 \n 🟢 2 - Realizar um novo cadastro 
                 \n 🟢 3 - Realizar uma alteração
                 \n 🟢 4 - Realizar uma exclusão 
                 \n 🟢 5 - Sair \n''')
    while True:
        print(menu)
        valor = int(input('Para inicializarmos escolha uma das opções do menu: '))
        if valor == 5:
            print('Programa finalizado')
            break
        else:
            tabela = input('Qual o nome da tabela que deseja realizar essa ação? ')
            if valor == 1:
                tipo = input('Entre com o tipo de retorno que deseja da API (XML ou JSON) ')
                id = input('Entre com o ID da tabela caso deseje fazer uma busca especifica ')
                
                Buscar(tabela, tipo, id)

            elif valor == 2:
                Criar(tabela)

            elif valor == 3:
                colunas = input('Forneça os nomes das colunas que deseja alterar o valor, separadas por vírgula: ')
                id = input('Entre com o ID da tabela ')
                colunas = [col.strip() for col in colunas.split(",")]
                
                Atualizar(tabela, id, colunas)

            elif valor == 4:
                id = input('Entre com o ID da tabela ')
                Deletar(tabela, id)
            
            else: 
                print('desculpe, não temos essa opção em nossa menu, tente novamente')