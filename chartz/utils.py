def read_config(path):
    import yaml
    with open(path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def handle_configs(lib_path):
    try:
        config_path = './chartz_configs/'
        filters = read_config(f'{config_path}filters.yaml')
        settings = read_config(f'{config_path}settings.yaml')
        data_sources = read_config(f'{config_path}data_sources.yaml')
        main_filters = read_config(f'{lib_path}chartz_static/main_filters.yaml')

        main_filters['data_source']['options'] = list()
        for k in data_sources.keys():
            d = dict()
            d['value'] = k
            d['name'] = k
            main_filters['data_source']['options'].append(d)

        setup = dict()
        setup['db_source'] = settings['db_source']
        setup['settings'] = settings
        setup['add_filters'] = list(filters.keys())
        setup['dim_filters'] = filters
        setup['data_sources'] = data_sources
        setup['main_filters'] = main_filters
        setup['plot_caching'] = settings['plot_caching']
        return setup
    except FileNotFoundError as e:
        print(e)


def create_settings():
    settings_example = """

bg_color: '#4d4d4d'
filters_bg_color: '#007fff'
f_color: '#7FFFD4'
plot_height: 400
plot_width: 470

plot_caching: 
  active: False
  cache_storage: local #gcpbucket (possible only if you have bigquery as data source)
  cache_time: 86400
  cache_bucket: "bucket_name" #works only if cache_storage is gcpbucket
  cache_path: "./chartz_configs/cache"  #cache for gcpbucket

db_source:
   - name: 'gbq'
     source: 'bigquery'
     project: 'project_name'
     connection_type: 'personal_account' # 'service_account'
     sa_path: 'sa_file_path.json' # only if connection type is service account
     file_format: 'sql'

   - name: 'pgsql'
     source: 'postgresql'
     user: 'username'
     password: 'password'
     host: '127.0.0.1'
     port: '5432'
     database: 'exampledb'

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
  schema: 'table_schema_name'
  db_source: 'db_source_from_settings'
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


def create_example_main(parent_directory='.'):
    import os
    example_main_text = """
from flask import Flask
import os

SECRET_KEY = os.urandom(32)
from chartz import chartz
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
    if not os.path.exists(f"{parent_directory}/example_main.py"):
        with open(f"{parent_directory}/example_main.py", "a+") as f:
            f.write(example_main_text)


def setup_env(parent_directory='.', force_recreate=True):
    import os
    dir_chartz = f'{parent_directory}/chartz_configs'
    function_dict = {'settings': create_settings,
                     'filters': create_filters,
                     'data_sources': create_data_sources}

    files = ['settings.yaml', 'filters.yaml', 'data_sources.yaml']
    if force_recreate:
        os.makedirs(dir_chartz)
        os.makedirs(f'{dir_chartz}/views')
        os.makedirs(f'{dir_chartz}/cache')
        for file in files:
            f_name = file.replace('.yaml', '')
            txt = function_dict[f_name]()
            with open(f"{dir_chartz}/{file}", "a+") as f:
                f.write(txt)
    else:
        if not os.path.exists(dir_chartz):
            os.makedirs(dir_chartz)
        if not os.path.exists(f'{dir_chartz}/views'):
            os.makedirs(f'{dir_chartz}/views')
        if not os.path.exists(f'{dir_chartz}/cache'):
            os.makedirs(f'{dir_chartz}/cache')
        for file in files:
            if not os.path.exists(f"{dir_chartz}/{file}"):
                f_name = file.replace('.yaml', '')
                txt = function_dict[f_name]()
                with open(f"{dir_chartz}/{file}", "a+") as f:
                    f.write(txt)
    create_example_main(parent_directory)


def get_paths():
    import importlib
    resources_path0 = importlib.import_module('chartz.chartz_templates')
    resources_path = str(resources_path0.__path__).replace("_NamespacePath(['", '').replace("chartz_templates'])", '')
    return resources_path


def make_table_yml(table_unique_name, client, project, dataset, table, limit=10000, unique_values=3):

    # get data
    sql_meta = f""" SELECT * FROM `{project}.{dataset}.{table}` limit {limit} """
    df = client.query(query=sql_meta).to_dataframe()

    # get object/bool
    possible_dimensions = df.select_dtypes(include=['object', 'bool', 'category', 'datetime64']).columns.to_list()
    make_table_filters(df, possible_dimensions)
    # get numerics
    possible_metrics = df.select_dtypes(include=['number', 'integer']).columns.to_list()

    # find possible dimensions in numerical (limited amount of values)
    possible_num_dims = list()
    for col in df[possible_metrics]:
        if df[col].nunique() <= unique_values:
            possible_num_dims.append(col)

    possible_dimensions += possible_num_dims

    # create file
    table_meta = dict()
    table_meta[table_unique_name] = dict()
    table_meta[table_unique_name]['value'] = table_unique_name
    table_meta[table_unique_name]['table'] = table
    table_meta[table_unique_name]['schema'] = dataset
    table_meta[table_unique_name]['db_source'] = 'db_source_from_settings'
    table_meta[table_unique_name]['plots'] = ['bar', 'points', 'time', 'box', 'table']
    table_meta[table_unique_name]['dimensions'] = [''] + possible_dimensions
    table_meta[table_unique_name]['metrics'] = possible_metrics
    table_meta[table_unique_name]['calculations'] = ['']
    table_meta[table_unique_name]['fixed_filters'] = ['']

    import yaml
    with open(f'{table_unique_name}.yaml', 'w') as file:
        table_meta_yml = yaml.dump(table_meta, file)


def make_table_filters(df, possible_dimensions):
    filters_list = list()

    for col in possible_dimensions:
        filter_dict = dict()
        filter_dict[col] = dict()

        col_options = list(df[col].unique())

        filter_dict[col]['name'] = col
        filter_dict[col]['value'] = col
        filter_dict[col]['operators'] = ['eq']
        filter_dict[col]['duplicable'] = False

        # possible types: choices, checkbox, number, select
        # define the type smart way (depends on the options len)

        if col_options.__len__() <= 4:
            dim_type = 'checkbox'
        else:
            dim_type = 'choices'

        filter_dict[col]['type'] = dim_type
        filter_dict[col]['options'] = col_options

        # add to list
        filters_list.append(filter_dict)

        import yaml
        with open(f'filters_temp.yaml', 'w') as file:
            table_meta_yml = yaml.dump(filters_list, file, allow_unicode=True)
