import dash
from dash import callback, dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
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
            ],
            className="page-content",
        )
    ],
    fluid=True,
)

# Função para calcular a classificação ABC
def calculate_abc(df, start_date, end_date):
    # Calcula o mesmo período do ano anterior
    previous_start_date = start_date - pd.DateOffset(years=1)
    previous_end_date = end_date - pd.DateOffset(years=1)

    # Filtra os dados para o período atual
    current_period = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

    # Filtra os dados para o mesmo período do ano anterior
    previous_period = df[(df["date"] >= previous_start_date) & (df["date"] <= previous_end_date)]

    # Agrupa por fornecedor e calcula:
    # - Total de vendas no período atual
    # - Contagem de códigos únicos no período atual
    current_sales = (
        current_period.groupby(["proveedor_id", "proveedor"])
        .agg(
            total_current=("total", "sum"),  # Total de vendas no período atual
            unique_codes_current=("codigo", "nunique")  # Contagem de códigos únicos no período atual
        )
        .reset_index()
    )

    # Agrupa por fornecedor e calcula o total de vendas no período anterior
    previous_sales = (
        previous_period.groupby(["proveedor_id", "proveedor"])
        .agg(total_previous=("total", "sum"))  # Total de vendas no período anterior
        .reset_index()
    )

    # Combina os dados do período atual e do período anterior
    sales_by_supplier = pd.merge(current_sales, previous_sales, on=["proveedor_id", "proveedor"], how="left")

    # Preenche valores NaN com 0 para fornecedores sem vendas no período anterior
    sales_by_supplier["total_previous"] = sales_by_supplier["total_previous"].fillna(0)

    # Calcula o crescimento percentual
    sales_by_supplier["growth_percentage"] = (
        (sales_by_supplier["total_current"] - sales_by_supplier["total_previous"]) / sales_by_supplier["total_previous"]
    ) * 100
    sales_by_supplier["growth_percentage"] = sales_by_supplier["growth_percentage"].fillna(0)  # Substitui NaN por 0

    # Ordena os fornecedores pelo total de vendas no período atual em ordem decrescente
    sales_by_supplier = sales_by_supplier.sort_values(by="total_current", ascending=False)

    # Adiciona a coluna de posição (ranking)
    sales_by_supplier["posicao"] = range(1, len(sales_by_supplier) + 1)

    # Calcula a porcentagem de vendas sobre o total no período atual
    total_sales_current = sales_by_supplier["total_current"].sum()
    sales_by_supplier["percentage_of_total"] = (sales_by_supplier["total_current"] / total_sales_current) * 100

    # Calcula a porcentagem acumulada
    sales_by_supplier["cumulative_percentage"] = (
        sales_by_supplier["total_current"].cumsum() / total_sales_current * 100
    )

    # Classifica os fornecedores como A, B ou C usando numpy.select
    conditions = [
        (sales_by_supplier["cumulative_percentage"] <= 70),
        (sales_by_supplier["cumulative_percentage"] > 70) & (sales_by_supplier["cumulative_percentage"] <= 90),
        (sales_by_supplier["cumulative_percentage"] > 90)
    ]
    choices = ["A", "B", "C"]
    sales_by_supplier["classificacao"] = np.select(conditions, choices, default="C")
    
    print(sales_by_supplier.columns)

    return sales_by_supplier

@callback(
    [
        Output("abc-chart", "figure"),
        Output("abc-table", "children"),  # Atualiza o conteúdo da div
    ],
    [
        Input("gerar-previsao-btn", "n_clicks"),
        Input("proveedor-dropdown", "value"),
        Input("data-inicial", "date"),
        Input("data-final", "date"),
    ],
)
def update_dashboard(n_clicks, selected_supplier, start_date, end_date):
    if not n_clicks:
        return {}, [],

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

    # Cria a tabela ABC com o estilo personalizado
    table = dash_table.DataTable(
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
        ],
        data=abc_data_for_table.to_dict("records"),
        style_table={"overflowX": "auto"},
        # 🔹 Alinhamento por coluna
        style_data_conditional=[
            {"if": {"column_id": "posicao"}, "textAlign": "center"},
            {"if": {"column_id": "proveedor"}, "textAlign": "left"},  # Alinha à esquerda
            {"if": {"column_id": "total_current"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "total_previous"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "growth_percentage"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "percentage_of_total"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "cumulative_percentage"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "unique_codes_current"}, "textAlign": "right"},  # Alinha à direita
            {"if": {"column_id": "classificacao"}, "textAlign": "center"},  # Centraliza
        ],
        # 🔹 Estilos gerais da célula
        style_cell={
            "fontFamily": "Inter, sans-serif",
            "fontSize": "14px",
            "padding": "5px",
            "border": "1px solid #ececec",
            "whiteSpace": "normal",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        # 🔹 Estilos do cabeçalho
        style_header={
            "fontFamily": "Inter, sans-serif",
            "fontSize": "14px",
            "textAlign": "center",
            "fontWeight": "bold",
            "color": "#3a4552",
            "backgroundColor": "#f7f7f7",  # Fundo claro para o cabeçalho
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
