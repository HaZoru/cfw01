from flask import Flask, request, render_template
import pandas as pd
import json


app = Flask(__name__)

# get configs
with open("config.json") as config_file:
    config = json.load(config_file)
    csvfile = config["csvfile"]
    allowed_ips = config["allowed_ips"]
# set dataframe

df = pd.read_csv(csvfile, index_col='id')
df.sort_index(inplace=True)


# helper funcs
def get_filter(col, val):
    return df[col].str.contains(val, na=False, case=False)


# return filtered dataframe
def search(Name, Division):
    filt1 = get_filter('Name', Name)
    # filt2 = get_filter('Course', Course)
    filt3 = get_filter('Division', Division)
    return df.loc[filt1 & filt3, ['Name', 'Course', 'Division', 'Class No']]


# get ip
def get_ip():
    ip = ''
    if not request.headers.getlist("X-Forwarded-For"):
        ip = request.remote_addr
    else:
        ip = request.headers.getlist("X-Forwarded-For")[0]
    return ip


# routes
@app.route("/")
def renderPage():
    ip = get_ip()
    if ip not in allowed_ips:
        return "not authorised"
    return render_template('search.html', err=" ")


@app.route('/search', methods=['POST'])
def get_query():
    # regect unknown ips
    ip = get_ip()
    if ip not in allowed_ips:
        return "not authorised"

    raw_in = request.form['query'].split(',')
    try:
        Name = raw_in[0]
        Division = raw_in[1]
        results = search(Name, Division)
    except:
        return render_template('search.html', err='err: incorrect query format')
    if results.empty:
        return render_template('search.html', err='err: 0 results')
    else:
        tables_ = [results.to_html(
            classes='table table-hover', justify="unset", index=False, border=0)]
        return render_template('search.html', tables=tables_)
