""" 
TO RUN YOUR APP USE THIS COMMAND ON TERMINAL
-> streamlit run chatbot_duble.py
"""

import streamlit as st
import boto3
import json
import json
import logging
import time

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

TOKEN_BLACKLIST = { # id: text
    13: '\n',
    733: ' [', 
    28766: '|',
    11741: 'AI',
    28766: '|',
    28793: ']',
    28792: '[',
    28779: 'U',
    1294: 'man',
    28709: 'o'
}

STOPWORD_SEQ_1 = ['\n', '[', '|', 'U', 'man','o']
STOPWORD_SEQ_2 = ['\n', ' [', '|', 'U', 'man', 'o']

SKIPWORD_SEQ_1 = ['\n', '[', '|', 'AI', '|', ']']
SKIPWORD_SEQ_2 = ['\n', ' [', '|', 'AI', '|', ']']

LOGO_URL = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a0/Fastweb_logo.svg/2560px-Fastweb_logo.svg.png"
BOT_LOGO_URL = ("https://play-lh.googleusercontent.com/1SYd62lmDg6gita4ZZe8mVfVbGGKNHwEtKCVNHQv9LgQ_311tPv9dpmmWS8ZM3uxlrPY")


class History:
    def __init__(self):
        self.history = []
    
    def add(self, subject, message):
        if len(self.history) == 0:
            self.history.append(f"Conversazione tra umano ed AI, [|{subject}|] {message}")
        else:
            self.history.append(f"[|{subject}|] {message}")
    
    def format(self):
        return "\n ".join(self.history)


def response_generator(a):
    stop_sequence = []
    tokens = []
    for p in a["Body"]:
        try:
            token = json.loads(p["PayloadPart"]['Bytes'].decode('utf-8').split('data:')[1])['token']
            tokens.append(token['text'])
            if any([token['id'] == x for x in TOKEN_BLACKLIST.keys()]):
                stop_sequence.append(token['text'])
                if len(stop_sequence) >= 6 and (stop_sequence[-6:] == STOPWORD_SEQ_1 or stop_sequence[-6:] == STOPWORD_SEQ_2):
                    logging.info('Risposta bloccata per rilevazione stopword')
                    return()
                if len(stop_sequence) >= 6 and (stop_sequence[-6:] == SKIPWORD_SEQ_1 or stop_sequence[-6:] == SKIPWORD_SEQ_2):
                    logging.info('Risposta accorciata per rilevazione skipword')
                    tokens = []
            if len(tokens) == 6:
                token_return = tokens[0]
                tokens = tokens[1:]
                yield token_return
        except:
            pass

def dumb_response_generator(sentence):
    for word in sentence.split():
        yield word + " "
        time.sleep(0.05)


client = boto3.client("runtime.sagemaker", 
                        region_name= "eu-central-1",
                        aws_access_key_id=st.secrets.default.aws_access_key_id,
                        aws_secret_access_key=st.secrets.default.aws_secret_access_key,
                        aws_session_token=st.secrets.default.aws_session_token,
)

with st.sidebar:
    st.image(LOGO_URL)
    if st.button("Nuova conversazione", type="primary"):
        for key in st.session_state.keys():
            del st.session_state[key]
        logging.info("Reset storico conversazione per scelta dell'utente")

    st.divider()

    model = st.selectbox(
        "Selezione il modello con cui interagire",
        ("Mistral", "Mistral DeepMount"))


# if model == 'Mistral':
logging.info(f'Modello scelto: {model}')
st.title("LLM NAZIONALE")
st.header(model)   

# if model == 'Mistral DeepMount': 
#     logging.info(f'Modello scelto: {model}')
#     st.title("LLM NAZIONALE")


if "history" not in st.session_state:
    st.session_state["history"] = History()
    logging.info('Inizializzazione storico conversazione')

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] == "user":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    else:
        with st.chat_message(message["role"], avatar=BOT_LOGO_URL):
            st.markdown(message["content"])

if prompt := st.chat_input("Scrivi.."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        st.session_state["history"].add(subject="Umano", message=prompt)
        message = st.session_state["history"].format()

    payload = {
        "inputs": message,
        "parameters": {"max_new_tokens": 256, "stop":["[|Umano|]"]},
        "stream": True
        }

    if model == 'Mistral':
        with st.chat_message("assistant", avatar=BOT_LOGO_URL):
            stream = client.invoke_endpoint_with_response_stream(
                EndpointName="llm-nazionale-mistral-demo28052024",
                Body=json.dumps(payload),
                ContentType="application/json")
        
            response = st.write_stream(response_generator(stream))
    
    elif model == 'Mistral DeepMount':
        with st.chat_message("assistant", avatar=BOT_LOGO_URL):
            stream = client.invoke_endpoint_with_response_stream(
                EndpointName="llm-nazionale-llama-demo27052024-v3",
                Body=json.dumps(payload),
                ContentType="application/json")
        
            response = st.write_stream(response_generator(stream))

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state["history"].add(subject="AI", message=response)
    print("------ OUTPUT --------")
    print(st.session_state["history"].format())
    print()

