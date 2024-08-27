# Yoda
AI Chat based on Streamlit &amp; Llama-Index

## How to setup
Make sure python is installed on your computer in Version > 3.0, then clone the repository install the modules with:

``pip install -r requirements.txt``

After installing the packages you need to do the following:
1. Create a Folder named "data" within the main folder (Yoda/data)
2. Place your custom data into that folder e.g. PDF-Files or other File Data
3. Create a file .env within the main folder and setup following variables:

OPENAI_API_KEY=[YOUR API KEY]<br>
ANTHROPIC_API_KEY=[YOUR API KEY]<br>
ANTHROPIC_MODELL=[YOUR MODELL]<br>
COMPANY_NAME=[The Company Name is used to become a greet in the initial message]<br>

>Notice: You can choose one of the listed Anthropic Modells. If you don't have or want a Anthropic API-Key you can remove the Anthropic Variables from .env file. In that case GPT 3.5 is used as default.

You can choose between the following modells (starts with low-price/fast):
- gpt-3.5-turbo (used if your .env file doesn't contain Anthropic Values)
- claude-3-haiku-20240307
- claude-3-sonnet-20240229
- claude-3-5-sonnet-20240620
- claude-3-opus-20240229

## Start the App
Make sure you have some file in your data Folder. Then run command:

``streamlit run main.py``

If everything is setup correctly the browser will open a Chat on localhost. Notice that the initial load will need some time, because the index is created. If you change your data over time, you can simply delete the /storage folder which is created by the app. This will force the app to recreate the index.