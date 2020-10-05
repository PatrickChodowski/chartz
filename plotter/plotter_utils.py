def read_config(path):
    import yaml
    with open(path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def handle_configs():
    import numpy as np
    cnfg_path = 'plotter_configs/'
    filters = read_config(f'{cnfg_path}filters.yaml')
    settings = read_config(f'{cnfg_path}settings.yaml')
    data_sources = read_config(f'{cnfg_path}data_sources.yaml')
    source = settings['data_source']
    a = np.where([dsd['active'] for dsd in source])[0][0]
    source = source[a]
    setup = dict()
    setup['source'] = source
    setup['settings'] = settings
    setup['filters'] = filters
    setup['add_filters'] = [df['value'] for df in filters['add_filters']['options']]
    setup['data_sources'] = data_sources
    return setup


def create_settings():
    settings_example = """
max_metrics: -1
bg_color: '#4d4d4d'
f_color: '#7FFFD4'
plot_height: 400
plot_width: 470
plot_caching: False

data_source:
   - name: 'gbq'
     source: 'bigquery'
     project: 'project_name'
     schema: 'dash'
     sa_path: 'sa_file_path.json'
     active: True"""
    return settings_example


def create_filters():
    filters_example = """
main_filters:
  data_source:
    value: 'ds'
    name: 'Data Source'
    type: 'select'
    options:
      - value: 'unique_ds_name'
        name: 'My Data'

  plot_type:
    value: 'plot_type'
    name: 'Plot Type'
    type: 'select'
    options:
      - value: 'bar'
        name: 'Bar'
      - value: 'table'
        name: 'Table'
  metrics:
    value: 'metrics'
    name: 'Metrics'
    type: 'choices'
    options:
      - name: ''
        value: ''
  dimensions:
    value: 'dimensions'
    name: 'Dimensions'
    type: 'select'
    options:
      - name: ''
        value: ''
  aggr_type:
    value: 'aggr_type'
    name: 'Aggregates'
    type: 'select'
    options:
      - name: ''
        value: ''
      - name: 'Mean'
        value: 'avg'
      - name: 'Sum'
        value: 'sum'
      - name: 'Count'
        value: 'count'
  show_top_n:
    value: 'show_top_n'
    name: 'SHOW TOP N'
    type: 'number'
    options:
       min: 1
       max: 500
       default: 450

add_filters:
  name: 'Additional filters'
  value: 'dim_filters'
  type: 'select'
  options:
    - name: ''
      value: ''
    - name: 'Transaction Date'
      value: 'transaction_date'
    - name: 'Email"
      value: 'customer_email'
    - name: 'Product Name'
      value: 'product_name'

dim_filters:
  transaction_date:
    name: "Transaction Date"
    value: "transaction_date"
    operators:
      - "eq"
      - "lt"
      - "gt"
    duplicable: True
    type: "text"
  customer_email:
    name: "Email"
    value: "customer_email"
    operators:
      - "eq"
    duplicable: False
    type: "text" 
  product_name:
    name: "Product Name"
    value: "product_name"
    operators:
      - "eq"
    duplicable: False
    type: "text"      

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


def setup_env():
    import os
    dirp = './plotter_configs'
    if not os.path.exists(dirp):
        os.makedirs(dirp)

    function_dict = {'settings': create_settings,
                     'filters': create_filters,
                     'data_sources': create_data_sources}

    files = ['settings.yaml', 'filters.yaml', 'data_sources.yaml']
    for file in files:
        if not os.path.exists(f"{dirp}/{file}"):
            f_name = file.replace('.yaml', '')
            txt = function_dict[f_name]()
            with open(f"{dirp}/{file}", "a+") as f:
                f.write(txt)
