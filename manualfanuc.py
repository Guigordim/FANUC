import streamlit as st
import openai
import time
import os
from deep_translator import GoogleTranslator

# Configuração inicial
st.title("📖 Tutor Virtual para FANUC")
client = openai.Client()

# Inicialização de estados da sessão
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "configurado" not in st.session_state:  # Novo estado para garantir que só configure uma vez
    st.session_state.configurado = False

# Função para traduzir respostas para português
def traduzir_resposta(resposta):
    return GoogleTranslator(source='auto', target='pt').translate(resposta)

# Função para obter todos os arquivos PDF da pasta 'files'
def obter_arquivos_da_pasta(pasta="files"):
    arquivos_pdf = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith(".pdf")]
    return arquivos_pdf

# Função para configurar o sistema apenas uma vez
def configurar_sistema():
    if not st.session_state.configurado:  # Evita reconfiguração a cada execução
        with st.spinner("Configurando o tutor virtual..."):
            try:
                # Obtém todos os arquivos PDF da pasta
                arquivos_pdf = obter_arquivos_da_pasta()

                if not arquivos_pdf:
                    st.error("Nenhum arquivo PDF encontrado na pasta 'files'.")
                    return

                # Cria o Vector Store
                vector_store = openai.vector_stores.create(name="Manual_FANUC")

                # Faz upload dos arquivos para o Vector Store
                file_batch = openai.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id,
                    files=[open(file_path, "rb") for file_path in arquivos_pdf]
                )

                # Cria o assistente especializado
                assistant = openai.beta.assistants.create(
                    name="Especialista FANUC",
                    instructions="Você é um especialista técnico em robótica industrial com amplo conhecimento nos manuais FANUC. Responda às perguntas de forma clara e técnica, citando sempre as páginas relevantes do manual e traduzindo qualquer conteúdo necessário para português.",
                    tools=[{"type": "file_search"}],
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                    model="gpt-4-turbo-preview"
                )

                st.session_state.vector_store = vector_store
                st.session_state.assistant = assistant
                st.session_state.configurado = True  # Marca como configurado
                st.success(f"{len(arquivos_pdf)} arquivo(s) carregado(s) e sistema configurado com sucesso!")

            except Exception as e:
                st.error(f"Erro na configuração: {str(e)}")

# Chamando a configuração automaticamente apenas uma vez
configurar_sistema()

# Interface de perguntas
user_question = st.text_input("📝 Faça sua pergunta sobre os manuais FANUC:")

if user_question and st.session_state.assistant:
    with st.spinner("Analisando os manuais e preparando resposta..."):
        try:
            thread = openai.beta.threads.create()
            message = openai.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_question
            )

            run = openai.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=st.session_state.assistant.id,
            )

            while run.status not in ["completed", "failed"]:
                time.sleep(1)
                run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            if run.status == "completed":
                messages = openai.beta.threads.messages.list(thread_id=thread.id)
                resposta = messages.data[0].content[0].text.value

                resposta_traduzida = traduzir_resposta(resposta)
                st.markdown(f"**Resposta:**\n\n{resposta_traduzida}")
            else:
                st.error("Erro ao processar a solicitação")

        except Exception as e:
            st.error(f"Erro na consulta: {str(e)}")