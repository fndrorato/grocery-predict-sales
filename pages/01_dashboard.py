import dash
from dash import callback, dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
from utils.functions import create_card, create_table
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


dash.register_page(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    path="/dashboard",
)

import warnings

warnings.filterwarnings("ignore")

# dataset
df = pd.read_csv(
    "data/sales.csv",
    usecols=[
        "date",
        "codigo",
        "year",
        "month",
        "week",
        "categoria",
        "subcategoria",
        "cat_nivel3",
        "cat_nivel4",
        "cat_nivel5",
        "total",
        "qty",
    ],
)
# Obtém o último ano disponível
latest_year = max(df["year"].unique())


# layout
layout = dbc.Container(
    [
        html.Div(
            [
                html.H2(
                    "Visão Geral",  # title
                    className="title",
                ),
                html.Br(),

                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3(
                                    "Selecione o Ano",
                                    className="subtitle-small",
                                ),
                                dcc.Dropdown(
                                    id="year-dropdown",
                                    options=[
                                        {"label": "Todas Vendas (2023-2024)", "value": "All"}
                                    ]
                                    + [
                                        {"label": col, "value": col}
                                        for col in sorted(df["year"].unique())
                                    ],
                                    value=latest_year,  # Define o último ano como padrão
                                    clearable=True,
                                    multi=False,
                                    placeholder="Selecione o ano",
                                    className="custom-dropdown",
                                ),
                                html.Br(),
                                dcc.Checklist(
                                    id="compare-checkbox",
                                    options=[{"label": " Comparar com ano anterior", "value": "compare"}],
                                    value=[],  # Começa desativado
                                    inline=True,
                                    className="custom-checkbox",
                                ),                                
                            ],
                            width=4,
                        ),
                    ]
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            create_card("Ítens Únicos", "purchases-card", "fa-list"),
                            width=4,
                        ),
                        dbc.Col(
                            create_card("Faturamento", "spend-card", "fa-coins"),
                            width=4,
                        ),
                        dbc.Col(
                            create_card("Top Categoria", "category-card", "fa-tags"),
                            width=4,
                        ),
                    ],
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(
                                    id="sales-chart",
                                    config={"displayModeBar": False},
                                    className="chart-card",
                                    style={"height": "400px"},
                                ),
                                type="circle",
                                color="#1f3990",
                            ),
                            width=12,
                        ),
                    ],
                ),
                # Adicionar um segundo gráfico para vendas diárias
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(
                                    id="daily-sales-chart",
                                    config={"displayModeBar": False},
                                    className="chart-card",
                                    style={"height": "400px"},
                                ),
                                type="circle",
                                color="#1f3990",
                            ),
                            width=12,
                        ),
                    ],
                    id="daily-sales-container",  # ID para controlar a visibilidade
                    style={"display": "none"},  # Começa oculto
                ),
                
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(
                                    id="week-chart",
                                    config={"displayModeBar": False},
                                    className="chart-card",
                                    style={"height": "400px"},
                                ),
                                type="circle",
                                color="#1f3990",
                            ),
                            width=12,
                        ),
                    ],
                ),                
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Loading(
                                dcc.Graph(
                                    id="category-chart",
                                    config={"displayModeBar": False},
                                    className="chart-card",
                                    style={"height": "400px"},
                                ),
                                type="circle",
                                color="#1f3990",
                            ),
                            width=12,
                        ),
                    ],
                ), 
                html.Br(),
                # Nova seção para as tabelas
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4("Top 10 Categorias com Maiores Vendas"),
                            width=12,
                            className="text-center mt-3",
                        ),                        
                        dbc.Col(
                            dcc.Loading(
                                html.Div(
                                    id="top10-maiores-vendas",
                                    className="chart-card",
                                    style={"padding": "20px", "borderRadius": "10px", "backgroundColor": "#ffffff"},
                                ),
                                type="circle",
                                color="#1f3990",
                            ),
                            width=12,
                        ),
                    ],
                ),
                 
                html.Br(),
                # Nova seção para as tabelas
                dbc.Row(
                    [
                        dbc.Col(
                            html.H4("Top 10 Categorias com Menores Vendas"),
                            width=12,
                            className="text-center mt-3",
                        ),                        
                        dbc.Col(
                            dcc.Loading(
                                html.Div(
                                    id="top10-menores-vendas",
                                    className="dash-table-container",
                                    style={"padding": "20px", "borderRadius": "10px", "backgroundColor": "#ffffff"},
                                ),
                                type="circle",
                                color="#1f3990",
                            ),
                            width=12,
                        ),
                    ],
                ),              
                               
            ],
            className="page-content",
        )
    ],
    fluid=True,
)


# callback cards and graphs
@callback(
    [
        Output("purchases-card", "children"),
        Output("spend-card", "children"),
        Output("category-card", "children"),
        Output("sales-chart", "figure"),
        Output("week-chart", "figure"),
        Output("category-chart", "figure"),
        Output("top10-maiores-vendas", "children"),
        Output("top10-menores-vendas", "children"),
    ],
    [
        Input("year-dropdown", "value"),
        Input("compare-checkbox", "value"),
    ],
)
def update_values(select_year, compare_value):

    filtered_df = df.copy()

    # filter
    if select_year and select_year != "All":
        filtered_df = filtered_df[filtered_df["year"] == select_year]

    # cards
    # Contar códigos únicos onde a soma total de qty é maior que 0
    purchases_card = f"{(filtered_df.groupby('codigo')['qty'].sum() > 0).sum():,.0f}"
    spend_card = f"$ {round(filtered_df['total'].sum(), -2):,.0f}"
    category_card = filtered_df.groupby("categoria")["total"].sum().idxmax()


    # sales
    # Obtém os dados do ano selecionado
    df_selected_year = filtered_df.groupby("month", observed=True)["total"].sum().reset_index()
    df_selected_year["year"] = str(select_year)  # 🔹 Converte ano para string para evitar problemas de mapeamento de cor

    # Define prev_year como None inicialmente
    prev_year = None  

    # Se a comparação estiver ativada, adiciona os dados do ano anterior
    if "compare" in compare_value and select_year and select_year != "All":
        prev_year = str(int(select_year) - 1)  # 🔹 Garante que prev_year seja uma string
        df_prev_year = df[df["year"] == int(prev_year)].groupby("month", observed=True)["total"].sum().reset_index()
        df_prev_year["year"] = prev_year  

        # Junta os dois DataFrames
        df_combined = pd.concat([df_selected_year, df_prev_year], ignore_index=True)
    else:
        df_combined = df_selected_year

    # Mapeamento de cores
    color_map = {
        str(select_year): "#1f3990",
    }
    if prev_year:  # 🔹 Só adiciona a cor do ano anterior se ele existir
        color_map[prev_year] = "#da4624"

    # Gera o gráfico
    sales_chart = px.bar(
        df_combined,
        x="month",
        y="total",
        color="year",  # 🔹 Diferencia os anos automaticamente
        barmode="group",  # 🔹 Garante barras lado a lado
        text_auto=".2s",
        title="Vendas por Mês",
        labels={"month": "Mês", "total": "Faturamento", "year": "Ano"},
        color_discrete_map=color_map,  # 🔹 Aplica o mapeamento de cores corrigido
    )

    # Configurações adicionais
    sales_chart.update_layout(
        margin=dict(l=35, r=35, t=60, b=40),
        legend=dict(
            title="Ano",
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    sales_chart.update_traces(
        textposition="outside",
        hoverlabel=dict(bgcolor="rgba(255, 255, 255, 0.1)", font_size=12),
        hovertemplate="<b>%{x}</b><br>Valor: %{y:,}<extra></extra>",
    )


    if "compare" in compare_value:  
        prev_year = str(int(select_year) - 1)
        df_prev_year = df[df["year"] == int(prev_year)].copy()

        df_prev_year["year"] = prev_year  # Converte para string para diferenciar no gráfico
        filtered_df["year"] = str(select_year)

        filtered_df = pd.concat([filtered_df, df_prev_year])  # Junta os dados dos dois anos

    # Agrupa por semana e ano
    df_grouped = filtered_df.groupby(["week", "year"])["total"].sum().reset_index()

    # Define cores fixas
    color_map = {str(select_year): "#1f3990"}
    if prev_year:
        color_map[prev_year] = "#da4624"

    # 🔹 Criação do gráfico semanal com comparação
    week_chart = px.line(
        df_grouped,
        x="week",
        y="total",
        color="year",  # Diferencia os anos pela cor
        markers=True,
        title=f"Vendas Semanais ({select_year}{' vs ' + prev_year if 'compare' in compare_value else ''})",
        labels={"week": "Semana", "total": "Total de Vendas"},
        color_discrete_map=color_map,  # 🔹 Aplica cores fixas
    ) 

    # category   
    # Verifica se há valores não numéricos na coluna 'total'
    filtered_df['total'] = filtered_df['total'].fillna(0)
   
    # Agrupa os dados e calcula o total
    grouped_df = filtered_df.groupby(
        ["categoria", "subcategoria", "cat_nivel3", "cat_nivel4", "cat_nivel5"],
        as_index=False,
        observed=True
    )["total"].sum()

    # Calcula o total geral
    total_geral = grouped_df["total"].sum()

    # Calcula a porcentagem em relação ao total geral
    grouped_df["pct_total"] = (grouped_df["total"] / total_geral) * 100

    # Calcula a porcentagem em relação à categoria (nível superior)
    grouped_df["pct_categoria"] = grouped_df.groupby("categoria")["total"].transform(
        lambda x: (x / x.sum()) * 100
    )
    
    # Cria o gráfico de treemap
    category_chart = px.treemap(
        grouped_df,
        path=["categoria", "subcategoria", "cat_nivel3", "cat_nivel4", "cat_nivel5"],  # Define a hierarquia
        values="total",  # Mantém o valor total para o tamanho dos retângulos
        title="Faturamento por Categoria",
        color="categoria",
        color_discrete_sequence=px.colors.sequential.Blues,  # Paleta de azuis
        hover_data={"pct_total": ":.2f%", "pct_categoria": ":.2f%"}  # Exibe as porcentagens no hover
    )

    # Ajustes visuais
    category_chart.data[0].textinfo = "label+percent parent"  # Mostra o valor e a porcentagem em relação ao nível superior
    category_chart.update_traces(textfont=dict(size=13))
    category_chart.update_layout(margin=dict(l=35, r=35, t=60, b=35), hovermode=False)
    
    total_vendas = filtered_df["total"].sum()
    # Agrupa e seleciona as 10 categorias com maiores vendas
    top10_maiores_vendas = (
        filtered_df.groupby("cat_nivel3", as_index=False)["total"]
        .sum()
        .nlargest(10, "total")
    )
    
    table_top10_maiores = create_table(top10_maiores_vendas, total_vendas)
    
    # Top 10 categorias com menores vendas
    top10_menores_vendas = (
        filtered_df.groupby("cat_nivel3", as_index=False)["total"]
        .sum()
        .nsmallest(10, "total")
    )
    
    table_top_10_menores = create_table(top10_menores_vendas, total_vendas)
       

    return (
        purchases_card, 
        spend_card, 
        category_card, 
        sales_chart, 
        week_chart, 
        category_chart, 
        table_top10_maiores, 
        table_top_10_menores,
    )
    
@callback(
    [
        Output("daily-sales-chart", "figure"),
        Output("daily-sales-container", "style"),
    ],
    [
        Input("year-dropdown", "value"),
        Input("sales-chart", "clickData"), 
        Input("compare-checkbox", "value"),
    ],  
)
def update_daily_sales(select_year, click_data, compare_value):
    if not click_data:
        return {}, {"display": "none"}  # Oculta o gráfico se nenhum mês for clicado

    selected_month = click_data["points"][0]["x"]  # Mês clicado
    df_filtered = df[df["month"] == selected_month].copy()

    prev_year = None  # Inicializa prev_year

    if select_year and select_year != "All":
        df_filtered = df_filtered[df_filtered["year"] == select_year]

    if "compare" in compare_value:  
        prev_year = str(int(select_year) - 1)
        df_prev_year = df[(df["month"] == selected_month) & (df["year"] == int(prev_year))].copy()

        df_prev_year["year"] = prev_year  # Ajusta a coluna 'year' para string
        df_filtered["year"] = str(select_year)

        df_filtered = pd.concat([df_filtered, df_prev_year])  # Junta os dados dos dois anos

    # Agrupa por data e ano para permitir comparação
    df_grouped = df_filtered.groupby(["date", "year"])["total"].sum().reset_index()

    # Converte a coluna 'date' para datetime
    df_grouped["date"] = pd.to_datetime(df_grouped["date"])

    # Formata a coluna 'date' para exibir apenas dia/mês
    df_grouped["dia_mes"] = df_grouped["date"].dt.strftime("%d/%m")
           
    # Mapeamento de cores
    color_map = {
        str(select_year): "#1f3990",
    }
    if prev_year:  # 🔹 Só adiciona a cor do ano anterior se ele existir
        color_map[prev_year] = "#da4624"        

    # Gráfico de linha para comparar os anos
    daily_sales_chart = px.line(
        df_grouped,
        x="dia_mes",  # Usa a coluna formatada
        y="total",
        color="year",  # Diferencia os anos pela cor
        markers=True,
        title=f"Vendas Diárias - {selected_month} ({select_year}{' vs ' + prev_year if 'compare' in compare_value else ''})",
        labels={"dia_mes": "Dias do Mês", "total": "Total de Vendas"},
        color_discrete_map=color_map,  # 🔹 Aplica cores fixas
    )

    return daily_sales_chart, {"display": "block"}

