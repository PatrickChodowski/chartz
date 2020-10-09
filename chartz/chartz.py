from flask import Blueprint, request, render_template
from chartz.plots import Plots
from bokeh.embed import components
from bokeh.resources import INLINE
from chartz.utils import handle_configs, get_paths

js_resources = INLINE.render_js()
css_resources = INLINE.render_css()

resources_path = get_paths()
setup = handle_configs(resources_path)

try:
    setup['settings']['plot_height']
except KeyError:
    print('Have you created settings.yaml? Try running setup_env() from chartz.utils as a first step')

plots = Plots(plot_height=setup['settings']['plot_height'],
              plot_width=setup['settings']['plot_width'],
              f_color=setup['settings']['f_color'],
              bg_color=setup['settings']['bg_color'],
              add_filters=setup['add_filters'],
              data_sources=setup['data_sources'],
              source=setup['source'])

chartz = Blueprint('chartz',
                    __name__,
                    template_folder=f'{resources_path}chartz_templates',
                    static_folder=f'{resources_path}chartz_static')

plot_type_dict = {'bar':    plots.plot_bar,
                  'points': plots.plot_points,
                  'time':   plots.plot_time,
                  'box':    plots.plot_box,
                  'shot':   plots.plot_shots,
                  'table':  plots.plot_table}

@chartz.route('/dash', methods=['POST', 'GET'])
def dash():
    return render_template('dash.html', filters=setup['main_filters'])


@chartz.route('/get_data_sources', methods=['POST'])
def get_data_sources():
    try:
        args = request.args.to_dict()
        return setup['data_sources'][args['data_source']]
    except KeyError as e:
        return str(e)

@chartz.route('/get_filter_info', methods=['POST'])
def get_filter_info():
    args = request.args.to_dict()
    filter_data = setup['dim_filters'][args['filter_name']]
    return filter_data

@chartz.route('/get_settings', methods=['POST'])
def get_settings():
    return setup['settings']


@chartz.route('/plot/<type>', methods=['POST', 'GET'])
def plot(type):
    url = request.url.split('plot/')[1]
    if plots.check_plot_cache(setup['settings'], url):
        if setup['settings']['plot_cache_storage'] == 'local':
            with open(f"{setup['settings']['plot_local_cache']}/{url}.html") as f:
                p = f.read()
                return p
        # elif setup['settings']['plot_cache_storage'] == 'gcpbucket':
        #     path = f"{setup['settings']['plot_gcpbucket_path']}{url}.html"
        #     blob = bucket.blob(path)
        #     p = blob.download_as_string()
        #     return p
    else:
        args = request.args.to_dict()
        p = plot_type_dict[type](**args)
        if isinstance(p, str):
            return f'<a class="error_msg"> {p} </a>'
        else:
            p_script, p_div = components(p)
            html_file = render_template('plot.html',
                                        bokeh_js=js_resources,
                                        bokeh_css=css_resources,
                                        plot_script=p_script,
                                        plot_div=p_div)

        if setup['settings']['plot_caching']:
            if setup['settings']['plot_cache_storage'] == 'local':
                with open(f"{setup['settings']['plot_local_cache']}/{url}.html", "w+") as f:
                    f.write(html_file)
            # else:
            #     file_blob = bucket.blob(f"{setup['settings']['plot_gcpbucket_path']}{url}.html")
            #     with open(f'/tmp/{url}.html', "w+") as f:
            #         f.write(html_file)
            #     file_blob.upload_from_filename(f'/tmp/{url}.html')
        return html_file


@chartz.route('/save_view', methods=['POST'])
def save_view():
    import json
    data = request.data
    data_dict = json.loads(data.decode())
    view_name = data_dict['view_name']
    query_log = data_dict['query_log']
    with open(f'./chartz_configs/views/{view_name}.json', 'w') as fp:
        json.dump(query_log, fp)
    return '200'

@chartz.route('/list_views', methods=['POST'])
def list_views():
    import glob
    view_list = glob.glob('./chartz_configs/views/*.json')
    views_cleaned = [v.replace('./chartz_configs/views/', '').replace('.json','') for v in view_list]
    views = ';'.join(views_cleaned)
    return views, '200'

@chartz.route('/load_view', methods=['POST'])
def load_view():
    import json
    data = request.data
    data_dict = json.loads(data.decode())
    view_name = data_dict['view_name']
    with open(f'./chartz_configs/views/{view_name}.json', 'r') as fp:
        query_log = json.load(fp)
    return query_log, '200'

