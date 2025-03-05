import dash
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Output, Input
from flask import session
from flask_session import Session

# Inicializa o app Dash
app = Dash(
    __name__,
    use_pages=True,
    title="Box Dashboard e Previsão de Vendas",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)

# Configuração do Flask para gerenciar sessões
server = app.server
server.config["SECRET_KEY"] = "minha_chave_secreta"
server.config["SESSION_TYPE"] = "filesystem"
Session(server)

# Sidebar dinâmica (exibida apenas se o usuário estiver autenticado)
def get_sidebar():
    return html.Div(
        [
            dbc.Row(
                [
                    html.Img(
                        src="assets/logo/boxmayorista.svg", style={"height": "148px"}
                    )
                ],
                className="sidebar-logo",
            ),
            html.Hr(),
            dbc.Nav(
                [
                    dbc.NavLink("Dashboard", href="/dashboard", active="exact"),
                    dbc.NavLink("Previsão de Vendas", href="/predict_sales", active="exact"),
                    html.Div(id="logout-section"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        className="sidebar",
    )


# Layout principal
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh=True),
        html.Div(id="sidebar-container", style={"display": "none"}),  # Inicialmente oculto
        html.Div(id="content", style={"flex": "1"}),  # Ocupa o espaço restante
    ],
    id="main-container",  # Adiciona um ID ao container principal
    style={"display": "flex", "height": "100vh"},  # Layout flexível com altura total da tela
)


# Callback para ajustar o estilo do body com base na rota
@app.callback(
    Output("main-container", "style"),  # Atualiza o estilo do container principal
    Input("url", "pathname"),
)
def update_body_style(pathname):
    """Ajusta o estilo do body com base na rota atual"""
    if pathname == "/login":
        return {"display": "flex", "height": "100vh", "margin": "0"}  # Margin 0 para /login
    else:
        return {"display": "flex", "height": "100vh", "marginLeft": "16.3rem", "marginRight": "8px", "marginTop": "2rem"}  # Margin padrão para outras rotas


# Callback para atualizar a sidebar conforme o login/logout
@app.callback(
    Output("sidebar-container", "children"),
    Output("sidebar-container", "style"),  # Adiciona um Output para o estilo
    [Input("url", "pathname")]
)
def update_sidebar(pathname):
    """Atualiza a sidebar apenas se o usuário estiver logado e não estiver na página de login"""
    if pathname == "/login":
        return None, {"display": "none"}  # Oculta o sidebar-container

    if session.get("logged_in"):
        return get_sidebar(), {"display": "block"}  # Exibe o sidebar-container

    return None, {"display": "none"}  # Oculta o sidebar-container se não estiver logado


# Callback para exibir o botão de logout dinamicamente
@app.callback(
    Output("logout-section", "children"),
    [Input("sidebar-container", "children")]
)
def show_logout_button(_):
    if session.get("logged_in"):
        return dbc.Button("Logout", href="/logout", color="danger", className="mt-3")
    return ""


# Callback para renderizar as páginas e gerenciar logout
@app.callback(
    Output("content", "children"),
    Output("url", "pathname"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def render_page(pathname):
    if pathname == "/logout":
        session.clear()
        return dash.page_registry["pages.login"]["layout"], "/login"

    if not session.get("logged_in") and pathname != "/login":
        return dash.page_registry["pages.login"]["layout"], "/login"

    return dash.page_container, pathname


if __name__ == "__main__":
    app.run_server(debug=True)