import streamlit as st
import boto3
import json
import logging
import time

from openai import OpenAI
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.colored_header import colored_header
from streamlit_float import *

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Fastweb_logo.svg/2560px-Fastweb_logo.svg.png"
BOT_LOGO_URL = "https://www.fastweb.it/myfastweb/gfx/common/app-icon-2023@2x.png"

MODEL_URL = "https://eadaee78c5feaaae48433fcde17458cb.serveo.net"
OPENAI_API_KEY = "EMPTY"
OPENAI_API_BASE = f"{MODEL_URL}/v1"
ARGS = {
    "temperature":0,
    "max_tokens": 2048,
    "top_p": 0.8
}

class History:
    def __init__(self):
        self.history = []
    
    def add(self, subject, message):
        if len(self.history) == 0:
            self.history.append(
                {"role":"system", 
                 "content": "Sei un assistente virtuale di poche parole che parla solo italiano. Rispondi alla seguente domanda o affermazione."}
            )
            logging.info('History updated with -> System')
        self.history.append({"role":subject, "content": message})
        logging.info(f'History updated with -> {subject}')
    
    def format(self):
        return "\n ".join([x["role"] + " - " + x["content"] for x in self.history])

def response_generator(response):
    for chunk in response:
        content = chunk.choices[0].delta.to_dict().get("content", "")
        yield content

def disable_input():
    st.session_state["input_disabled"] = True
    logging.info('Input KO, per disable_input()')


client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_BASE,
)

with st.sidebar:
    st.image(LOGO_URL)
    st.markdown("<h1 style='text-align: right; color: #fdc500;'>Enea v0.4</h1>", unsafe_allow_html=True)

    add_vertical_space(35)
    
    if st.button("Nuova conversazione", use_container_width =True):
        for key in st.session_state.keys():
            del st.session_state[key]
        logging.info("Reset storico conversazione per nuova conversazione")

if "history" not in st.session_state:
    st.session_state["history"] = History()
    logging.info('Inizializzazione storico conversazione')

if "input_disabled" not in st.session_state:
    st.session_state["input_disabled"] = False
    logging.info('Input OK')

if "messages" not in st.session_state:
    st.session_state.messages = []

response_container = st.container()
response_container.float()
input_container = st.container()
input_container.float()

with response_container:
    pass
                
with input_container:
    input_placeholder = st.empty()
    input_placeholder.chat_input(
        "Scrivi..",
        max_chars=100,
        disabled=st.session_state["input_disabled"],
        on_submit=disable_input,
        key = "fake")


with response_container:
    
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message(message["role"]):
                st.write(message["content"])
        else:
            with st.chat_message(message["role"], avatar=BOT_LOGO_URL):
                st.write(message["content"])
    
    if st.session_state.get("real"):
        st.session_state["input_disabled"] = True
        logging.info('Input KO')

        with st.chat_message("user"):
            st.write(st.session_state.get("real"))
            st.session_state.messages.append({"role": "user", "content": st.session_state.get("real")})
            st.session_state["history"].add(subject="user", message=st.session_state.get("real"))

        with st.chat_message("assistant", avatar=BOT_LOGO_URL):
            stream = client.chat.completions.create(
                model="Fastweb/Enea-v0.4-llama3-8b",
                messages=st.session_state["history"].history,
                stream=True,
                **ARGS)     
            response = st.write_stream(response_generator(stream))
            st.session_state["input_disabled"] = False
            logging.info('Input OK')

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state["history"].add(subject="assistant", message=response)

    else:
        with st.chat_message("assistant", avatar=BOT_LOGO_URL):
            welcome_text = "Ciao sono il nuovo assistente generativo di Fastweb, cosa posso fare per te?"
            response = st.write(welcome_text) 
            st.session_state.messages.append({"role": "assistant", "content": welcome_text})

    logging.info(f'{st.session_state["history"].history}')

    

with input_container:
    input_placeholder.chat_input(
        "Scrivi..",
        max_chars=100,
        disabled=st.session_state["input_disabled"],
        on_submit=disable_input,
        key = "real")

