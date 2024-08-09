# Instalar bibliotecas
#%pip install langchain-community langchain langchain-google-genai
#https://python.langchain.com/


# Autenticação na API do Google
import os
import requests
import json
import pickle
import pandas as pd
from settings import OPENAI_API_KEY
from openai import OpenAI
from langchain.docstore.document import Document
from langchain_community.document_loaders import WebBaseLoader

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ['USER_AGENT'] = "sentimento_ata/1.0 (mwbrisac@icconsult.net)"
# Coleta de dados ----

def send_prompt_to_openai(prompt, client):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"user", "content":prompt}],
    )
    return response.choices[0].message.content

def configura_persona(client):
    persona= "Você é um economista experiente especializado em política monetária. Sua tarefa é analisar atas publicadas pelo banco central e concluir qual é a probabilidade do banco central aumentar ou baixar os juros na sua próxima reunião."
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system", "content":persona}],
    )

def envia_prompt(client, documento):
    #prompt="Você é um cientista de dados experiente em machine learning e em NLP, dominando as técnicas de análise de sentimentos. Sua tarefa é analisar o sentimento do texto a seguir. "
    prompt="Baseado na sua interpretação do texto a seguir, retorne qual é a probalidade percentual do Banco Central cortar juros na sua próxima reunião e qual é a probabilidade dele subir os juros. Retorne apenas as probabilidades, sem a sua interpretação do texto: "    
    prompt+=documento.page_content

    response_text = send_prompt_to_openai(prompt, client)
    resp=[]
    for partial in response_text.split("\n"):
        resp.append(float(partial.split("\n")[0].rstrip().split(" ")[-1].replace("%","")))
    return resp



def coleta_atas():
    ultima_ata = requests.get(
    "https://www.bcb.gov.br/api/servico/sitebcb/copom/atas?quantidade=1"
    ).json()["conteudo"][0]["nroReuniao"]

    url_ata = "https://www.bcb.gov.br/api/servico/sitebcb/copom/atas_detalhes?nro_reuniao="

    documentos = []
    for num in list(range(232, ultima_ata + 1)):
        ata = WebBaseLoader(f"{url_ata}{num}").load()
        conteudo = json.loads(ata[0].page_content)["conteudo"][0]
        documentos.append(
            Document(
                page_content = conteudo["textoAta"],
                metadata = {"data": conteudo["dataReferencia"]}
            )
        )
    return documentos


if __name__ == "__main__":

    with open("atas.pkl","rb") as f:
        docs=pickle.load(f)

    client=OpenAI()
    x=configura_persona(client)
    dados=[]
    for doc in docs[:10]:
        x=envia_prompt(client,doc)
        print(doc.metadata["data"]+" - Corte: "+str(x[0])+" - Alta: "+str(x[1]))
        dados.append({"data":doc.metadata["data"],
                      "corte":x[0],
                      "alta" :x[1]
                      })

    

        