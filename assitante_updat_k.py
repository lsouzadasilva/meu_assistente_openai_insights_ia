import pandas as pd
import streamlit as st
import openai
import time
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

st.set_page_config(layout="wide")
st.header("🤖J.A.R.V.I.S", divider=True)

if 'api_key' not in st.session_state:
    st.session_state.api_key = None

api_key = st.sidebar.text_input("API Key", type="password")
if api_key:
    st.session_state.api_key = api_key
    st.sidebar.success('Chave salva com sucesso')

if st.session_state.api_key:
    client = openai.OpenAI(api_key=st.session_state.api_key)

instruction = st.sidebar.text_input("Instrução:")
selecao_modelo = st.sidebar.selectbox("Escolha o modelo:", ['gpt-4o', 'gpt-3.5-turbo','gpt-3.5-turbo-0125'])

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

# Estado para armazenar assistente e thread
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

def criar_assistant():
    if st.session_state.assistant_id is None:
        file = client.files.create(file=upload_file, purpose="assistants")
        assistant = client.beta.assistants.create(
            name="Analista de Dados",
            instructions=instruction,
            tools=[{"type": "code_interpreter"}],
            tool_resources={"code_interpreter": {"file_ids": [file.id]}},
            model=selecao_modelo
        )
        st.session_state.assistant_id = assistant.id
    return st.session_state.assistant_id

def criar_thread():
    if st.session_state.thread_id is None:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    return st.session_state.thread_id

def enviar_mensagem(pergunta):
    mensagem = f"{pergunta} Se necessário, forneça uma visualização em formato de imagem."
    return client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        content=[{"type": "text", "text": mensagem}],
        role='user'
    )

def rodar_thread_assistant():
    return client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.assistant_id,
        instructions="O nome do usuário é Leandro Souza e ele é um usuário Premium."
    )

def aguarda_thread_rodar(run):
    while run.status in ["queued", "in_progress", "cancelling"]:
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=run.thread_id, run_id=run.id
        )
    return run

def verifica_resposta(run):
    if run.status == "completed":
        mensagens = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
        mensagem = mensagens.data[0].content[0]
        if mensagem.type == 'text':
            st.write(mensagem.text.value)
        elif mensagem.type == 'image_file':
            file_id = mensagem.image_file.file_id
            image_data = client.files.content(file_id)
            with open(f'arquivos/{file_id}.png', 'wb') as f:
                f.write(image_data.read())
            img = mpimg.imread(f'arquivos/{file_id}.png')
            fig, ax = plt.subplots()
            ax.set_axis_off()
            ax.imshow(img)
            st.pyplot(fig)
    else:
        st.error(f"Erro: {run.status}")

if st.button("Iniciar Assistente") and upload_file is not None:
    criar_assistant()
    criar_thread()
    st.success("Assistente e Thread criados! Agora você pode fazer perguntas.")

pergunta = st.text_input("Perguntar ao arquivo:")
if st.button("Enviar Pergunta") and pergunta and st.session_state.assistant_id and st.session_state.thread_id:
    enviar_mensagem(pergunta)
    run = rodar_thread_assistant()
    run = aguarda_thread_rodar(run)
    verifica_resposta(run)