from flask import Flask, render_template, url_for, request
from klimaatbestendige_netwerken.pyBIVAS_plot import pyBIVAS_plot as pyBIVAS
from pathlib import Path
import plotly
import plotly.graph_objs as go
import plotly.express as px
import json

app = Flask(__name__)

database = Path(r'..\tests\resources\Bivas_2018_v3.db')

BIVAS = pyBIVAS(databasefile=database)
BIVAS.set_scenario()

countingpoints = BIVAS.countingpoint_list()

@app.route('/')
def index():

    fig = None
    return render_template('index.html', countingpoints=countingpoints['Name'], plot=fig)

@app.route('/update_graph', methods=['GET', 'POST'])
def change_features():
    df = BIVAS.countingpoint_timeseries(request.args['selected'])
    fig = create_plot(df)
    return fig


def create_plot(df):

    df_prep = df.copy()
    df_prep = df_prep.sum(axis=1)
    df_prep = df_prep.reset_index()
    df_prep.columns = ['Days', 'Vaarbewegingen']

    graph = px.line(df_prep, x='Days', y='Vaarbewegingen')
    graphJSON = json.dumps(graph, cls=plotly.utils.PlotlyJSONEncoder)

    return graphJSON

if __name__ == '__main__':
    app.run(debug=True)
