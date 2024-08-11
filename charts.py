import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

colors=["#2C4257",    #paleta não oficial
        "#6A98B0",
        "#708F92",
        "#A3ABA4",
        "#605869",  
        "#948794",
        "#F8B865",  
        "#D3782F"            
        ]

chart_horizontal_layout = dict(
    width=1500,
    height=500,
    margin={"l":100,"r":20},
    font={"family":"Segoe UI"},
    legend={"yanchor":"bottom",
            "xanchor":"left",
            "x":0,
            "y":-0.2,
            "orientation":"h"},
    #shapes=recs,
    #yaxis={
    #    "tickformat":".0%"
    #    },
    xaxis={
        "domain": [0, 0.97]  # Set the domain of the x-axis to use 90% of the available space
    },
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)'
)



def get_figure(df:pd.DataFrame)->go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    fig.add_trace(go.Scatter(name='modelo', x=df.index, y=df["modelo"].values, mode='lines+markers',line={"color":colors[0]}))
    #fig.add_trace(go.Scatter(name='modelo', x=df.index, y=df["divergencia"].values, mode='lines+markers',line={"color":colors[3]}), secondary_y=True)
    fig.add_trace(go.Bar(name='proxima decisão', x=df.index, y=df["prox movimento"], marker_color=colors[6]))
    # Change the bar mode
    fig.update_layout(chart_horizontal_layout,barmode='group')
    fig.update_yaxes(ticktext = ["redução","manutenção","aumento"], tickmode="array", tickvals=[-1,0,1])
    #fig.update_yaxes(labelalias={"-1":"Corte", "1":"Alta",  "0":"manutenção"})
    return fig