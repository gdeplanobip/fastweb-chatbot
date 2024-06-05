import streamlit as st
import boto3
import json
import logging
import time

from openai import OpenAI
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.colored_header import colored_header

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Fastweb_logo.svg/2560px-Fastweb_logo.svg.png"
BOT_LOGO_URL = "https://www.fastweb.it/myfastweb/gfx/common/app-icon-2023@2x.png"

class History:
    def __init__(self):
        self.history = []
    
    def add(self, subject, message):
        if len(self.history) == 0:
            self.history.append(
                {"role":"system", 
                 "content": "Sei un assistente virtuale di poche parole che parla solo italiano. Rispondi alla seguente domanda o affermazione."}
            )
        else:
            self.history.append({"role":subject, "content": message})
        logging.info(f'STORICO AGGIORNATO CON -> {subject}')
            
    
    def format(self):
        return "\n ".join([x["role"] + " - " + x["content"] for x in self.history])

def response_generator(response):
    for chunk in response:
        content = chunk.choices[0].delta.to_dict().get("content", "")
        yield content

def disable_input():
    st.session_state["input_disabled"] = True
    logging.info('Input KO, per disable_input()')

url = "https://eadaee78c5feaaae48433fcde17458cb.serveo.net"
 
# Modify OpenAI's API key and API base to use vLLM's API server.
openai_api_key = "EMPTY"
openai_api_base = f"{url}/v1"
 
client = OpenAI(
    api_key=openai_api_key,
    base_url=openai_api_base,
)

args = {
    "temperature":0,
    "max_tokens": 2048,
    "top_p": 0.8
}

with st.sidebar:
    st.image(LOGO_URL)
    st.markdown("<h1 style='text-align: right; color: #fdc500;'>Enea v0.4</h1>", unsafe_allow_html=True)

    add_vertical_space(35)
    
    if st.button("Nuova conversazione", use_container_width =True):
        for key in st.session_state.keys():
            del st.session_state[key]
        logging.info("Reset storico conversazione per scelta dell'utente")

if "history" not in st.session_state:
    st.session_state["history"] = History()
    logging.info('Inizializzazione storico conversazione')

if "input_disabled" not in st.session_state:
    st.session_state["input_disabled"] = False
    logging.info('Input OK')

if "messages" not in st.session_state:
    st.session_state.messages = []


# LAYOUT 

response_container = st.container()
colored_header(label="", description="", color_name="blue-70")
input_container = st.container()
logging.info('step 1')


with input_container:
    input_placeholder = st.empty()
    input_placeholder.chat_input(
        "Scrivi..",
        max_chars=100,
        disabled=st.session_state["input_disabled"],
        on_submit=disable_input,
        key = "fake")
# logging.info(f'prompt: {prompt}')
# st.session_state.messages.append({"role": "user", "content": "test"})

# logging.info('step 2')

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
        logging.info('Input KO, per if prompt')
        logging.info('step 3')
        with st.chat_message("user"):
            st.write(st.session_state.get("real"))
            st.session_state.messages.append({"role": "user", "content": st.session_state.get("real")})
            st.session_state["history"].add(subject="Umano", message=st.session_state.get("real"))
            # message = st.session_state["history"].format()
        logging.info('step 4')
        logging.info(st.session_state["history"].history)
        logging.info('step 5')

        with st.chat_message("assistant", avatar=BOT_LOGO_URL):
            stream = client.chat.completions.create(
                model="Fastweb/Enea-v0.4-llama3-8b",
                messages=st.session_state["history"].history,
            #     messages = [
            # {"role":"system", "content": "Sei un assistente che risponde in maniera coerente in lingua italiana"},
            # {"role": "user", "content": "Presentami la figura di napoleone in due righe"}
            # ],
                stream=True,
                **args)     
            for chunk in stream:
                content = chunk.choices[0].delta.to_dict().get("content", "")
                #full_string+=content
                print(content, end="", flush=True)
            response = st.write_stream(response_generator(stream))
            st.session_state["input_disabled"] = False
            logging.info('Input OK')
    
        logging.info('step 6')
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state["history"].add(subject="AI", message=response)
        # st.session_state["input_disabled"] = False
        # logging.info('Input OK')
        logging.info('step 7')
# prompt = None
logging.info('step 8')

with input_container:
    input_placeholder.chat_input(
        "Scrivi..",
        max_chars=100,
        disabled=st.session_state["input_disabled"],
        on_submit=disable_input,
        key = "real")
    logging.info('step 9')
    if st.session_state.get("real"):
        logging.info(f'prompt: {st.session_state.get("real")}')
        logging.info('pre add user mess')
        # st.session_state.messages.append({"role": "user", "content": st.session_state.get("real")})
        logging.info('post add user mess')
        logging.info(f'message: {st.session_state.messages}')
        logging.info('step 9.5')

# st.chat_input("ciao")
logging.info('step 10')
logging.info(st.session_state['history'].history)
