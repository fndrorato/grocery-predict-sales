import dash
from dash import callback, dcc, html, Input, Output, dash_table, State
import dash_bootstrap_components as dbc
import os
import xgboost as xgb
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


dash.register_page(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    path="/predict_sales",
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

df_items = pd.read_csv(
    "data/items.csv",
    usecols=[
        "codigo",
        "descripcion",
        "proveedor_id",
    ],
)

df_sales = pd.read_csv(
    "data/sales.csv",
    usecols=[
        "date",
        "codigo",
        "year",
        "month",
        "qty",
    ],
)
# Obtém o último ano disponível
latest_year = max(df_sales["year"].unique())
# Obter o ano atual
current_year = datetime.now().year

# Filtrar o DataFrame pelo ano anterior (ano atual - 1)
df_sales = df_sales[df_sales["year"] == current_year - 1]
df_sales['date'] = pd.to_datetime(df_sales['date'])  # Garantir que a data esteja no formato datetime


# Ordena os fornecedores pelo nome
df_proveedor = df_proveedor.sort_values(by="name")

# Ordena os fornecedores pelo nome
df_items = df_items.sort_values(by="descripcion")

# converte o codigo para string
df_items["codigo"] = df_items["codigo"].astype(str)

# layout
layout = dbc.Container(
    [
        html.Div(
            [
                html.H2(
                    "Previsão de Vendas",  # title
                    className="title",
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                html.H3(
                                    "Selecione o Proveedor",
                                    className="subtitle-small",
                                ),
                                dcc.Dropdown(
                                    id="proveedor-dropdown",
                                    options=[{"label": "Selecione um proveedor", "value": ""}]  # Opção padrão
                                    + [
                                        {"label": f"({proveedor_id}) - {name}", "value": str(proveedor_id)}  
                                        for proveedor_id, name in zip(df_proveedor["proveedor_id"], df_proveedor["name"])
                                    ],
                                    value="",  # Mantém a opção "Selecione um proveedor" pré-selecionada
                                    clearable=True,
                                    multi=False,
                                    placeholder="Selecione um proveedor",
                                    className="custom-dropdown",
                                ),
                            ],
                            width=6,
                        ),
                        dbc.Col(
                            [
                                html.H3(
                                    "Selecione un Item",
                                    className="subtitle-small",
                                ),
                                dcc.Dropdown(
                                    id="item-dropdown",
                                    options=[{"label": "Selecione um produto", "value": ""}]  # Opção padrão
                                    + [
                                        {"label": f"({codigo}) - {descripcion}", "value": str(codigo)}  
                                        for codigo, descripcion in zip(df_items["codigo"], df_items["descripcion"])
                                    ],
                                    value="",  # Mantém a opção "Selecione um produto" pré-selecionada
                                    clearable=True,
                                    multi=False,
                                    placeholder="Selecione um produto",
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
                                        date=pd.to_datetime("today").strftime("%Y-%m-%d"),  # Data padrão (hoje)
                                        display_format="DD/MM/YYYY",
                                        placeholder="Data Inicial",
                                        className="custom-date-picker",
                                    ),                       
                                ],
                                className="d-flex align-items-center",  # Aplica a classe de alinhamento
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H3("Data Final", className="subtitle-small"),
                                    dcc.DatePickerSingle(
                                        id="data-final",
                                        date=pd.to_datetime("today").strftime("%Y-%m-%d"),  # Data padrão (hoje)
                                        display_format="DD/MM/YYYY",
                                        placeholder="Data Final",
                                        className="custom-date-picker",
                                    ),                       
                                ],
                                className="d-flex align-items-center",  # Aplica a classe de alinhamento
                            ),
                            width=3,
                        ),
                        dbc.Col(
                            dbc.Button(
                                "Gerar Previsão de Vendas",
                                id="gerar-previsao-btn",
                                color="primary",
                                className="me-2 mt-auto",  # mt-auto empurra o botão para baixo
                                n_clicks=0,
                            ),
                            width=4,
                            className="d-flex flex-column",  # Define altura total e organiza os elementos na coluna
                        ),                  
                    ]
                ),                
                html.Br(),
                # Div para exibir a previsão de vendas
                html.Div(id="previsao-output"),                      
            ],
            className="page-content",
        )
    ],
    fluid=True,
)


@callback(
    Output("previsao-output", "children"),        
    Input("gerar-previsao-btn", "n_clicks"),  # Somente o botão como Input
    State("proveedor-dropdown", "value"),
    State("item-dropdown", "value"),
    State("data-inicial", "date"),
    State("data-final", "date"),
    prevent_initial_call=True,  # Garante que só executa após clicar no botão
)
def gerar_previsao(n_clicks, fornecedor, item, data_inicial, data_final):
    if not data_inicial or not data_final:
        return [html.Div("Selecione um período válido.", style={"color": "red"})]

    # Converter datas para datetime
    data_inicial = pd.to_datetime(data_inicial)
    data_final = pd.to_datetime(data_final)

    # Definir diretório de modelos
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Diretório atual
    BASE_DIR = os.path.dirname(BASE_DIR)  # Sobe um nível para a raiz

    # Se o usuário escolheu um fornecedor mas não escolheu um item
    if fornecedor and not item:
        # Verificar se o fornecedor é válido para conversão
        try:
            fornecedor = int(fornecedor)
        except (ValueError, TypeError):
            # Caso a conversão falhe, você pode retornar uma mensagem de erro ou um valor padrão
            return [html.Div("Fornecedor inválido. Por favor, selecione um fornecedor válido.", style={"color": "red"})]
        
        # Filtrar os itens pertencentes ao fornecedor
        itens_do_fornecedor = df_items[df_items['proveedor_id'] == fornecedor]['codigo'].tolist()

        if not itens_do_fornecedor:
            return [html.Div("O fornecedor selecionado não possui produtos com previsão de vendas.", style={"color": "red"})]

        todas_as_previsoes = []  # Lista para armazenar previsões de cada item
        modelos_encontrados = False  # Flag para verificar se encontrou modelos

        # Loop pelos itens do fornecedor
        for item_codigo in itens_do_fornecedor:
            modelo_path = os.path.join(BASE_DIR, "modelos", f"modelo_{item_codigo}.json")
            
            if os.path.exists(modelo_path):
                modelos_encontrados = True
                model = xgb.XGBRegressor()
                model.load_model(modelo_path)

                # Criar datas futuras
                future_dates = pd.date_range(start=data_inicial, end=data_final, freq='D')
                future_df = pd.DataFrame({'ds': future_dates})
                future_df['year'] = future_df['ds'].dt.year
                future_df['month'] = future_df['ds'].dt.month
                future_df['week'] = future_df['ds'].dt.isocalendar().week
                future_df['is_weekend'] = future_df['ds'].dt.weekday >= 5
                future_df['is_week_holiday'] = 0
                future_df['is_week_payday'] = future_df['ds'].dt.day.isin([1, 5, 10, 15, 20, 25])
                future_df['is_holiday'] = 0

                # Selecionar features para previsão
                features = ['year', 'month', 'week', 'is_holiday', 'is_weekend', 'is_week_holiday', 'is_week_payday']
                future_X = future_df[features]

                # Fazer previsão
                future_df['qty_pred'] = model.predict(future_X)
                future_df['codigo'] = item_codigo

                # Adicionar dados do item
                future_df = future_df.merge(df_items[['codigo', 'descripcion', 'proveedor_id']], on='codigo', how='left')
                # Adicionar nome do fornecedor
                future_df = future_df.merge(df_proveedor[['proveedor_id', 'name']], on='proveedor_id', how='left')

                # Arredondar valores
                future_df['qty_pred'] = pd.to_numeric(future_df['qty_pred'], errors='coerce').round(3)

                # Agregar previsões por semana
                df_semana = future_df.groupby(['week', 'codigo', 'descripcion', 'name']).agg({'qty_pred': 'sum'}).reset_index()

                todas_as_previsoes.append(df_semana)

        # Se nenhum modelo foi encontrado, retornar mensagem
        if not modelos_encontrados:
            return [html.Div("O fornecedor selecionado não possui produtos com previsão de vendas.", style={"color": "red"})]

        # Concatenar todas as previsões em um único DataFrame
        resultado_final = pd.concat(todas_as_previsoes, ignore_index=True)

    else:  # Se um item foi selecionado
        modelo_path = os.path.join(BASE_DIR, "modelos", f"modelo_{item}.json")

        if not os.path.exists(modelo_path):
            return [html.Div(f"Modelo para o item {item} não encontrado.", style={"color": "red"})]

        model = xgb.XGBRegressor()
        model.load_model(modelo_path)

        # Criar datas futuras
        future_dates = pd.date_range(start=data_inicial, end=data_final, freq='D')
        future_df = pd.DataFrame({'ds': future_dates})
        future_df['year'] = future_df['ds'].dt.year
        future_df['month'] = future_df['ds'].dt.month
        future_df['week'] = future_df['ds'].dt.isocalendar().week
        future_df['is_weekend'] = future_df['ds'].dt.weekday >= 5
        future_df['is_week_holiday'] = 0
        future_df['is_week_payday'] = future_df['ds'].dt.day.isin([1, 5, 10, 15, 20, 25])
        future_df['is_holiday'] = 0

        # Selecionar features para previsão
        features = ['year', 'month', 'week', 'is_holiday', 'is_weekend', 'is_week_holiday', 'is_week_payday']
        future_X = future_df[features]

        # Fazer previsão
        future_df['qty_pred'] = model.predict(future_X)
        future_df['codigo'] = item

        # Adicionar dados do item
        future_df = future_df.merge(df_items[['codigo', 'descripcion', 'proveedor_id']], on='codigo', how='left')
        # Adicionar nome do fornecedor
        future_df = future_df.merge(df_proveedor[['proveedor_id', 'name']], on='proveedor_id', how='left')

        # Arredondar valores
        future_df['qty_pred'] = pd.to_numeric(future_df['qty_pred'], errors='coerce').round(3)

        # Agregar previsões por semana
        resultado_final = future_df.groupby(['week', 'codigo', 'descripcion', 'name']).agg({'qty_pred': 'sum'}).reset_index()

    # Garantir que não existam valores negativos em 'qty_pred'
    resultado_final['qty_pred'] = resultado_final['qty_pred'].clip(lower=0)
    
    # **Adicionando as vendas reais do ano anterior**

    # Ajustar data_inicial e data_final para o ano passado
    data_inicial_last_year = data_inicial.replace(year=latest_year)
    data_final_last_year = data_final.replace(year=latest_year)

    # Agora filtrar df_sales com base nas datas ajustadas
    df_sales_filtered = df_sales[
        (df_sales['date'] >= data_inicial_last_year) & 
        (df_sales['date'] <= data_final_last_year)
    ]

    # Adicionar a coluna de semana em df_sales_filtered
    df_sales_filtered['week'] = df_sales_filtered['date'].dt.isocalendar().week
    df_sales_filtered['codigo'] = df_sales_filtered['codigo'].astype(str)
    df_sales_filtered = df_sales_filtered.groupby(['week', 'codigo']).agg({'qty': 'sum'}).reset_index()
    
    # Fazer o merge entre as previsões e as vendas reais do ano anterior
    resultado_final = resultado_final.merge(
        df_sales_filtered[['week', 'codigo', 'qty']],  # Garantir que 'vendas_real' existe no df_sales
        on=['week', 'codigo'], 
        how='left'
    )    

    # Criar tabela Dash com os dados finais
    tabela_dash = dash_table.DataTable(
        columns=[
            {"name": "Código", "id": "codigo"},
            {"name": "Descrição", "id": "descripcion"},
            {"name": "Fornecedor", "id": "name"},            
            {"name": "Semana", "id": "week"},
            {"name": "Previsão de Vendas", "id": "qty_pred", "type": "numeric", "format": {"specifier": ".3f"}},
            {"name": "Último Ano", "id": "qty", "type": "numeric", "format": {"specifier": ".3f"}},
            
        ],
        data=resultado_final.to_dict("records"),
        style_table={'overflowX': 'auto'},
        style_cell={
            "textAlign": "center",
            "fontFamily": "Inter, sans-serif",
            "font-size": "14px",
            "padding": "5px",
            "border": "1px solid #ececec",
            "whiteSpace": "normal",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        
        # Estilos do cabeçalho
        style_header={
            "fontFamily": "Inter, sans-serif",
            "font-size": "14px",
            "textAlign": "center",
            "fontWeight": "bold",
            "color": "#3a4552",
        },        
    )

    return [tabela_dash]
