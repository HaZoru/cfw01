from flask import Flask, request, render_template
import pandas as pd
import json
import re


app = Flask(__name__)

# get configs
with open("config.json") as config_file:
    config = json.load(config_file)
    csvfile = config["csvfile"]
    allowed_ips = config["allowed_ips"]


# set dataframe
df = pd.read_csv(csvfile, index_col='id')
df.sort_index(inplace=True)

# vars
months_3word_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
                     'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# helper funcs


def get_filter(col, val):
    """checks if val exists in the col and return a bool filter for search()"""
    if col == 'Date of Birth':
        day = f'{int(val[0]):02}' if val[0] != 'n' else ''
        month = months_3word_list[int(val[1]) - 1] if val[1] != 'n' else ''
        year = val[2] if val[2] != 'n' else ''
        print(day, month, year)
        dob_bool = df[col].str.contains(f'{day}/', na=False, case=False) & df[col].str.contains(
            f'/{year}', na=False, case=False) & df[col].str.contains(
            f'{month}', na=False, case=True)
        return dob_bool
    return df[col].str.contains(val, na=False, case=False)


def search(Name, Division, Dob):
    """returns filtered dataframe """
    name_filt = get_filter('Name', Name) if Name else True
    div_filt = get_filter('Division', Division) if Division else True
    dob_filter = get_filter('Date of Birth', Dob) if Dob else True
    return df.loc[name_filt & div_filt & dob_filter, ['Name', 'Course', 'Division', 'Date of Birth', 'Class No']]


def get_ip():
    """returns ip address of the client"""
    ip = ''
    if not request.headers.getlist("X-Forwarded-For"):
        ip = request.remote_addr
    else:
        ip = request.headers.getlist("X-Forwarded-For")[0]
    return ip


def process_input(raw_in):
    """returns NAME and DIVISION from the raw user input"""
    search_NAME = re.search(r'(name|n):(\w+)', raw_in)
    search_DIVISION = re.search(r'(div|d):(\w+)', raw_in)
    search_DOB = re.search(
        r'dob:([0-2]?[1-9]|3[0-1]|n)/(0?[1-9]|1[1-2]|n)/(\d{4}|n)', raw_in)

    NAME = search_NAME.group(2).replace(
        '_', ' ') if search_NAME is not None else ''
    DIVISION = search_DIVISION.group(2).replace(
        '_', ' ') if search_DIVISION is not None else ''
    # DOB = re.search(r'(dob):(\d\d?/\d\d?/\d{4})', raw_in).group(2)
    DOB = [search_DOB.group(1), search_DOB.group(2), search_DOB.group(
        3)] if search_DOB is not None else ''
    print(DOB)
    return NAME, DIVISION, DOB


# routes
@app.route("/")
def renderPage():
    """render home page"""
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

    # process raw input
    raw_in = request.form['query']
    NAME, DIVISION, DOB = process_input(raw_in)

    # catch no args
    if NAME == '' and DIVISION == '' and DOB == '':
        return render_template('search.html', err='err: no arguments given')

    # render tables
    results = search(NAME, DIVISION, DOB)
    if results.empty:
        return render_template('search.html', err='0 results')
    else:
        dflen = results.shape[0]
        tables_ = [results.to_html(
            classes='table table-hover', justify="unset", index=False, border=0)]
        return render_template('search.html', tables=tables_, dflen=dflen)


@app.route('/docs')
def render_docs():
    return render_template('docs.html')
