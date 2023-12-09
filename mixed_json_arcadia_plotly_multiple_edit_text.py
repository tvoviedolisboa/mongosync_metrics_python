import plotly.graph_objects as go
import plotly.subplots as sp
from plotly.io import write_image
from plotly.utils import PlotlyJSONEncoder
from plotly.subplots import make_subplots

from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory
import json
from datetime import datetime
import io
import base64
from werkzeug.utils import secure_filename
import matplotlib.pyplot as plt
import os

# Create a Flask app
app = Flask(__name__)

@app.route('/')
def upload_form():
    # Return a simple file upload form
    return render_template_string('''
        <form method="post" action="/upload" enctype="multipart/form-data">
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return redirect(request.url)

    if file:
        # Read the file and convert it to a list of lines
        lines = list(file)

        # Load lines with 'message' == "Replication progress."
        data = [json.loads(line) for line in lines if json.loads(line).get('message') == "Replication progress."]

        # Load lines with 'message' == "Version info"
        version_info_list = [json.loads(line) for line in lines if json.loads(line).get('message') == "Version info"]

        # Load lines with 'message' == "Mongosync Options"
        mongosync_opts_list = [json.loads(line) for line in lines if json.loads(line).get('message') == "Mongosync Options"]

        # Load lines with 'message' == "Operation duration stats."
        mongosync_ops_stats = [json.loads(line) for line in lines if json.loads(line).get('message') == "Operation duration stats."]

        # Create a string with all the Mongosync Options information
        mongosync_opts_text = "\n".join([json.dumps(item, indent=4) for item in mongosync_opts_list])

        # Create a string with all the version information
        version_text = "\n".join([f"MongoSync Version: {item.get('version')}, OS: {item.get('os')}, Arch: {item.get('arch')}" for item in version_info_list])

        # Extract the keys from the first dictionary in mongosync_opts_list
        keys = list(mongosync_opts_list[0].keys())

        # For each key, extract the corresponding values from all dictionaries in mongosync_opts_list
        values = [[item[key] for item in mongosync_opts_list] for key in keys]

        # If the key is 'hiddenFlags', extract its keys and values and add them to the keys and values lists
        for i, key in enumerate(keys):
            if key == 'hiddenFlags':
                hidden_keys = list(values[i][0].keys())
                hidden_values = [[item.get(key, '') for item in values[i]] for key in hidden_keys]
                keys = keys[:i] + hidden_keys + keys[i+1:]
                values = values[:i] + hidden_values + values[i+1:]
                break

        # Create a table trace with the keys as the first column and the corresponding values as the second column
        table_trace = go.Table(
            header=dict(values=['Key', 'Value'], font=dict(size=12, color='black')),
            cells=dict(values=[keys, values], font=dict(size=10, color='darkblue')),
            columnwidth=[0.75, 2.5]  # Adjust the column widths as needed
        )

        # Extract the data you want to plot
        times = [datetime.strptime(item['time'][:26], "%Y-%m-%dT%H:%M:%S.%f") for item in data if 'time' in item]
        totalEventsApplied = [item['totalEventsApplied'] for item in data if 'totalEventsApplied' in item]
        lagTimeSeconds = [item['lagTimeSeconds'] for item in data if 'lagTimeSeconds' in item]

        # Create a subplot for the scatter plots and a separate subplot for the table
        fig = make_subplots(rows=4, cols=1, subplot_titles=("Total Events Applied", "Lag Time Seconds", "MongoSync Options"), specs=[[{}], [{}], [{"type": "table"}], [{}]])

        # Add the version information as an annotation to the plot
        fig.add_annotation( x=0.5, y=1.05, xref="paper", yref="paper", text=version_text, showarrow=False, font=dict(size=12))

        # Add the table trace to the figure
        fig.add_trace(table_trace, row=3, col=1)

        # Add traces
        fig.add_trace(go.Scatter(x=times, y=totalEventsApplied, mode='lines', name='Total Events Applied'), row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=lagTimeSeconds, mode='lines', name='Lag Time Seconds'), row=2, col=1)
        


        # Extract the data you want to plot
        times = [datetime.strptime(item['time'][:26], "%Y-%m-%dT%H:%M:%S.%f") for item in data if 'time' in item]
        totalEventsApplied = [item['totalEventsApplied'] for item in data if 'totalEventsApplied' in item]
        lagTimeSeconds = [item['lagTimeSeconds'] for item in data if 'lagTimeSeconds' in item]
        CollectionCopySourceRead = [float(item['CollectionCopySourceRead']['averageDurationMs']) for item in mongosync_ops_stats if 'CollectionCopySourceRead' in item and 'averageDurationMs' in item['CollectionCopySourceRead']]
        CollectionCopyDestinationWrite = [float(item['CollectionCopyDestinationWrite']['averageDurationMs']) for item in mongosync_ops_stats if 'CollectionCopyDestinationWrite' in item and 'averageDurationMs' in item['CollectionCopyDestinationWrite']]
        CEASourceRead = [float(item['CEASourceRead']['averageDurationMs']) for item in mongosync_ops_stats if 'CEASourceRead' in item and 'averageDurationMs' in item['CEASourceRead']]
        CEASourceRead_maximum  = [float(item['CEASourceRead']['maximumDurationMs']) for item in mongosync_ops_stats if 'CEASourceRead' in item and 'maximumDurationMs' in item['CEASourceRead']]
        CEASourceRead_numOperations = [float(item['CEASourceRead']['numOperations']) for item in mongosync_ops_stats if 'CEASourceRead' in item and 'numOperations' in item['CEASourceRead']]
        CEADestinationWrite = [float(item['CEADestinationWrite']['averageDurationMs']) for item in mongosync_ops_stats if 'CEADestinationWrite' in item and 'averageDurationMs' in item['CEADestinationWrite']]
        CEADestinationWrite_maximum = [float(item['CEADestinationWrite']['maximumDurationMs']) for item in mongosync_ops_stats if 'CEADestinationWrite' in item and 'maximumDurationMs' in item['CEADestinationWrite']]    
        CEADestinationWrite_numOperations = [float(item['CEADestinationWrite']['numOperations']) for item in mongosync_ops_stats if 'CEADestinationWrite' in item and 'numOperations' in item['CEADestinationWrite']] 

        # Create a subplot for the scatter plots and a separate subplot for the table
        fig = make_subplots(rows=6, cols=1, subplot_titles=("Total Events Applied", "Collection Copy Source Read", "Collection Copy Destination Write", "CEA Source Read", "CEA Destination Write", "MongoSync Options"), specs=[[{}], [{}], [{}], [{}],[{}],[{"type": "table"}]])

        # Add the version information as an annotation to the plot
        fig.add_annotation( x=0.5, y=1.05, xref="paper", yref="paper", text=version_text, showarrow=False, font=dict(size=12))

        # Add the table trace to the figure
        fig.add_trace(table_trace, row=6, col=1)

        # Add traces
        fig.add_trace(go.Scatter(x=times, y=totalEventsApplied, mode='lines', name='Total Events Applied'), row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=lagTimeSeconds, mode='lines', name='Lag Time Seconds'), row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=CollectionCopySourceRead, mode='lines', name='Collection Copy Source Read'), row=2, col=1)
        fig.add_trace(go.Scatter(x=times, y=CollectionCopyDestinationWrite, mode='lines', name='Collection Copy Destination Write'), row=3, col=1)
        fig.add_trace(go.Scatter(x=times, y=CEASourceRead, mode='lines', name='CEA Source'), row=4, col=1)
        fig.add_trace(go.Scatter(x=times, y=CEASourceRead_maximum, mode='lines', name='CEA Source Read Maximum'), row=4, col=1)
        fig.add_trace(go.Scatter(x=times, y=CEASourceRead_numOperations, mode='lines', name='CEA Source Read Number of Operations'), row=4, col=1)
        fig.add_trace(go.Scatter(x=times, y=CEADestinationWrite, mode='lines', name='CEADestinationWrite'), row=5, col=1)
        fig.add_trace(go.Scatter(x=times, y=CEADestinationWrite_maximum, mode='lines', name='CEA Destination Write Maximum'), row=5, col=1)
        fig.add_trace(go.Scatter(x=times, y=CEADestinationWrite_numOperations, mode='lines', name='CEA Destination Write Number of Operations'), row=5, col=1)


        # Update layout
        fig.update_layout(height=1800, width=1250, title_text="Replication Progress")

        # Convert the figure to JSON
        plot_json = json.dumps(fig, cls=PlotlyJSONEncoder)

        # Render the plot in the browser
        return render_template_string('''
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <div id="plot"></div>
            <script>
            var plot = {{ plot_json | safe }};
            Plotly.newPlot('plot', plot.data, plot.layout);
            </script>
        ''', plot_json=plot_json)
    
@app.route('/plot')
def serve_plot():
    file_path = os.path.join(app.static_folder, 'plot.png')
    print(file_path)  # print the file path

    if os.path.exists(file_path):
        return send_from_directory(app.static_folder, 'plot.png')
    else:
        return "File not found", 404

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=3030)