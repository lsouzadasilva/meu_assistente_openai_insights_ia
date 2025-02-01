import openai

# Substitua pela sua chave de API
client = openai.OpenAI(api_key="SUA CHAVE")

# Listar todos os arquivos
files = client.files.list()

# Exibir os arquivos carregados
for file in files.data:
    print(f"ID: {file.id} - Nome: {file.filename}")

# Excluir todos os arquivos
for file in files.data:
    client.files.delete(file.id)
    print(f"Arquivo {file.id} deletado.")
