from flask import Flask, render_template, url_for
from klimaatbestendige_netwerken.pyBIVAS_plot import pyBIVAS_plot as pyBIVAS
from pathlib import Path

app = Flask(__name__)

database = Path(r'D:\software\BIVAS\BIVAS_4.8.1\Bivas.db')

BIVAS = pyBIVAS(databasefile=database)
BIVAS.set_scenario()

countingpoints = BIVAS.countingpoint_list()

@app.route('/')
def index():
    return render_template('index.html', countingpoints=countingpoints)

if __name__ == '__main__':
    app.run(debug=True)
