import os.path
import streamlit as st
import tiktoken
from dotenv import load_dotenv
from tomli import load
from llama_index.core import Settings
from llama_index.llms.anthropic import Anthropic
from llama_index.llms.openai import OpenAI
from llama_index.readers.file import DocxReader, PDFReader, PandasExcelReader, MarkdownReader, ImageReader, PandasCSVReader

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

models = { "anthropic": config["anthropic"]["models"],
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
    pdf_reader = PDFReader()
    docx_reader = DocxReader()
    csv_reader = PandasCSVReader()
    xlsx_reader = PandasExcelReader()
    markdown_reader = MarkdownReader()
    image_reader = ImageReader()

    file_extractor = { ".docx": docx_reader,
                       ".pdf": pdf_reader,
                       ".xlsx": xlsx_reader,
                       ".csv": csv_reader,
                       ".md": markdown_reader,
                       ".png": image_reader,
                       ".jpg": image_reader,
                       ".jpeg": image_reader }

    # 1. Load all files in data
    documents = SimpleDirectoryReader("./data", file_extractor=file_extractor).load_data()
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
def switch_modell(selected_provider: str, selected_model: str):
    selected_model_obj = None
    
    try:
        if selected_provider == "anthropic":
            Settings.tokenizer = Anthropic().tokenizer
            selected_model_obj = Anthropic(model=selected_model)
        else:
            Settings.tokenizer = tiktoken.encoding_for_model(selected_model).encode #set to default GPT
            selected_model_obj = OpenAI(model=selected_model)        
    except KeyError:
        Settings.tokenizer = tiktoken.get_encoding("cl100k_base") #Fallback to default tokenizer from gpt models

    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context", verbose=False, streaming=True, llm=selected_model_obj, system_prompt=config["app"]["system_prompt"]
    )

def on_provider_change():
    selected_provider = st.session_state.sel_provider
    selected_model = models.get(selected_provider)[0] #get default model for that provider
    switch_modell(selected_provider, selected_model)

def on_model_change():
    selected_provider = st.session_state.sel_provider
    selected_model = st.session_state.sel_model
    switch_modell(selected_provider, selected_model)

#Create Model Selection
if config["app"]["show_model_selection"]:
    
    col1, col2 = st.columns(2)
    with col1:        
        selected_provider = st.selectbox(config["texts"][language]["choose_model_provider"], models.keys(), 0, on_change=on_provider_change, key="sel_provider")
    with col2:
        selected_model = st.selectbox(config["texts"][language]["choose_model"], models.get(selected_provider), 0, on_change=on_model_change, key="sel_model")

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

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_engine" not in st.session_state.keys():  # Initialize the chat engine
    st.session_state.chat_engine = index.as_chat_engine(
        chat_mode="condense_plus_context", verbose=False, streaming=True, system_prompt=config["app"]["system_prompt"]
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
            st.markdown("*" + source + "*")
            for source in response_stream.source_nodes:
                if source.metadata.get("file_name"):
                    if source.metadata.get("page_label"):                        
                        st.markdown(source.metadata["file_name"] + " " + source.metadata["page_label"])
                    else:
                        st.markdown(source.metadata["file_name"])
                        
        #Add message to chat history
        message = {"role": "assistant", "content": response_stream.response}        
        st.session_state.messages.append(message)