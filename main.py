import os.path
import streamlit as st
import tiktoken
from dotenv import load_dotenv
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
from tomli import load

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
)

##############################
# Initialize & Check Configuration
##############################

pre_check_message = ""

#LOAD Secrets & API-Keys
load_dotenv()
if os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
if os.getenv("ANTHROPIC_API_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

#LOAD Configuration
with open("config.toml", mode="rb") as handle:
    config = load(handle)

#CHECK Config & Pre-Conditions
if not os.environ["OPENAI_API_KEY"]:
    pre_check_message = "You must have a OPENAI API Key, because OPENAI Ada is used for Embeddings. Add OPENAI_API_KEY=*** to your .env file."
if ( not os.environ["ANTHROPIC_API_KEY"] and 
     config["app"]["default_provider"] == "anthropic" ):
    pre_check_message = "You set ANTHROPIC as default provider in config.toml, but your .env file doesn't contain any ANTHROPIC_API_KEY. Please add ANTHROPIC_API_KEY to your .env file or set default_provider in config.toml to openai."
if ( not config["app"]["default_provider"] or
     not config["app"]["default_model"]):
    pre_check_message = "Your config.toml doesn't contain values for default_provider or default_model. These are both mandatory."

selected_provider = config["app"]["default_provider"]
selected_model = config["app"]["default_model"]

models = { "anthrophic": config["anthropic"]["models"],
           "openai": config["openai"]["models"] }

if not pre_check_message == "":
    st.error(pre_check_message)

##############################
# Initialize llama-index
##############################

#Setup global Settings for the App
if selected_provider == "anthropic":
    Settings.tokenizer = Anthropic().tokenizer
    Settings.llm = Anthropic(model=selected_model)
else:
    Settings.tokenizer = tiktoken.encoding_for_model(selected_model).encode
    Settings.llm = OpenAI(model=selected_model)

#Create and persist index based on data folder
PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):

    # Load DATA Folder
    documents = SimpleDirectoryReader("data").load_data()

    index = VectorStoreIndex.from_documents(documents)
    
    # store it for later
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    # load the existing index
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

##############################
# Initialize Streamlit App
##############################

#Initialize Texts
language = config["app"]["language"]
title = config["app"]["title"]
initial_message = config["texts"][language]["initial_message"]
source = config["texts"][language]["source"]

# Define a simple Streamlit app for Frontend
st.set_page_config(
    page_title=title,
    page_icon=""
)

st.logo("assets/logo.png")
st.title(title)

#Switch Chat-Engine based on choosen Model
def on_model_change():

    selected_model_obj = None
    if selected_provider == "anthropic":
        Settings.tokenizer = Anthropic().tokenizer
        selected_model_obj = Anthropic(model=selected_model)
    else:
        Settings.tokenizer = tiktoken.encoding_for_model(selected_model).encode #set to default GPT
        selected_model_obj = OpenAI(model=selected_model)
    
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=False, streaming=True, llm=selected_model_obj
    )

#Create Model Selection
if config["app"]["show_model_selection"]:
    
    col1, col2 = st.columns(2)
    with col1:        
        selected_provider = st.selectbox(config["texts"][language]["choose_model_provider"], models.keys(), 0)
    with col2:
        selected_model = st.selectbox(config["texts"][language]["choose_model"], models.get(selected_provider), 0, on_change=on_model_change)

##############################
# Initialize Chat Functionality
##############################

if "messages" not in st.session_state.keys():  # Initialize the chat messages history
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": f"{initial_message}",
        }
    ]

chat_engine = index.as_chat_engine(chat_mode="condense_question")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_question", verbose=False, streaming=True
    )

if prompt := st.chat_input():  # Prompt for user input and save to chat history
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
            st.write(source)
            for source in response_stream.source_nodes:
                st.markdown(source.metadata["file_name"] + source.metadata["page_label"])

        #Add message to chat history
        message = {"role": "assistant", "content": response_stream.response}        
        st.session_state.messages.append(message)