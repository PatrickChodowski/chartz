def read_config(path):
    import yaml
    with open(path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def handle_configs(lib_path):
    try:
        config_path = './plotter_configs/'
        filters = read_config(f'{config_path}filters.yaml')
        settings = read_config(f'{config_path}settings.yaml')
        data_sources = read_config(f'{config_path}data_sources.yaml')

        main_filters = read_config(f'{lib_path}plotter_static/main_filters.yaml')
        source = settings['data_source']
        main_filters['data_source']['options'] = list()
        for k in data_sources.keys():
            d = dict()
            d['value'] = k
            d['name'] = k
            main_filters['data_source']['options'].append(d)

        act_check = [dsd['active'] for dsd in source]
        which_active = [i for i, x in enumerate(act_check) if x][0]
        assert isinstance(which_active, int)
        source = source[which_active]
        setup = dict()
        setup['source'] = source
        setup['settings'] = settings
        setup['add_filters'] = list(filters.keys())
        setup['dim_filters'] = filters
        setup['data_sources'] = data_sources
        setup['main_filters'] = main_filters
        return setup
    except AssertionError:
        if type(which_active) != int:
            print('Please make sure you have exactly 1 active data source in data_sources.yaml')
    except FileNotFoundError as e:
        print(e)


def create_settings():
    settings_example = """

bg_color: '#4d4d4d'
filters_bg_color: '#007fff'
f_color: '#7FFFD4'
plot_height: '400px'
plot_width: '470px'

plot_caching: False
cache_storage: 'local' # gcpbucket or local
cache_time: 86400 # in seconds
cache_bucket: 'bucketname' # works only if cache_storage is gcpbucket
cache_path: './plotter_configs/cache'  # use just 'cache' for gcpbucket

data_source:
   - name: 'gbq'
     source: 'bigquery'
     project: 'project_name'
     schema: 'dash'
     sa_path: 'sa_file_path.json'
     active: True

   - name: 'pgsql'
     source: 'postgresql'
     user: 'username'
     password: 'password'
     host: '127.0.0.1'
     port: '5432'
     database: 'exampledb'
     schema: 'dash'
     active: False

     """
    return settings_example


def create_filters():
    filters_example = """
transaction_date:
  name: 'Transaction Date'
  value: 'transaction_date'
  operators:
    - 'eq'
    - 'lt'
    - 'gt'
  duplicable: True
  type: 'text'
customer_email:
  name: 'Email'
  value: 'customer_email'
  operators:
    - 'eq'
  duplicable: False
  type: 'text'
product_name:
  name: 'Product Name'
  value: 'product_name'
  operators:
    - 'eq'
  duplicable: False
  type: 'text'      

    """
    return filters_example


def create_data_sources():
    ds_example = """
unique_ds_name:
  value: 'unique_ds_name'
  table: 'actual_table_name'
  plots:
    - 'bar'
    - 'table'
  dimensions:
    - ''
    - 'transaction_date'
    - 'cutomer_email'
    - 'product_name'
  metrics:
    - 'amount'
    - 'quantity'
  calculations:
    - avg_order:
        'IFNULL(SUM(amount)/NULLIF(SUM(quantity),0),0)'
  fixed_filters: '&transaction_date>=20200101'
"""
    return ds_example


def create_example_main():
    import os
    example_main_text = """
from flask import Flask
import os

SECRET_KEY = os.urandom(32)
from chartz.chartz import chartz
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config["FLASK_DEBUG"] = 0
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.register_blueprint(chartz)

@app.route('/', methods=['POST','GET'])
def index():
    return 'hello! chartz will be on /dash!'


if __name__ == '__main__':
   app.run(port=5001, debug=False)    
"""
    if not os.path.exists("example_main.py"):
        with open(f"example_main.py", "a+") as f:
            f.write(example_main_text)


def setup_env(force_recreate=True):
    import os
    dir_plotter = './plotter_configs'
    function_dict = {'settings': create_settings,
                     'filters': create_filters,
                     'data_sources': create_data_sources}

    files = ['settings.yaml', 'filters.yaml', 'data_sources.yaml']
    if force_recreate:
        os.makedirs(dir_plotter)
        os.makedirs(f'{dir_plotter}/views')
        os.makedirs(f'{dir_plotter}/cache')
        for file in files:
            f_name = file.replace('.yaml', '')
            txt = function_dict[f_name]()
            with open(f"{dir_plotter}/{file}", "a+") as f:
                f.write(txt)
    else:
        if not os.path.exists(dir_plotter):
            os.makedirs(dir_plotter)
        if not os.path.exists(f'{dir_plotter}/views'):
            os.makedirs(f'{dir_plotter}/views')
        if not os.path.exists(f'{dir_plotter}/cache'):
            os.makedirs(f'{dir_plotter}/cache')
        for file in files:
            if not os.path.exists(f"{dir_plotter}/{file}"):
                f_name = file.replace('.yaml', '')
                txt = function_dict[f_name]()
                with open(f"{dir_plotter}/{file}", "a+") as f:
                    f.write(txt)
    create_example_main()


def get_paths():
    import importlib
    resources_path0 = importlib.import_module('chartz.chartz_templates')
    resources_path = str(resources_path0.__path__).replace("_NamespacePath(['", '').replace("chartz_templates'])", '')
    return resources_path
