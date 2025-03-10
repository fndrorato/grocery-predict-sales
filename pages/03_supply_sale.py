import dash
from dash import callback, dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.functions import calculate_abc
from datetime import datetime


dash.register_page(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    path="/supplier_sales",
)

import warnings

warnings.filterwarnings("ignore")

# dataset
df_proveedor = pd.read_csv(
    "data/proveedor.csv",
    usecols=[
        "proveedor_id",
        "name",
    ],
)

# Remove duplicados com base na coluna 'cod_proveedor', mantendo a última ocorrência
df_proveedor = df_proveedor.drop_duplicates(subset=['proveedor_id'], keep='last')

df_item = pd.read_csv(
    "data/items.csv",
    usecols=[
        "codigo",
        "descripcion",
    ],
)

df_item = df_item.drop_duplicates(subset=['codigo'])

df_sales = pd.read_csv(
    "data/sales_proveedor.csv",
    usecols=[
        "date",
        "codigo",
        "year",
        "month",
        "week",
        "proveedor",
        "proveedor_id",
        "categoria",
        "subcategoria",
        "cat_nivel3",
        "total",
        "qty",
    ],
)
# Obtém o último ano disponível
latest_year = max(df_sales["year"].unique())
# Obter o ano atual
current_year = datetime.now().year

# Filtrar o DataFrame pelo ano anterior (ano atual - 1)
df_sales['date'] = pd.to_datetime(df_sales['date'])  # Garantir que a data esteja no formato datetime


# Ordena os fornecedores pelo nome
df_proveedor = df_proveedor.sort_values(by="name")

# layout
layout = dbc.Container(
    [
        html.Div(
            [
                html.H2("Vendas por Fornecedor", className="title"),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3("Selecione o Proveedor", className="subtitle-small"),
                                dcc.Dropdown(
                                    id="proveedor-dropdown",
                                    options=[{"label": "Selecione um proveedor", "value": ""}]
                                    + [
                                        {"label": f"({proveedor_id}) - {name}", "value": str(proveedor_id)}
                                        for proveedor_id, name in zip(df_proveedor["proveedor_id"], df_proveedor["name"])
                                    ],
                                    value="",
                                    clearable=True,
                                    multi=False,
                                    placeholder="Selecione um proveedor",
                                    className="custom-dropdown",
                                ),
                            ],
                            width=6,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H3("Data Inicial", className="subtitle-small"),
                                    dcc.DatePickerSingle(
                                        id="data-inicial",
                                        date=pd.to_datetime("today").strftime("%Y-%m-%d"),
                                        display_format="DD/MM/YYYY",
                                        placeholder="Data Inicial",
                                        className="custom-date-picker",
                                    ),
                                ],
                                className="d-flex align-items-center",
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H3("Data Final", className="subtitle-small"),
                                    dcc.DatePickerSingle(
                                        id="data-final",
                                        date=pd.to_datetime("today").strftime("%Y-%m-%d"),
                                        display_format="DD/MM/YYYY",
                                        placeholder="Data Final",
                                        className="custom-date-picker",
                                    ),
                                ],
                                className="d-flex align-items-center",
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Atualizar Relatório",
                                id="gerar-previsao-btn",
                                color="primary",
                                className="me-2 mt-auto",
                                n_clicks=0,
                            ),
                            width=4,
                            className="d-flex flex-column",
                        ),
                    ]
                ),
                html.Br(),
                # Gráfico ABC com Loading
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                id="loading-abc-chart",
                                children=dcc.Graph(id="abc-chart", style={"height": "400px"}),
                                type="circle",  # Tipo de animação (circle, dot, default, etc.)
                            ),
                            width=12,
                        ),
                    ]
                ),
                html.Br(),
                # Tabela de Classificação ABC com Loading
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                html.Div(
                                    id="abc-table",  # ID da div que conterá a tabela
                                    className="dash-table-container",
                                    style={
                                        "padding": "20px",
                                        "borderRadius": "10px",
                                        "backgroundColor": "#ffffff",
                                        "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",  # Adiciona sombra para melhorar a aparência
                                    },
                                ),
                                type="circle",
                                color="#1f3990",  # Cor do loading spinner
                            ),
                            width=12,
                        ),
                    ]
                ),
                html.Br(),
                # Modal para exibir os produtos do fornecedor selecionado
                dbc.Modal(
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Produtos do Fornecedor"), close_button=True),
                        dbc.ModalBody(
                            dcc.Loading(
                                id="loading-products-modal",
                                children=dash_table.DataTable(
                                    id="products-table",
                                    columns=[
                                        {"name": "Código", "id": "codigo"},
                                        {"name": "Descripción", "id": "descripcion"},
                                        {"name": "Categoria", "id": "categoria"},
                                        {"name": "Subcategoria", "id": "subcategoria"},
                                        {"name": "Total de Vendas", "id": "total_vendas"},
                                        {"name": "Quantidade Vendida", "id": "quantidade_vendida"},
                                    ],                                    
                                    style_table={"overflowX": "auto"},
                                    style_data_conditional=[
                                        {"if": {"column_id": "codigo"}, "textAlign": "center"},  # Centraliza a coluna "Código"
                                        {"if": {"column_id": "descripcion"}, "textAlign": "left"},  # Alinha à esquerda
                                        {"if": {"column_id": "categoria"}, "textAlign": "left"},  # Alinha à esquerda
                                        {"if": {"column_id": "subcategoria"}, "textAlign": "left"},  # Alinha à esquerda
                                        {"if": {"column_id": "total_vendas"}, "textAlign": "right"},  # Alinha à direita
                                        {"if": {"column_id": "quantidade_vendida"}, "textAlign": "right"},  # Alinha à direita
                                    ],                                    
                                    style_cell={
                                        "fontFamily": "Inter, sans-serif",
                                        "fontSize": "14px",
                                        "padding": "5px",
                                        "border": "1px solid #ececec",
                                        "whiteSpace": "normal",
                                        "overflow": "hidden",
                                        "textOverflow": "ellipsis",
                                    },
                                    style_header={
                                        "fontFamily": "Inter, sans-serif",
                                        "fontSize": "14px",
                                        "textAlign": "center",
                                        "fontWeight": "bold",
                                        "color": "#3a4552",
                                        "backgroundColor": "#f7f7f7",
                                    },
                                ),
                                type="circle",
                                color="#1f3990",
                            )
                        ),
                        dbc.ModalFooter(
                            dbc.Button("Fechar", id="close-products-modal", className="ms-auto", n_clicks=0)
                        ),
                    ],
                    id="products-modal",
                    is_open=False,  # O modal começa fechado
                    size="lg",  # Tamanho grande para acomodar a tabela 
                    style={"maxWidth": "90% !important", "width": "90% !important"}  ,  # Ajusta a largura do modal
                ),              
            ],
            className="page-content",
        )
    ],
    fluid=True,
)

@callback(
    [
        Output("abc-chart", "figure"),
        Output("abc-table", "children"),  # Atualiza o conteúdo da div
    ],
    [
        Input("gerar-previsao-btn", "n_clicks"),
        Input("data-inicial", "n_submit"),  # Detecta Enter no campo de data inicial
        Input("data-final", "n_submit"),    # Detecta Enter no campo de data final
    ],
    [
        State("proveedor-dropdown", "value"),
        State("data-inicial", "date"),
        State("data-final", "date"),
    ],
)
def update_dashboard(n_clicks, submit_initial, submit_final, selected_supplier, start_date, end_date):
    # Verifica se algum dos eventos foi acionado
    ctx = dash.callback_context
    if not ctx.triggered:
        return {}, []

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Converte datas para datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Filtra os dados pelo período selecionado
    filtered_df = df_sales[(df_sales["date"] >= start_date) & (df_sales["date"] <= end_date)]

    # Filtra por fornecedor, se selecionado
    if selected_supplier:
        filtered_df = filtered_df[filtered_df["proveedor_id"] == int(selected_supplier)]

    # Calcula a classificação ABC
    abc_data = calculate_abc(df_sales, start_date, end_date)

    # Formata os dados para exibição na tabela ABC
    abc_data_for_table = abc_data.copy()
    abc_data_for_table["total_current"] = abc_data_for_table["total_current"].apply(lambda x: f"₲ {x:,.0f}")  # Formata como moeda Guarani
    abc_data_for_table["total_previous"] = abc_data_for_table["total_previous"].apply(lambda x: f"₲ {x:,.0f}")  # Formata como moeda Guarani
    abc_data_for_table["growth_percentage"] = abc_data_for_table["growth_percentage"].apply(lambda x: f"{x:.2f}%" if x != 0 else "-")
    abc_data_for_table["percentage_of_total"] = abc_data_for_table["percentage_of_total"].apply(lambda x: f"{x:.2f}%")
    abc_data_for_table["cumulative_percentage"] = abc_data_for_table["cumulative_percentage"].apply(lambda x: f"{x:.2f}%")
    # Adiciona uma coluna com botões na tabela ABC
    abc_data_for_table["view_button"] = abc_data_for_table.apply(
        lambda row: f"[+]",  # Cria um link com o nome do fornecedor como identificador
        axis=1,
    )

    # Cria a tabela ABC com o estilo personalizado
    table = dash_table.DataTable(
        id="abc-table",
        columns=[
            {"name": "Posição", "id": "posicao"},
            {"name": "Fornecedor", "id": "proveedor"},
            {"name": "Total de Vendas (Atual)", "id": "total_current"},
            {"name": "Total de Vendas (Anterior)", "id": "total_previous"},
            {"name": "Crescimento (%)", "id": "growth_percentage"},
            {"name": "% de Vendas", "id": "percentage_of_total"},
            {"name": "% Acumulada", "id": "cumulative_percentage"},
            {"name": "Códigos Únicos", "id": "unique_codes_current"},
            {"name": "Classificação", "id": "classificacao"},
            {"name": "Ver", "id": "view_button", "presentation": "markdown"},  # Nova coluna com botões
        ],
        data=abc_data_for_table.to_dict("records"),
        style_table={"overflowX": "auto"},
        # Alinhamento por coluna
        style_data_conditional=[
            {"if": {"column_id": "posicao"}, "textAlign": "center"},
            {"if": {"column_id": "proveedor"}, "textAlign": "left"},
            {"if": {"column_id": "total_current"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "total_previous"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "growth_percentage"}, "textAlign": "right"},
            {"if": {"column_id": "percentage_of_total"}, "textAlign": "right"},
            {"if": {"column_id": "cumulative_percentage"}, "textAlign": "right"},
            {"if": {"column_id": "unique_codes"}, "textAlign": "right"},
            {"if": {"column_id": "classificacao"}, "textAlign": "center"},
            {"if": {"column_id": "view_button"}, "textAlign": "center"},  # Centraliza os botões
        ],
        # Estilos gerais da célula
        style_cell={
            "fontFamily": "Inter, sans-serif",
            "fontSize": "14px",
            "padding": "5px",
            "border": "1px solid #ececec",
            "whiteSpace": "normal",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        # Estilos do cabeçalho
        style_header={
            "fontFamily": "Inter, sans-serif",
            "fontSize": "14px",
            "textAlign": "center",
            "fontWeight": "bold",
            "color": "#3a4552",
            "backgroundColor": "#f7f7f7",
        },
    )    

    # Gráfico ABC (Pizza)
    # Ordena os dados pela classificação (A, B, C)
    classification_counts = abc_data["classificacao"].value_counts().reset_index()
    classification_counts.columns = ["classificacao", "count"]
    classification_counts = classification_counts.sort_values(by="classificacao")  # Ordena em ordem alfabética

    # Gráfico ABC (Pizza)
    abc_chart = px.pie(
        classification_counts,
        names="classificacao",
        values="count",
        title="Distribuição de Fornecedores por Classificação ABC",
        labels={"classificacao": "Classificação", "count": "Número de Fornecedores"},
        hole=0.3,  # Donut chart
    )

    # Adiciona a legenda ao gráfico
    abc_chart.update_layout(
        legend=dict(
            orientation="h",  # Horizontal layout para a legenda
            yanchor="bottom",  # Posiciona a legenda na parte inferior
            y=-0.2,  # Ajusta a posição vertical da legenda
            xanchor="center",  # Centraliza a legenda horizontalmente
            x=0.5,  # Centraliza a legenda no meio do gráfico
            traceorder="normal",  # Mantém a ordem dos dados (alfabética)
        ),
        margin=dict(t=50, b=50, l=50, r=50),  # Ajusta as margens para evitar sobreposição
    )

    return (
        abc_chart,
        table,  # Retorna a tabela formatada para a div "top10-menores-vendas"
    )

@callback(
    [
        Output("products-modal", "is_open"),  # Controla a visibilidade do modal
        Output("products-table", "data"),  # Dados da tabela de produtos
    ],
    [
        Input("abc-table", "active_cell"),  # Detecta cliques nas células da tabela ABC
        Input("close-products-modal", "n_clicks"),  # Fecha o modal
    ],
    [
        State("products-modal", "is_open"),  # Estado atual do modal
        State("abc-table", "data"),  # Dados da tabela ABC
    ],
)
def open_products_modal(active_cell, close_clicks, is_open, abc_table_data):
    ctx = dash.callback_context

    # Verifica qual input disparou o callback
    if not ctx.triggered:
        return False, []

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # Fecha o modal se o botão "Fechar" for clicado
    if trigger_id == "close-products-modal":
        return False, []

    # Verifica se uma célula foi clicada e se é a coluna "Ver"
    if active_cell and active_cell["column_id"] == "view_button":
        # Obtém o nome do fornecedor clicado
        selected_supplier = abc_table_data[active_cell["row"]]["proveedor"]

        # Filtra os dados dos produtos vendidos pelo fornecedor
        supplier_products = df_sales[df_sales["proveedor"] == selected_supplier]
        supplier_products_summary = (
            supplier_products.groupby(["codigo", "categoria", "subcategoria", "cat_nivel3"])
            .agg(
                total_vendas=("total", "sum"),
                quantidade_vendida=("qty", "sum"),
            )
            .reset_index()
        )
        
        # Ordena os produtos pelo total de vendas em ordem decrescente
        supplier_products_summary = supplier_products_summary.sort_values(by="total_vendas", ascending=False)
        
        # Faz o merge com df_item para adicionar a coluna 'descripcion'
        supplier_products_summary = supplier_products_summary.merge(
            df_item, on="codigo", how="left"
        )        
        
        # Formata os dados para exibição
        supplier_products_summary["total_vendas"] = supplier_products_summary["total_vendas"].apply(
            lambda x: f"₲ {x:,.0f}"
        )
        supplier_products_summary["quantidade_vendida"] = supplier_products_summary["quantidade_vendida"].apply(
            lambda x: f"{x:,}"
        )

        # Converte os dados para o formato da tabela
        products_data = supplier_products_summary.to_dict("records")

        # Abre o modal e retorna os dados
        return True, products_data

    # Caso contrário, mantém o modal fechado
    return False, []