import os.path
import streamlit as st
from dotenv import load_dotenv
from llama_index.llms.anthropic import Anthropic
from llama_index.core import Settings
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

#Setup API Keys and Config Variables
load_dotenv()

if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
if os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
if os.getenv("ANTHROPIC_MODELL"):
    anthropic_modell = os.getenv("ANTHROPIC_MODELL") #claude-3-haiku-20240307 = fast/cheap, claude-3-sonnet-20240229, claude-3-5-sonnet-20240620, claude-3-opus-20240229 = slow/expensive
else:
    anthropic_modell = "" #will force app to use OpenAI Modell
if os.getenv("COMPANY_NAME"):
    company_name = os.getenv("COMPANY_NAME")
else:
    company_name = "mindsquare AG"

#Setup global Settings for the App
if anthropic_modell:
    Settings.tokenizer = Anthropic().tokenizer
    Settings.llm = Anthropic(model=anthropic_modell)

#Create and persist index based on data folder
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    # load the documents and create the index
    documents = SimpleDirectoryReader("data").load_data()
    index = VectorStoreIndex.from_documents(documents)
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

# Define a simple Streamlit app for Frontend
st.set_page_config(
    page_title="mindsquare Yoda",
    page_icon=""
)

st.logo("assets/logo.png")
st.title('mindsquare Yoda')

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"Frage mich etwas über {company_name}.",
        }
    ]

chat_engine = index.as_chat_engine(chat_mode="condense_question")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=True, streaming=True
    )

if prompt := st.chat_input(
    "Stelle eine Frage"
):  # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:  # Write message history to UI
    with st.chat_message(message["role"]):
        st.write(message["content"])

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        response_stream = st.session_state.chat_engine.stream_chat(prompt)
        st.write_stream(response_stream.response_gen)

        #Add Source Information
        with st.container():
            st.write("Quellen")
            for source in response_stream.source_nodes:
                st.markdown(source.metadata["file_name"] + " S." + source.metadata["page_label"])

        
        #Add message to chat history
        message = {"role": "assistant", "content": response_stream.response}        
        st.session_state.messages.append(message)