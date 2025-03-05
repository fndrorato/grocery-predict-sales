import dash_bootstrap_components as dbc
import pandas as pd
from dash import html, dash_table



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