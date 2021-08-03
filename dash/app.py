# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
import plotly.express as px
import plotly.graph_objects as go 
import dash_daq as daq
from dash.dependencies import Input, Output, State


from flask import Flask, request

import os
import urllib.parse

import pandas as pd
import requests
import glob

import pymzml
import numpy as np
from tqdm import tqdm
import urllib
import json

from flask_caching import Cache
import tasks
import msql_parser
import msql_visualizer
import msql_translator

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'GNPS - Template'

cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'temp/flask-cache',
    'CACHE_DEFAULT_TIMEOUT': 0,
    'CACHE_THRESHOLD': 10000
})

server = app.server

NAVBAR = dbc.Navbar(
    children=[
        dbc.NavbarBrand(
            html.Img(src="https://gnps-cytoscape.ucsd.edu/static/img/GNPS_logo.png", width="120px"),
            href="https://gnps.ucsd.edu"
        ),
        dbc.Nav(
            [
                dbc.NavItem(dbc.NavLink("GNPS - MSQL Dashboard - Version 0.2", href="#")),
                dbc.NavItem(dbc.NavLink("Documentation", href="https://mwang87.github.io/MassQueryLanguage_Documentation/")),
            ],
        navbar=True)
    ],
    color="light",
    dark=False,
    sticky="top",
)

DATASELECTION_CARD = [
    dbc.CardHeader(html.H5("Data Selection")),
    dbc.CardBody(
        [   
            html.H5(children='Query Sandbox'),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Query", addon_type="prepend"),
                    dbc.Textarea(id='query', placeholder="Enter Query", value="", rows="4"),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Filename", addon_type="prepend"),
                    dbc.Select(
                        id="filename",
                        options=[],
                        value="GNPS00002_A3_p.mzML"
                    )
                ],
                className="mb-3",
            ),
            html.H5(children='Plotting Options'),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("x_axis", addon_type="prepend"),
                    dbc.Input(id='x_axis', placeholder="Enter Query", value=""),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("y_axis", addon_type="prepend"),
                    dbc.Input(id='y_axis', placeholder="Enter Query", value=""),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("facet_column", addon_type="prepend"),
                    dbc.Input(id='facet_column', placeholder="Enter Facet", value=""),
                ],
                className="mb-3",
            ),
            html.Br(),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("scan", addon_type="prepend"),
                    dbc.Input(id='scan', placeholder="Enter Scan", value=""),
                ],
                className="mb-3",
            ),
            html.Br(),
            dbc.Button("Copy Link", block=True, color="info", id="copy_link_button", n_clicks=0),
            html.Hr(),
            html.H5("Parse Viz Options"),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("x_value", addon_type="prepend"),
                    dbc.Input(id='x_value', placeholder="Enter X m/z Value", value="500"),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("y_value", addon_type="prepend"),
                    dbc.Input(id='y_value', placeholder="Enter Y Intensity Value", value="1"),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("ms1_usi", addon_type="prepend"),
                    dbc.Input(id='ms1_usi', placeholder="Enter MS1 USI", value=""),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("ms2_usi", addon_type="prepend"),
                    dbc.Input(id='ms2_usi', placeholder="Enter MS2 USI", value=""),
                ],
                className="mb-3",
            ),
            html.Hr(),
            html.H5(children='Query Parse Visualization'),
            dcc.Loading(
                id="output_parse_drawing",
                children=[html.Div([html.Div(id="loading-output-21")])],
                type="default",
            ),
            html.Br(),
            html.Hr(),
            dcc.Loading(
                id="output_parse",
                children=[html.Div([html.Div(id="loading-output-872")])],
                type="default",
            ),
        ]
    )
]

LEFT_DASHBOARD = [
    html.Div(
        [
            html.Div(DATASELECTION_CARD),
        ]
    )
]

MIDDLE_DASHBOARD = [
    dbc.CardHeader(html.H5("Data Exploration")),
    dbc.CardBody(
        [
            dcc.Loading(
                id="output",
                children=[html.Div([html.Div(id="loading-output-23")])],
                type="default",
            ),
            html.Br(),
            html.Br(),
            dcc.Loading(
                id="spectrumplot",
                children=[html.Div([html.Div(id="loading-output-298")])],
                type="default",
            ),
            html.Br(),
            dcc.Loading(
                id="plotting",
                children=[html.Div([html.Div(id="loading-output-26")])],
                type="default",
            ),
        ]
    )
]

CONTRIBUTORS_DASHBOARD = [
    dbc.CardHeader(html.H5("Contributors")),
    dbc.CardBody(
        [
            "Mingxun Wang PhD - UC San Diego",
            html.Br(),
            html.Br(),
            html.H5("Citation"),
            html.A('Mingxun Wang, Jeremy J. Carver, Vanessa V. Phelan, Laura M. Sanchez, Neha Garg, Yao Peng, Don Duy Nguyen et al. "Sharing and community curation of mass spectrometry data with Global Natural Products Social Molecular Networking." Nature biotechnology 34, no. 8 (2016): 828. PMID: 27504778', 
                    href="https://www.nature.com/articles/nbt.3597")
        ]
    )
]

EXAMPLES_DASHBOARD = [
    dbc.CardHeader(html.H5("Examples")),
    dbc.CardBody(
        [
            html.A('Get all MS2 scans in file', 
                    href="/?query=QUERY scaninfo(MS2DATA)"),
            html.Br(),
            html.A('Get TIC of MS1 in file', 
                    href="/?query=QUERY scansum(MS1DATA)&x_axis=rt&y_axis=i"),
            html.Br(),
            html.A('Get XIC of MS1 in file', 
                    href="/?query=QUERY scansum(MS1DATA) FILTER MS1MZ=100:TOLERANCEMZ=0.1&x_axis=rt&y_axis=i"),
            html.Br(),
            html.A('Get MS2 peaks where a product ion is present', 
                    href="/?query=QUERY MS2DATA WHERE MS2PROD=226.18"),
            html.Br(),
            html.A('Get MS2 info where a product ion is present', 
                    href="/?query=QUERY scaninfo(MS2DATA) WHERE MS2PROD=167.0857:TOLERANCEPPM=5"),
            html.Br(),
            html.A('Get MS2 info where a product ion and neutral loss is present', 
                    href="/?query=QUERY scaninfo(MS2DATA) WHERE MS2NL=176.0321 AND MS2PROD=85.02915"),
            html.Br(),
            html.A('Get MS1 peaks where a MS2 with product ion is present', 
                    href="/?query=QUERY MS1DATA WHERE MS2PROD=226.18"),
            html.Br(),
            html.A('Sub Query', 
                    href="/?query=QUERY scanrangesum(MS1DATA, TOLERANCE=0.1) WHERE MS1MZ=(QUERY scanmz(MS2DATA) WHERE MS2NL=176.0321 AND MS2PROD=85.02915)")
        ]
    )
]

BODY = dbc.Container(
    [
        dcc.Location(id='url', refresh=False),
        html.Div(
            [
                dcc.Link(id="query_link", href="#", target="_blank"),
            ],
            style="display:none"
        ),
        dbc.Row([
            dbc.Col(
                dbc.Card(LEFT_DASHBOARD),
                className="col-6"
            ),
            dbc.Col(
                [
                    dbc.Card(MIDDLE_DASHBOARD),
                    html.Br(),
                    dbc.Card(CONTRIBUTORS_DASHBOARD),
                    html.Br(),
                    dbc.Card(EXAMPLES_DASHBOARD)
                ],
                className="col-6"
            ),
        ], style={"marginTop": 30}),
        
    ],
    fluid=True,
    className="",
)

app.layout = html.Div(children=[NAVBAR, BODY])

def _get_url_param(param_dict, key, default):
    return param_dict.get(key, [default])[0]

@app.callback([
                Output('query', 'value'),
                Output('filename', 'value'),
                Output('x_axis', 'value'),
                Output('y_axis', 'value'),
                Output('facet_column', 'value'),
                Output('scan', 'value'),
                Output('x_value', 'value'),
                Output('y_value', 'value'),
                Output('ms1_usi', 'value'),
                Output('ms2_usi', 'value'),
              ],
              [
                  Input('url', 'search')
              ])
def determine_params(search):
    try:
        query_dict = urllib.parse.parse_qs(search[1:])
    except:
        query_dict = {}

    query = _get_url_param(query_dict, "query", 'QUERY scaninfo(MS2DATA) WHERE MS2PROD=226.18:TOLERANCEPPM=5')
    filename = _get_url_param(query_dict, "filename", dash.no_update)
    x_axis = _get_url_param(query_dict, "x_axis", dash.no_update)
    y_axis = _get_url_param(query_dict, "y_axis", dash.no_update)
    facet_column = _get_url_param(query_dict, "facet_column", dash.no_update)
    scan = _get_url_param(query_dict, "scan", dash.no_update)
    x_value = _get_url_param(query_dict, "x_value", dash.no_update)
    y_value = _get_url_param(query_dict, "y_value", dash.no_update)
    ms1_usi = _get_url_param(query_dict, "ms1_usi", dash.no_update)
    ms2_usi = _get_url_param(query_dict, "ms2_usi", dash.no_update)

    return [query, filename, x_axis, y_axis, facet_column, scan, x_value, y_value, ms1_usi, ms2_usi]

@app.callback([
                Output('filename', 'options'),
              ],
              [
                  Input('url', 'search')
              ])
def determine_files(search):
    file_list = glob.glob("./test/*.mzML")
    file_list += glob.glob("./test/*.json")
    file_list += glob.glob("./test/*.mgf")
    file_list = [os.path.basename(filename) for filename in file_list]
    file_list = [{"label": filename, "value": filename} for filename in file_list]

    return [file_list]

def _render_parse(query):
    response_list = []

    try:
        parse_results = msql_parser.parse_msql(query)
    except:
        return ["Parse Error"]

    parse_markdown = dcc.Markdown(
        '''
```json
{}
```
'''.format(json.dumps(parse_results, indent=4)))

    # Creating written description that is translated
    try:
        translation = msql_translator.translate_query(query)
    except:
        translation = "Translation Error"
    
    return [html.Pre(query), html.Hr(), html.Pre(translation), html.Hr(), parse_markdown, html.Hr()]

@app.callback([
                Output('output_parse', 'children'),
              ],
              [
                  Input('query', 'value')
            ])
def draw_parse(query):
    all_queries = query.split("|||")

    # Let's parse first
    merged_list = []
    for split_query in all_queries:
        parse_render_list = _render_parse(split_query)
        merged_list += parse_render_list
    
    return [merged_list]


def _render_parse_visualizations(query, x_value, y_value, ms1_peaks, ms2_peaks):
    try:
        ms1_fig, ms2_fig = msql_visualizer.visualize_query(query, 
                                                            variable_x=float(x_value), 
                                                            variable_y=float(y_value),
                                                            ms1_peaks=ms1_peaks,
                                                            ms2_peaks=ms2_peaks)
    except:
        ["Parse Error"]

    ms1_graph = dcc.Graph(figure=ms1_fig)
    ms2_graph = dcc.Graph(figure=ms2_fig)

    return [ms1_graph, ms2_graph]

    

@app.callback([
                Output('output_parse_drawing', 'children'),
              ],
              [
                  Input('query', 'value'),
                  Input('x_value', 'value'),
                  Input('y_value', 'value'),
                  Input('ms1_usi', 'value'),
                  Input('ms2_usi', 'value'),
            ])
def draw_parse_drawing(query, x_value, y_value, ms1_usi, ms2_usi):
    # Getting the peaks
    ms1_peaks = None
    ms2_peaks = None

    try:
        r = requests.get("https://metabolomics-usi.ucsd.edu/json/?usi1={}".format(ms1_usi))
        ms1_peaks = r.json()["peaks"]
    except:
        pass

    try:
        r = requests.get("https://metabolomics-usi.ucsd.edu/json/?usi1={}".format(ms2_usi))
        ms2_peaks = r.json()["peaks"]
    except:
        pass

    all_queries = query.split("|||")

    # Let's parse first
    merged_list = []
    for split_query in all_queries:
        parse_render_list = _render_parse_visualizations(split_query, x_value, y_value, ms1_peaks, ms2_peaks)
        merged_list += parse_render_list
        
    return [merged_list]

@app.callback([
                Output('output', 'children'),
              ],
              [
                  Input('query', 'value'),
                  Input('filename', 'value')
            ])
def draw_output(query, filename):
    parse_results = msql_parser.parse_msql(query)

    full_filepath = os.path.join("test", filename)
    results_list = tasks.task_executequery.delay(query, full_filepath)
    results_list = results_list.get()

    if len(results_list) == 0:
        return ["No Matches"]

    # Doing enrichment if possible

    table = dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in results_list[0].keys()],
        data=results_list,
        page_size=10,
        sort_action='native',
        filter_action='native',
        export_format='csv'
    )

    return [table]


@app.callback([
                Output('plotting', 'children'),
              ],
              [
                  Input('query', 'value'),
                  Input('filename', 'value'),
                  Input('x_axis', 'value'),
                  Input('y_axis', 'value'),
                  Input('facet_column', 'value')
            ])
def draw_plot(query, filename, x_axis, y_axis, facet_column):
    try:
        parse_results = msql_parser.parse_msql(query)
    except:
        return ["Parse Error"]

    full_filepath = os.path.join("test", filename)
    results_list = tasks.task_executequery.delay(query, full_filepath)
    results_list = results_list.get()

    results_df = pd.DataFrame(results_list)

    try:
        fig = px.scatter(results_df, x=x_axis, y=y_axis, facet_row=facet_column)
    except:
        fig = px.scatter(results_df, x=x_axis, y=y_axis)

    return [dcc.Graph(figure=fig)]


@app.callback([
                Output('spectrumplot', 'children'),
              ],
              [
                  Input('filename', 'value'),
                  Input('scan', 'value'),
            ])
def draw_spectrum(filename, scan):
    full_filepath = os.path.join("test", filename)

    if not ".mzML" in full_filepath:
        return

    MS_precisions = {
        1: 5e-6,
        2: 20e-6,
        3: 20e-6,
        4: 20e-6,
        5: 20e-6,
        6: 20e-6,
        7: 20e-6,
    }

    
    run = pymzml.run.Reader(full_filepath, MS_precisions=MS_precisions)

    try:
        spectrum = run[int(scan)]
    except:
        spectrum = run[str(scan)]
    peaks = spectrum.peaks("raw")

    # Drawing the spectrum object
    mzs = [peak[0] for peak in peaks]
    ints = [peak[1] for peak in peaks]
    neg_ints = [intensity * -1 for intensity in ints]

    interactive_fig = go.Figure(
        data=go.Scatter(x=mzs, y=ints, 
            mode='markers+text',
            marker=dict(size=0.00001),
            error_y=dict(
                symmetric=False,
                arrayminus=[0]*len(neg_ints),
                array=neg_ints,
                width=0
            ),
            hoverinfo="x",
            textposition="top right",
        )
    )

    interactive_fig.update_layout(title='{}'.format(scan))
    interactive_fig.update_xaxes(title_text='m/z')
    interactive_fig.update_yaxes(title_text='intensity')
    interactive_fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
    interactive_fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
    interactive_fig.update_yaxes(range=[0, max(ints) * 1.2])

    return [dcc.Graph(figure=interactive_fig)]


### Rendering URL
@app.callback([
                Output('query_link', 'href'),
              ],
                [
                    Input('query', 'value'),
                    Input('filename', 'value'),
                    Input('x_axis', 'value'),
                    Input('y_axis', 'value'),
                    Input('facet_column', 'value'),
                    Input('scan', 'value'),
                    Input('x_value', 'value'),
                    Input('y_value', 'value'),
                    Input('ms1_usi', 'value'),
                    Input('ms2_usi', 'value'),
                ])
def draw_url(query, filename, x_axis, y_axis, facet_column, scan, x_value, y_value, ms1_usi, ms2_usi):
    params = {}
    params["query"] = query
    params["filename"] = filename
    params["x_axis"] = x_axis
    params["y_axis"] = y_axis
    params["facet_column"] = facet_column
    params["scan"] = scan
    params["x_value"] = x_value
    params["y_value"] = y_value
    params["ms1_usi"] = ms1_usi
    params["ms2_usi"] = ms2_usi

    url_params = urllib.parse.urlencode(params)

    return [request.host_url + "/?" + url_params]

app.clientside_callback(
    """
    function(n_clicks, text_to_copy) {
        original_text = "Copy Link"
        if (n_clicks > 0) {
            const el = document.createElement('textarea');
            el.value = text_to_copy;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            setTimeout(function(){ 
                    document.getElementById("copy_link_button").textContent = original_text
                }, 1000);
            document.getElementById("copy_link_button").textContent = "Copied!"
            return 'Copied!';
        } else {
            document.getElementById("copy_link_button").textContent = original_text
            return original_text;
        }
    }
    """,
    Output('copy_link_button', 'children'),
    [
        Input('copy_link_button', 'n_clicks')
    ],
    [
        State('query_link', 'href'),
    ]
)

# API
@server.route("/api")
def api():
    version_dict = {}
    version_dict["version"] = 1.0
    return json.dumps(version_dict)

@server.route("/parse")
def parse_api():
    query = request.args.get("query")

    try:
        parse_results = msql_parser.parse_msql(query)
    except:
        return ["Parse Error"]

    return json.dumps(parse_results)



if __name__ == "__main__":
    app.run_server(debug=True, port=5000, host="0.0.0.0")
