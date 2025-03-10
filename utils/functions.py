import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
from dash import html, dash_table
from datetime import timedelta



def create_card(title, card_id, icon_class):
    return dbc.Card(
        dbc.CardBody(
            [
                html.Div(
                    [
                        html.I(
                            className=f"fas {icon_class} card-icon",
                        ),
                        html.H3(title, className="card-title"),
                    ],
                    className="d-flex align-items-center",
                ),
                html.H4(id=card_id),
            ],
            className="card-body",
        ),
        className="card",
    )

def create_table(df, total_vendas):
    # Calcula a porcentagem do total de vendas
    df["pct_total"] = (df["total"] / total_vendas) * 100

    # Renomeia colunas para exibição
    df = df.rename(
        columns={"cat_nivel3": "Nome", "total": "Total de Vendas", "pct_total": "% do Total"}
    )

    # Formatação dos valores
    df["Total de Vendas"] = df["Total de Vendas"].apply(lambda x: f"₲ {x:,.0f}".replace(",", "."))
    df["% do Total"] = df["% do Total"].apply(lambda x: f"{x:.2f}%")

    # 🔹 Criação da tabela no Dash
    table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict("records"),
        style_table={"overflowX": "auto"},
        
        # 🔹 Alinhamento por coluna
        style_data_conditional=[
            {"if": {"column_id": "Nome"}, "textAlign": "left"},
            {"if": {"column_id": "Total de Vendas"}, "textAlign": "right"},
            {"if": {"column_id": "% do Total"}, "textAlign": "center"},
        ],
        
        # 🔹 Estilos gerais da célula
        style_cell={
            "fontFamily": "Inter, sans-serif",
            "font-size": "14px",
            "padding": "5px",
            "border": "1px solid #ececec",
            "whiteSpace": "normal",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        
        # 🔹 Estilos do cabeçalho
        style_header={
            "fontFamily": "Inter, sans-serif",
            "font-size": "14px",
            "textAlign": "center",
            "fontWeight": "bold",
            "color": "#3a4552",
        },
    )
    
    return table 

# Filtra os fornecedores que iniciaram vendas no período selecionado
def new_suppliers_in_period(df, start_date, end_date):
    filtered_df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
    first_sale_dates = filtered_df.groupby("proveedor_id")["date"].min().reset_index()
    new_suppliers = first_sale_dates[first_sale_dates["date"] >= start_date]
    return new_suppliers

# Calcula o crescimento percentual das vendas
def calculate_growth(df, start_date, end_date):
    previous_period_start = start_date - timedelta(days=(end_date - start_date).days + 1)
    previous_period_end = start_date - timedelta(days=1)
    
    current_period_sales = df[(df["date"] >= start_date) & (df["date"] <= end_date)].groupby("proveedor_id")["total"].sum().reset_index()
    previous_period_sales = df[(df["date"] >= previous_period_start) & (df["date"] <= previous_period_end)].groupby("proveedor_id")["total"].sum().reset_index()
    
    growth_df = pd.merge(current_period_sales, previous_period_sales, on="proveedor_id", how="left", suffixes=("_current", "_previous"))
    growth_df["growth_percentage"] = ((growth_df["total_current"] - growth_df["total_previous"]) / growth_df["total_previous"]) * 100
    growth_df.fillna(0, inplace=True)  # Substitui NaN por 0 para novos fornecedores
    return growth_df

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

    return sales_by_supplier