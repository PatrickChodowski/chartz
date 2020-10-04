from flask import Blueprint, request, render_template
from plotter.plots import Plots
from bokeh.embed import components
from bokeh.resources import INLINE
from plotter.plotter_utils import handle_configs

js_resources = INLINE.render_js()
css_resources = INLINE.render_css()

setup = handle_configs()
plots = Plots(plot_height=setup['settings']['plot_height'],
              plot_width=setup['settings']['plot_width'],
              f_color=setup['settings']['f_color'],
              bg_color=setup['settings']['bg_color'],
              add_filters=setup['add_filters'],
              data_sources=setup['data_sources'],
              source=setup['source'])

plotter = Blueprint('plotter',
                    __name__,
                    template_folder='plotter_templates',
                    static_folder='plotter_static')

plot_type_dict = {'bar':    plots.plot_bar,
                  'points': plots.plot_points,
                  'time':   plots.plot_time,
                  'box':    plots.plot_box,
                  'shot':   plots.plot_shots,
                  'table':  plots.plot_table}

@plotter.route('/dash', methods=['POST', 'GET'])
def dash():
    return render_template('dash.html',
                           filters=setup['filters'])

@plotter.route('/get_setup/<what>', methods=['POST'])
def get_setup(what):
    '''
    settings, filters, data_sources, filter_info
    '''
    if what == 'data_sources':
        try:
            args = request.args.to_dict()
            return setup[what][args['data_source']]
        except KeyError as e:
            return str(e)
    elif what == 'filters':
        args = request.args.to_dict()
        filters = setup[what]['add_filters']['options']
        dimensions = setup['data_sources'][args['data_source']]['dimensions']
        filter_dict = dict()
        for d in filters:
            if d['value'] in dimensions:
                filter_dict[d['value']] = d['name']
        return filter_dict
    elif what == 'filter_info':
        args = request.args.to_dict()
        filter_data = setup['filters']['dim_filters'][args['filter_name']]
        return filter_data
    else:
        return setup[what]

@plotter.route('/plot/<type>', methods=['POST', 'GET'])
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

