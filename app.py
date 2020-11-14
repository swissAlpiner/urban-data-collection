import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html

from sqlalchemy import create_engine
import pandas as pd

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

# build the app
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label='Sensor Data', children=[
            html.H3('Sensor Data')
        ]),
        dcc.Tab(label='Sensor Locations', children=[
            html.H3('Sensor Locations')
        ]),
        dcc.Tab(label='Sandbox', children=[
            html.Div(id='tabs-content'),
            html.H2('Hello World'),
            dcc.Dropdown(
                id='dropdown',
                options=[{'label': i, 'value': i} for i in ['LA', 'NYC', 'MTL']],
                value='LA'
            ),
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

@app.callback(dash.dependencies.Output('display-value', 'children'),
              [dash.dependencies.Input('dropdown', 'value')])
def display_value(value):
    return 'You have selected "{}"'.format(value)


if __name__ == '__main__':
    app.run_server(debug=True)
