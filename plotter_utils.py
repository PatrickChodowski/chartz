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


