import streamlit as st
import openai
import time

# Configuração inicial
st.title("📖 Tutor Virtual para Manual FANUC")
#openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai.Client ()
# Inicialização de estados da sessão
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "assistant" not in st.session_state:
    st.session_state.assistant = None

# Função principal
def main():
    # Upload do PDF
    with st.expander("🔧 Configuração do Sistema"):
        if st.button("🔄 Inicializar Sistema"):
            with st.spinner("Configurando o tutor virtual..."):
                try:
                    # Cria o Vector Store com o manual FANUC
                    vector_store = openai.vector_stores.create(
                        name="Manual_FANUC"
                    )
                    
                    # Faz upload do PDF para o Vector Store
                    file_path = "files/Fanuc S-Errors.pdf"  # Garanta que o PDF está neste caminho
                    with open(file_path, "rb") as f:
                        file_batch = openai.vector_stores.file_batches.upload_and_poll(
                            vector_store_id=vector_store.id,
                            files=[f]
                        )
                    
                    # Cria o assistente especializado
                    assistant = openai.beta.assistants.create(
                        name="Especialista FANUC",
                        instructions="Você é um especialista técnico em robótica industrial com amplo conhecimento nos manuais FANUC. Responda às perguntas de forma clara e técnica, citando sempre as páginas relevantes do manual.",
                        tools=[{"type": "file_search"}],
                        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
                        model="gpt-4-turbo-preview"
                    )
                    
                    st.session_state.vector_store = vector_store
                    st.session_state.assistant = assistant
                    st.success("Sistema configurado com sucesso!")
                    
                except Exception as e:
                    st.error(f"Erro na configuração: {str(e)}")

    # Interface de perguntas
    user_question = st.text_input("📝 Faça sua pergunta sobre o manual FANUC:")
    
    if user_question and st.session_state.assistant:
        with st.spinner("Analisando o manual e preparando resposta..."):
            try:
                # Cria a thread de conversação
                thread = openai.beta.threads.create()
                message = openai.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=user_question
                )
                
                # Executa a assistente
                run = openai.beta.threads.runs.create(
                    thread_id=thread.id,
                    assistant_id=st.session_state.assistant.id,
                )
                
                # Aguarda conclusão
                while run.status not in ["completed", "failed"]:
                    time.sleep(1)
                    run = openai.beta.threads.runs.retrieve(
                        thread_id=thread.id,
                        run_id=run.id
                    )
                
                # Obtém e exibe a resposta
                if run.status == "completed":
                    messages = openai.beta.threads.messages.list(thread_id=thread.id)
                    resposta = messages.data[0].content[0].text.value
                    st.markdown(f"**Resposta:**\n\n{resposta}")
                else:
                    st.error("Erro ao processar a solicitação")
                    
            except Exception as e:
                st.error(f"Erro na consulta: {str(e)}")

if __name__ == "__main__":
    main()
