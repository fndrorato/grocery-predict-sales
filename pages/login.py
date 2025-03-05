from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
from flask import session
import dash

# Registrar a página de login
dash.register_page(__name__, path="/login", title="Login")

# Layout da página de Login
layout = html.Div(
    [
        dbc.Row(
            [
                html.Img(
                    src="assets/logo/boxmayorista.svg", style={"height": "124px", "marginBottom": "1rem"}
                )
            ],
            className="sidebar-logo",
        ),
        dbc.Input(id="username", placeholder="Usuário", type="text", className="mb-2", style={"width": "250px"}),
        dbc.Input(id="password", placeholder="Senha", type="password", className="mb-2", style={"width": "250px"}),
        dbc.Button("Entrar", id="login-button", color="primary", className="mb-2"),
        html.Div(id="login-output", className="text-danger"),
        dcc.Location(id="redirect", refresh=True),
        dcc.Store(id="enter-key", data=None),  # Captura o evento de tecla pressionada
    ],
    className="d-flex flex-column align-items-center justify-content-center vh-100",
    style={"backgroundColor": "#1f3990", "color": "white", "width": "100%"},  # Ocupa 100% da largura
)

# Lista de usuários válidos
USERS = {"admin": "1234", "user": "senha"}

# Callback para capturar o evento de tecla pressionada
@callback(
    Output("enter-key", "data"),
    Input("username", "n_submit"),
    Input("password", "n_submit"),
    prevent_initial_call=True,
)
def capture_enter(username_submit, password_submit):
    return True  # Retorna True quando Enter é pressionado

# Callback para autenticação
@callback(
    Output("login-output", "children"),
    Output("redirect", "pathname"),
    Input("login-button", "n_clicks"),
    Input("enter-key", "data"),  # Adiciona o evento de tecla como entrada
    State("username", "value"),
    State("password", "value"),
    prevent_initial_call=True,
)
def login(n_clicks, enter_key, username, password):
    if username in USERS and USERS[username] == password:
        session["logged_in"] = True
        return "", "/dashboard"
    return "Usuário ou senha incorretos.", "/login"