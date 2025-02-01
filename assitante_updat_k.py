import pandas as pd
import streamlit as st
import openai
import time
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

st.set_page_config(layout="wide")
st.header("🤖J.A.R.V.I.S", divider=True)

api_key = st.sidebar.text_input("API Key", type="password")
if st.sidebar.button("Salvar"):
    st.sidebar.success('Chave salva com sucesso')

client = openai.OpenAI(api_key=api_key)


selecao_modelo =st.sidebar.selectbox("Escolha o modelo:", ['gpt-4o', 'gpt-3.5-turbo'])

pergunta = st.text_input("Perguntar ao arquivo:")

upload_file = st.sidebar.file_uploader("Escolha um arquivo CSV", type=["csv"])


df = None
if upload_file is not None:
    try:
        df = pd.read_csv(upload_file, sep=";", decimal=",")
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df = df.sort_values("Date")
        st.write("### Dados do CSV")
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {e}")


def criar_assistant():
    """Cria um assistente no OpenAI."""
    file = client.files.create(
        file=upload_file, purpose="assistants"
    )
    
    assistant = client.beta.assistants.create(
        name="Analista de Dados",
        instructions="Você é um analista de dados. Utilize os dados fornecidos para análise de faturamento de 3 filiais.",
        tools=[{"type": "code_interpreter"}],
        tool_resources={"code_interpreter": {"file_ids": [file.id]}},
        model=selecao_modelo
    )
    return assistant


def criar_thread():
    """Cria uma nova thread no OpenAI."""
    thread = client.beta.threads.create()
    return thread

def enviar_mensagem(thread, pergunta):
    """Envia uma mensagem para a thread solicitando um gráfico caso seja pertinente."""
    mensagem = f"{pergunta} Se necessário, forneça uma visualização em formato de imagem."
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        content=[{"type": "text", "text": mensagem}],
        role='user'
    )
    return message


def rodar_thread_assistant(thread, assistant):
    """Executa a thread com o assistente."""
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        instructions="O nome do usuário é Leandro Souza e ele é um usuário Premium."
    )
    return run


def aguarda_thread_rodar(run):
    """Aguarda a execução da thread."""
    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=run.thread_id,
            run_id=run.id
        )
        # st.write(run.status)
    return run


def verifica_resposta(run, thread):
    """Verifica a resposta do assistente."""
    if run.status == "completed":
        mensagens = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        mensagem = mensagens.data[0].content[0]
        if mensagem.type == 'text':
            st.write(mensagem.text.value)
        elif mensagem.type == 'image_file':
            file_id = mensagem.image_file.file_id
            image_data = client.files.content(file_id)
            with open(f'arquivos/{file_id}.png', 'wb') as f:
                f.write(image_data.read())
                st.write(f'Imagem {file_id} salva')
            img = mpimg.imread(f'arquivos/{file_id}.png')
            fig, ax = plt.subplots()
            ax.set_axis_off()
            ax.imshow(img)
            st.pyplot(fig)
    else:
        st.error(f"Erro: {run.status}")


# Execução principal
if st.button("Executar Análise") and df is not None:
    assistant = criar_assistant()
    thread = criar_thread()
    enviar_mensagem(thread, pergunta)  # ✅ Enviar a pergunta do usuário para a thread
    run = rodar_thread_assistant(thread, assistant)
    run = aguarda_thread_rodar(run)
    verifica_resposta(run, thread)

