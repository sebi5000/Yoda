# Yoda
![Static Badge](https://img.shields.io/badge/Version-0.3-blue) <br>
AI Chat based on Streamlit &amp; Llama-Index

## How to setup
Make sure python is installed on your computer in Version > 3.0, then clone the repository install the modules with:

``pip install -r requirements.txt``

After installing the packages you need to do the following:
1. Create a Folder named "data" within the main folder (Yoda/data)
2. Place your custom data into that folder e.g. PDF-Files or other File Data (it's mandatory to place at least 1 File)
3. Create a file .env within the main folder and setup following variables:

[mandatory]
OPENAI_API_KEY=[YOUR API KEY]<br>

[optional]
ANTHROPIC_API_KEY=[YOUR API KEY]<br> #if you want to also use Anthropic Models
LLAMA_PARSE_API_KEY=[YOUR_API_KEY] #if you want to parse files with llama-parse, which leads to better undestanding excel or word files. In this case create a subfolder in "data" named "office" and drop office documents there.

## Start the App
Make sure you have some file in your data Folder. Then run command:

``streamlit run main.py``

If everything is setup correctly the browser will open a Chat on localhost. Notice that the initial load will need some time, because the index is created. If you change your data over time, you can simply delete the /storage folder which is created by the app. This will force the app to recreate the index.

## Further Configuration
You will find a config.toml file within the apps main folder. Use this file to configure the app texts and models in more detail:

You can choose between the following modells (starts with low-price/fast):
- gpt-3.5-turbo
- gpt-4
- gpt-4o
- claude-3-haiku-20240307
- claude-3-sonnet-20240229
- claude-3-5-sonnet-20240620
- claude-3-opus-20240229

By default the config is pre-configured for using Anthropic Models.

## Supported File Formats
.docx
.pdf
.xlsx
.csv
.md
.png
.jpg
.jpeg