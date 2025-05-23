# 📖 Tutor Virtual para Manual FANUC

Este projeto é um tutor virtual baseado em inteligência artificial que permite consultar o manual da FANUC (fabricante de controladores CNC e robótica industrial) de forma prática e rápida. Utiliza a API da OpenAI para criar um assistente especializado que responde perguntas técnicas baseadas no conteúdo do manual.

---

## Funcionalidades

- Upload e indexação do manual FANUC em formato PDF.
- Assistente virtual que responde perguntas técnicas sobre o manual.
- Integração com Streamlit para interface web simples e interativa.
- Uso do modelo GPT-4 Turbo Preview para respostas rápidas e precisas.
- Capacidade de citar páginas relevantes do manual nas respostas.

---

## Como usar

### Pré-requisitos

- Python 3.7+
- Conta e chave de API da OpenAI com acesso ao GPT-4 Turbo Preview e vector stores.
- Streamlit instalado (`pip install streamlit`).
- Biblioteca OpenAI atualizada para suporte às funcionalidades beta.

### Passos para rodar localmente

1. Clone este repositório:
   ```bash
   git clone https://github.com/seu-usuario/tutor-virtual-fanuc.git
   cd tutor-virtual-fanuc
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure sua chave de API da OpenAI:
   - Crie um arquivo `.streamlit/secrets.toml` com o conteúdo:
     ```
     OPENAI_API_KEY = "sua-chave-aqui"
     ```

4. Coloque o arquivo PDF do manual FANUC na pasta `files/` (ex: `Fanuc S-Errors.pdf`).

5. Execute a aplicação:
   ```bash
   streamlit run app.py
   ```

6. Na interface web, clique em **"Inicializar Sistema"** para carregar o manual e configurar o assistente.

7. Faça perguntas sobre o manual e receba respostas técnicas.

---

## Estrutura do projeto

- `app.py` - Código principal da aplicação Streamlit.
- `files/` - Pasta para armazenar o manual FANUC em PDF.
- `.streamlit/secrets.toml` - Configurações sensíveis (não versionar).
- `requirements.txt` - Dependências Python.

---

## Tecnologias utilizadas

- [Streamlit](https://streamlit.io/) para interface web.
- [OpenAI API](https://platform.openai.com/docs/) para IA e processamento de linguagem natural.
- Python para lógica do backend.

---

## Contribuições

Contribuições são bem-vindas! Por favor, abra issues para reportar bugs ou sugerir melhorias e envie pull requests para colaborar.

---

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

---

Desenvolvido por [
    GUILHERME HENRIQUE ANDRADE
].

