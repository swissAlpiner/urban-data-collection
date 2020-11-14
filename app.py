import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html

from sqlalchemy import create_engine
import pandas as pd
import plotly.graph_objects as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

# get our traffic data
USER = "admin"
PW = "KatzeGurkeSessel"
DBNAME = "urban_data"
PORT = "3306"
REGION = "eu-central-1"
ENDPOINT = "smart-city-lab-2020.cuvz2t3c3rzu.eu-central-1.rds.amazonaws.com"

sql_engine = create_engine('mysql+pymysql://' + USER + ':' + PW + '@' + ENDPOINT + ':' + PORT + '/' + DBNAME)
dbConnection = sql_engine.connect()

df_sensor_data = pd.read_sql("select * from sensor_data", dbConnection);
df_sensor_locations = pd.read_sql("select * from sensor_locations", dbConnection);

pd.set_option('display.expand_frame_repr', False)

# mapbox
mapbox_access_token = open(".mapbox_token").read()
map_locations = go.Figure(go.Scattermapbox(
    lat=df_sensor_locations['lat'],
    lon=df_sensor_locations['lng'],
    mode='markers',
    marker=go.scattermapbox.Marker(
        size=9
    ),
    text=df_sensor_locations['name'],
))

map_locations.update_layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=47.3890,
            lon=8.1758
        ),
        pitch=0,
        zoom=13
    ),
)

# build the app
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Sensor Data', children=[
            html.H3('Sensor Data'),
            html.H4('Choose sensor'),
            dcc.Dropdown(
                id='dropdown_location',
                options=[{'label': row['name'] + ' (ID: ' + str(row['id']) + ')', 'value': row['id']} for index, row in
                         df_sensor_locations.iterrows()]
            ),
            dcc.RadioItems(
                id='bin',
                options=[{'label': i, 'value': i} for i in [
                    'Yearly', 'Seasonally', 'Monthly', 'Weekly'
                ]],
                value='Yearly',
                labelStyle={'display': 'inline'}
            ),
            html.Div([
                html.Div(
                    className='six columns',
                    children=dcc.Graph(id='cars-over-time')
                ),
                html.Div(
                    className='six columns',
                    children=dcc.Graph(id='map', animate=True)
                )
            ]),
            html.Div([
                html.Iframe(id='datatable', height=500, width=1200)
            ]),
        ]),
        dcc.Tab(label='Sensor Locations', children=[
            html.H3('Sensor Locations'),
            dcc.Graph(figure=map_locations)
        ]),
        dcc.Tab(label='Sandbox', children=[
            html.Div(id='tabs-content'),
            html.Div(id='display-value'),
            html.H2('Raw sensor data'),
            dash_table.DataTable(
                id='sensor_data',
                columns=[{"name": i, "id": i} for i in df_sensor_data.columns],
                data=df_sensor_data.to_dict('records'),
            ),
            html.H2('Raw sensor locations'),
            dash_table.DataTable(
                id='sensor_locations',
                columns=[{"name": i, "id": i} for i in df_sensor_locations.columns],
                data=df_sensor_locations.to_dict('records'),
            )
        ]),
    ]),
])


# bar char callback
@app.callback(
    dash.dependencies.Output('cars-over-time', 'figure'),
    [dash.dependencies.Input('bin', 'value'),
     dash.dependencies.Input('dropdown_location', 'value')])
def display_cars_over_time(bin, dropdown_location):
    df = df_sensor_data
    if dropdown_location:
        df = df_sensor_data[df_sensor_data['sensor_locations_id'] == dropdown_location]
    return {
        'data': [
            {
                'x': df['observing_datetime'],
                'customdata': df['sensor_locations_id'],
                'name': 'Open Date',
                'type': 'histogram',
                'autobinx': False,
                'xbins': {
                    'start': '2020-01-01',
                    'end': '2020-12-31',
                    'size': (
                        'M12' if bin == 'Yearly' else
                        'M3' if bin == 'Seasonally' else
                        'M1' if bin == 'Monthly' else
                        1000 * 60 * 60 * 24 * 7  # Weekly
                    )
                }
            }
        ],
        'layout': {
            'margin': {'l': 40, 'r': 20, 't': 0, 'b': 30}
        }
    }


# map callback
@app.callback(
    dash.dependencies.Output('map', 'figure'),
    [dash.dependencies.Input('cars-over-time', 'selectedData'),
     dash.dependencies.Input('dropdown_location', 'value')])
def display_map(selected_points, dropdown_location):
    df = df_sensor_locations
    if dropdown_location:
        df = df_sensor_locations[df_sensor_locations['id'] == dropdown_location]
    selected_indices = []
    if selected_points:
        for bin in selected_points['points']:
            selected_indices += bin['pointNumbers']
    return {
        'data': [{
            'lat': df['lat'],
            'lon': df['lng'],
            'type': 'scattermapbox',
            'selectedpoints': selected_indices,
            'selected': {
                'marker': {'color': '#85144b'}
            },
            'text': df['name']
        }],
        'layout': {
            'mapbox': {
                'center': {
                    'lat': 47.3890,
                    'lon': 8.1758
                },
                'zoom': 13,
                'accesstoken': mapbox_access_token
            },
            'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0}
        }
    }


# sensor data debug callback
@app.callback(
    dash.dependencies.Output('datatable', 'srcDoc'),
    [dash.dependencies.Input('cars-over-time', 'selectedData'),
     dash.dependencies.Input('dropdown_location', 'value')])
def display_sensor_data_debug(selected_points, dropdown_location):
    df_sensor = df_sensor_data
    df_locations = df_sensor_locations
    if dropdown_location:
        df_sensor = df_sensor_data[df_sensor_data['sensor_locations_id'] == dropdown_location]
        df_locations = df_sensor_locations[df_sensor_locations['id'] == dropdown_location]
    return df_sensor.to_html()


if __name__ == '__main__':
    app.run_server(debug=True)
