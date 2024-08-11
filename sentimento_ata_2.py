# Instalar bibliotecas
#%pip install langchain-community langchain langchain-google-genai
#https://python.langchain.com/


# Autenticação na API do Google

import os
os.environ['USER_AGENT'] = "sentimento_ata/1.0 (mwbrisac@icconsult.net)"

import requests
import json
import pickle
import pandas as pd
from settings import OPENAI_API_KEY
import plotly.graph_objects as go
from openai import OpenAI
from bs4 import BeautifulSoup
#from langchain.docstore.document import Document
#from langchain_community.document_loaders import WebBaseLoader
from charts import get_figure

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
PRIMEIRA_ATA=232

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
    prompt+=documento["texto"]#.page_content

    response_text = send_prompt_to_openai(prompt, client)
    resp=[]
    try:
        partials=[x for x in response_text.split("\n") if x!="" ]
        for partial in partials:
            resp.append(float(partial.split("\n")[0].rstrip().split(" ")[-1].replace("%","").replace(",",".")))
    except Exception as e:
        print(response_text)
        resp=[0,0]
        pass
    return resp

def pega_comunicado(num:int):
    #json.loads(x.content)["conteudo"][0]["textoAta"]
    url="https://www.bcb.gov.br/api/servico/sitebcb/copom/comunicados_detalhes?nro_reuniao="
    x = requests.get( f"{url}{num}")
    if x.status_code!=200:
        return ""
    else:
        try:
            return json.loads(x.content)["conteudo"][0]["titulo"]
        except Exception:
            pass
    return ""

def pega_ata(num:int):
    url="https://www.bcb.gov.br/api/servico/sitebcb/copom/comunicados_detalhes?nro_reuniao="
    x = requests.get( f"{url}{num}")
    if x.status_code!=200:
        return {"data":"erro","texto":"Erro ao baixar reuniao: "+str(num)}
    else:
        try:
            txt=json.loads(x.content)["conteudo"][0]["textoComunicado"]
            clean_txt= BeautifulSoup(txt, "lxml").text
            return {"data" :json.loads(x.content)["conteudo"][0]["dataReferencia"],
                    "texto":clean_txt}
        except Exception:
            pass
    return {"data":"erro","texto":"Erro no parsing da reuniao: "+str(num)}


def coleta_atas(filename:str|None=None)->list:
    """
    Devolve uma lista Documents com todas as atas desde a ata 232
    se filename for passado, le um pikle com as atas
    """

    if filename is None:
        ultima_ata = requests.get(
        "https://www.bcb.gov.br/api/servico/sitebcb/copom/atas?quantidade=1"
        ).json()["conteudo"][0]["nroReuniao"]



        documentos = []
        for num in list(range(PRIMEIRA_ATA, ultima_ata + 1)):
            #ata       = WebBaseLoader(f"{url_ata}{num}").load()
            ata       = pega_ata(num)
            if ata["texto"]!="":
                titulo    = pega_comunicado(num)
                documentos.append(ata | {"titulo":titulo})
            else:
                print("Ata sem texto: "+str(num))
    else:
        with open(filename,"rb") as f:
            documentos=pickle.load(f)
    return documentos

def calcula_modelo(docs:list)->pd.DataFrame:
    """
    Recebe um array de Documents com as atas do copom e usa o chatGPT para calcular as probabilidade de alta ou corte na proxima reunião
    retorna um dataframe com o resultado do modelo
    """
    client=OpenAI()
    x=configura_persona(client)
    dados=[]
    for doc in docs:
        x=envia_prompt(client,doc)
        #print(doc.metadata["data"]+" - Corte: "+str(x[0])+" - Alta: "+str(x[1]))
        print(doc["data"]+" - Corte: "+str(x[0])+" - Alta: "+str(x[1]))
        dados.append({"data":doc["data"],
                      "titulo":doc["titulo"],
                      "corte":x[0],
                      "alta" :x[1]})

    df=pd.DataFrame(dados).set_index("data")
    return df
    

if __name__ == "__main__":
    print("Coletando atas")
    #docs=coleta_atas()
    #with open("atas.pkl","wb") as f:
    #    pickle.dump(docs,f)
    #docs=coleta_atas("atas.pkl")
    print("Calculando modelo")
    #df=calcula_modelo(docs)    
    #df.to_csv('modelo.csv')
    df=pd.read_csv("modelo.csv",index_col="data")
    df["ação"]=df["titulo"].map(lambda x: "alta" if "eleva" in x else ("corte" if "reduz" in x else "mantem"))
    df["movimento"]=df["titulo"].map(lambda x: 1 if "eleva" in x else (-1 if "reduz" in x else 0))
    df["modelo"]=(df["alta"]-df["corte"])/100
    df["divergencia"]=(df["alta"]*df["corte"])**0.5
    df["prox movimento"]=df["movimento"].shift(-1)
    fig=get_figure(df)
    fig.show()

        