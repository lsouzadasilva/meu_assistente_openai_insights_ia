import pandas as pd
import streamlit as st
import openai
import time
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

st.set_page_config(
    page_title="J.A.R.V.I.S ASSISTANTS",
    page_icon="🤖"
)

st.markdown("<h1 style='text-align: center; color: #4B8BBE;'>Assistente de leitura CSV 🤖</h1>", unsafe_allow_html=True)
st.divider()

# --- Ocultar menus ---
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

st.sidebar.markdown("<h2 style='color: #A67C52;'>J.A.R.V.I.S 🤖</h2>", unsafe_allow_html=True)

home, configuracoes = st.sidebar.tabs(['Home', 'Configurações'])

with configuracoes:
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None

    api_key = st.text_input("API Key", type="password")
    if api_key:
        st.session_state.api_key = api_key
        st.success('Chave salva com sucesso')

    client = None
    if st.session_state.api_key:
        client = openai.OpenAI(api_key=st.session_state.api_key)

    instruction = st.text_input("Instrução:")
    selecao_modelo = st.selectbox("Escolha o modelo:", ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-3.5-turbo-0125'])
    upload_file = st.file_uploader("Escolha um arquivo CSV", type=["csv"])

with home:
    st.markdown(
        """
        ## Bem-vindo ao J.A.R.V.I.S! 🤖
        Esta aplicação permite interações com modelos de IA da OpenAI, proporcionando respostas inteligentes e contextualizadas para suas perguntas.

        🔹 **Como funciona?**
        
        ✅ Insira sua chave da API OpenAI na aba Configurações.  
        ✅ Preencha o campo "Instrução" para direcionar o assistente.  
        ✅ Escolha entre os modelos GPT-3.5-Turbo e GPT-4.  
        ✅ Faça o upload de um arquivo CSV para análise.  
        ✅ Digite sua pergunta no chat e obtenha insights baseados nos dados fornecidos. 
        """
    )

df = None
if upload_file is not None:
    try:
        df = pd.read_csv(upload_file, sep=";", decimal=",")
        df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
        df = df.drop(columns=["Unnamed: 0"], errors='ignore')
        df = df.sort_values("Date")
        st.write("### Dados do CSV")
        st.dataframe(df, use_container_width=True, hide_index=True)
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
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=st.session_state.assistant_id,
        instructions="O nome do usuário é Leandro Souza e ele é um usuário Premium."
    )
    return aguarda_thread_rodar(run)

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
        for mensagem in mensagens.data:
            for conteudo in mensagem.content:
                if conteudo.type == 'text':
                    st.write(conteudo.text.value)
                elif conteudo.type == 'image_file':
                    file_id = conteudo.image_file.file_id
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


with configuracoes:
    if st.button("Iniciar Assistente") and upload_file is not None:
        criar_assistant()
        criar_thread()
        st.success("Assistente e Thread criados! Agora você pode fazer perguntas.")


pergunta = st.text_input("Perguntar ao arquivo:")
if st.button("Enviar Pergunta") and pergunta and st.session_state.assistant_id and st.session_state.thread_id:
    enviar_mensagem(pergunta)
    run = rodar_thread_assistant()
    verifica_resposta(run)

st.sidebar.divider()
st.sidebar.markdown("""
    **Desenvolvido por Leandro Souza**  
    [![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in//leandro-souza-dados/)
    [![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/lsouzadasilva/meu_assistente_openai_insights)
""")
