import streamlit as st
import openai
import time
import os
# Importa GoogleTranslator apenas uma vez
from deep_translator import GoogleTranslator
# Não precisa importar streamlit e GoogleTranslator novamente

# Carregar variáveis de ambiente do arquivo .env (ainda útil para a API Key)
# Certifique-se de ter python-dotenv instalado (pip install python-dotenv)
from dotenv import load_dotenv
load_dotenv()

# Inicializar cliente OpenAI
# A chave da API será buscada automaticamente da variável de ambiente OPENAI_API_KEY
try:
    client = openai.Client()
except Exception as e:
    st.error(f"Erro ao inicializar cliente OpenAI. Verifique se OPENAI_API_KEY está no seu arquivo .env: {e}")
    st.stop() # Parar a execução se o cliente não puder ser inicializado


# Configuração inicial da interface
st.title("🤖 Tutor Virtual para FANUC")

# Inicialização de estados da sessão
# Mantemos assistant e vector_store na sessão para reutilizar após a configuração inicial
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "assistant" not in st.session_state:
    st.session_state.assistant = None
# Usamos 'configurado' para saber se a configuração inicial pesada já rodou nesta sessão
if "configurado" not in st.session_state:
    st.session_state.configurado = False
# Novo estado para armazenar o ID da thread para manter o histórico da conversa
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None
# Estado para armazenar o histórico de mensagens exibidas
if "messages" not in st.session_state:
    st.session_state.messages = []


# Função para traduzir respostas para português
def traduzir_resposta(resposta):
    """Traduz a resposta para português, com tratamento básico de erros."""
    try:
        if not resposta or len(resposta.strip()) < 5: # Evita traduzir strings vazias ou muito curtas
            return resposta
        return GoogleTranslator(source='auto', target='pt').translate(resposta)
    except Exception as e:
        st.warning(f"Erro na tradução: {e}")
        return resposta # Retorna a resposta original em caso de erro


# Função para obter todos os arquivos PDF da pasta 'files'
def obter_arquivos_da_pasta(pasta="files"):
    """Lista todos os arquivos PDF em uma pasta específica."""
    if not os.path.exists(pasta):
        st.error(f"Pasta '{pasta}' não encontrada.")
        return []
    arquivos_pdf = [os.path.join(pasta, f) for f in os.listdir(pasta) if f.endswith(".pdf")]
    return arquivos_pdf


# Função para configurar o sistema (cria Vector Store e Assistente)
# Esta função ainda é lenta na primeira execução após um restart completo do script.
def configurar_sistema():
    """Configura o Vector Store e o Assistente da OpenAI se ainda não estiverem configurados na sessão."""
    if not st.session_state.configurado:
        with st.spinner("Configurando o tutor virtual (isso pode levar alguns minutos na primeira execução)..."):
            try:
                arquivos_pdf = obter_arquivos_da_pasta()

                if not arquivos_pdf:
                    st.error("Nenhum arquivo PDF encontrado na pasta 'files'.")
                    return

                # --- Criação do Vector Store ---
                # O ideal seria buscar um Vector Store existente pelo nome ou ID
                # Mas seguindo a restrição de não usar IDs externos, criamos um novo.
                # Isso é o principal ponto de lentidão na primeira execução.
                # st.info("Criando Vector Store...") # Removido
                vector_store = client.vector_stores.create(name="Manual_FANUC_AppSession") # Nome para identificar

                # st.info(f"Fazendo upload de {len(arquivos_pdf)} arquivo(s) para o Vector Store...") # Removido
                file_streams = [open(file_path, "rb") for file_path in arquivos_pdf]
                try:
                    file_batch = client.vector_stores.file_batches.upload_and_poll(
                        vector_store_id=vector_store.id,
                        files=file_streams
                    )
                    # st.info(f"Status do upload e processamento: {file_batch.status}") # Removido
                    if file_batch.status != 'completed':
                         st.warning(f"Alguns arquivos podem não ter sido processados corretamente. Status: {file_batch.status}")
                         # Opcional: Adicionar lógica para verificar quais falharam: file_batch.file_counts.failed

                finally:
                    # Fechar os streams de arquivo
                    for fs in file_streams:
                        fs.close()

                # --- Criação do Assistente ---
                # st.info("Criando Assistente...") # Removido
                assistant = client.beta.assistants.create(
                    name="Especialista FANUC AppSession", # Nome para identificar
                    instructions="Você é um especialista técnico em robótica industrial com amplo conhecimento nos manuais FANUC. Responda às perguntas de forma clara e técnica, citando sempre as páginas relevantes do manual e traduzindo qualquer conteúdo necessário para português.",
                    tools=[{"type": "file_search"}],
                    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                    model="gpt-4o-mini"
                )
                st.session_state.vector_store = vector_store
                st.session_state.assistant = assistant
                st.session_state.configurado = True
                st.success("Sistema configurado com sucesso!")

            except Exception as e:
                st.error(f"Erro na configuração: {str(e)}")
                # Em caso de erro na configuração, resetar o estado para tentar novamente?
                # Ou parar? Vamos parar para evitar loop de erro.
                st.stop()


# --- Chamando a configuração automaticamente apenas uma vez por sessão ---
# Esta chamada ainda causará lentidão na primeira execução completa do script.
configurar_sistema()

# Exibir histórico de mensagens (opcional, para dar contexto visual)
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# Interface de perguntas
user_question = st.text_input("📝 Faça sua pergunta sobre os manuais FANUC:")

# Processamento da pergunta
if user_question and st.session_state.assistant: # Verifica se o assistente foi configurado
    # Adicionar pergunta do usuário ao histórico (opcional)
    # st.session_state.messages.append({"role": "user", "content": user_question})
    # with st.chat_message("user"):
    #     st.markdown(user_question)

    with st.spinner("Analisando os manuais e preparando resposta..."):
        try:
            # --- Reutiliza a thread ou cria uma nova se for a primeira pergunta da sessão ---
            if st.session_state.thread_id is None:
                 st.info("Iniciando nova conversa...")
                 thread = client.beta.threads.create()
                 st.session_state.thread_id = thread.id
                 # st.info(f"Nova Thread ID: {st.session_state.thread_id}") # Para debug
            else:
                 # Opcional: Tentar recuperar a thread existente para verificar se ainda é válida
                 try:
                     thread = client.beta.threads.retrieve(st.session_state.thread_id)
                     # st.info(f"Continuando conversa na Thread ID: {st.session_state.thread_id}") # Para debug
                 except Exception:
                      # Se a thread não existir mais (ex: expirou), cria uma nova
                      st.warning("Thread anterior não encontrada ou expirou. Iniciando nova conversa...")
                      thread = client.beta.threads.create()
                      st.session_state.thread_id = thread.id
                      # st.info(f"Nova Thread ID criada: {st.session_state.thread_id}") # Para debug


            # Adiciona a mensagem do usuário à thread (usa o ID da thread armazenado)
            message = client.beta.threads.messages.create(
                thread_id=st.session_state.thread_id,
                role="user",
                content=user_question
            )

            # Executa o assistente na thread (usa o ID do assistente armazenado e o ID da thread)
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=st.session_state.assistant.id,
                # instructions="Opcional: Sobrescrever instruções do assistente para esta run específica"
            )

            # Polling para verificar o status da execução
            # Reduzimos o tempo de sleep para verificar o status mais frequentemente
            while run.status in ["queued", "in_progress", "cancelling"]:
                time.sleep(0.2) # Espera menor (0.2 segundos)
                run = client.beta.threads.runs.retrieve(thread_id=st.session_state.thread_id, run_id=run.id)
                # st.write(f"Status do Run: {run.status}") # Opcional: mostrar status para debug

            if run.status == "completed":
                # Recupera as mensagens após a conclusão
                # Buscamos apenas as mensagens mais recentes, limitando a 1 (a resposta do assistente)
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id,
                    order="desc", # Obter as mensagens mais recentes primeiro
                    limit=1 # Pegar apenas a última mensagem
                )

                # Encontrar a última mensagem do assistente para esta run específica
                # É mais robusto verificar se a mensagem pertence à run atual
                assistant_messages_for_this_run = [
                    msg for msg in messages.data
                    if msg.run_id == run.id and msg.role == "assistant"
                ]

                if assistant_messages_for_this_run:
                    # A resposta está no primeiro item de content, que é um objeto TextContent
                    resposta = assistant_messages_for_this_run[0].content[0].text.value

                    # Traduz a resposta
                    resposta_traduzida = traduzir_resposta(resposta)

                    # Exibe a resposta traduzida
                    st.markdown(f"**Resposta:**\n\n{resposta_traduzida}")

                    # Adicionar resposta do assistente ao histórico (opcional)
                    # st.session_state.messages.append({"role": "assistant", "content": resposta_traduzida})
                    # with st.chat_message("assistant"):
                    #    st.markdown(resposta_traduzida)

                else:
                     st.warning("Assistente não gerou uma resposta para esta solicitação nesta execução.")


            elif run.status == "requires_action":
                 st.warning("A execução requer ação (ex: uso de função externa não implementada).")
                 # Se você tiver tools de "function calling", precisaria implementar a lógica aqui.
                 # Para file_search, geralmente não chega neste status a menos que haja um erro.

            else:
                st.error(f"Erro ao processar a solicitação. Status do Run: {run.status}")
                # Opcional: Recuperar passos do run para mais detalhes do erro
                # run_steps = client.beta.threads.runs.steps.list(thread_id=thread.id, run_id=run.id)
                # st.json(run_steps.data)


        except Exception as e:
            st.error(f"Erro na consulta: {str(e)}")
            # Opcional: Em caso de erro grave na thread, pode ser útil iniciar uma nova na próxima vez
            # st.session_state.thread_id = None

# Nota: A exclusão do Vector Store e do Assistente ao final da sessão não é automática.
# Eles persistirão na sua conta da OpenAI até que você os exclua manualmente via API, CLI ou playground.
# Em um ambiente de produção, você provavelmente gerenciaria o ciclo de vida desses recursos
# de forma mais controlada.
