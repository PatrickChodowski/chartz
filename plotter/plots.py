
from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure
from bokeh.transform import factor_cmap


# todo: fix cache plots
# todo: dokumentacja + porzadne readme
# todo: iterate by -> plot per category
# todo: move main filters and add filters definiton to package insides

# todo: kto jest w jakim percentylu
# todo: handle operators -- czy moze wszystkie filtry jako tekst xd
# todo: improve styling of forms
# todo: (maybe last step ever- cleanup script.js and styles.css script) reorgenize in some logical order


class Plots:
    def __init__(self, plot_height, plot_width, f_color, bg_color, add_filters, data_sources, source):
        self.plot_height = plot_height
        self.plot_width = plot_width
        self.f_color = f_color
        self.bg_color = bg_color
        self.add_filters = add_filters
        self.source = source
        self.data_sources = data_sources

        self.title_text = None
        self.client = None
        self.con_q = {
                    'bigquery': self._data_bigquery,
                    'postgresql': self._data_sql
                }

    def _handle_connection(self, **params):
        if self.client is None:
            try:
                assert self.source['source'] in ['bigquery', 'postgresql']
                con_dict = {
                    'bigquery': self._connect_bigquery,
                    'postgresql': self._connect_postgresql
                }
                con_dict[self.source['source']]()
            except AssertionError:
                return 'Make sure that active source in settings is one of [bigquery. postgresql]'
        else:
            pass

    def _handle_data(self, **params):
        args = self.source
        all_params = {**args, **params}
        self._handle_connection(**params)
        sql, metrics = self._make_query(**all_params)
        df = self.con_q[self.source['source']](sql)
        return df, metrics

    def _connect_bigquery(self):
        from google.cloud import bigquery
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_file(self.source['sa_path'])
        self.client = bigquery.Client(
            credentials=credentials,
            project=self.source['project'],
        )

    def _connect_postgresql(self):
        from sqlalchemy import create_engine
        db_string = f"postgres://{self.source['user']}:{self.source['password']}@{self.source['host']}:{self.source['port']}/{self.source['database']}"
        self.client = create_engine(db_string)

    def _data_bigquery(self, sql):
        df = self.client.query(query=sql).to_dataframe()
        df = df.round(3)
        if df.shape[0] == 0:
            raise ValueError(f"""Value error: Empty dataset. Please double check query: {sql}""")
        return df

    def _data_sql(self, sql):
        import pandas as pd
        df = pd.read_sql(sql, con=self.client)
        df = df.round(3)
        if df.shape[0] == 0:
            raise ValueError(f"""Value error: Empty dataset. Please double check query: {sql}""")
        return df

    def _make_query(self, **args):
        possible_calcs = self.data_sources[args['source']]['calculations']
        calcs_dict = dict((key, d[key]) for d in possible_calcs for key in d)
        calcs = list(calcs_dict.keys())
        metrics = args['metrics'].split(';')
        df_name = self.data_sources[args['source']]['table']

        req_fields = self.data_sources[args['source']]['req_fields']
        if req_fields is not None:
            # remove from req fields if given fields is already in dimensions or metrics:
            req_fields2 = [rq for rq in req_fields if (rq not in metrics) & (rq != args['dimensions'])]
            rqf_txt = ','.join(req_fields2) + ','
        else:
            rqf_txt = ''

        # disgusting
        if args['aggr_type'] == '':
            prtn_txt_1 = ''
            prtn_txt_2 = ''
            gb_txt = ''
        else:
            prtn_txt_1 = '('
            prtn_txt_2 = ')'
            rqf_txt = ''  # erases required columns if there is  aggregation
            if args['dimensions'] != '':
                gb_txt = f"GROUP BY {rqf_txt}{args['dimensions']}"
            else:
                gb_txt = ''

        if args['dimensions'] == '':
            cm_txt = ''
        else:
            cm_txt = ', '

        colqs = list()
        for nc in metrics:
            if nc not in calcs:
                colqs.append(f"{args['aggr_type']}{prtn_txt_1}{nc}{prtn_txt_2} AS {nc}")
            else:
                colqs.append(f"{calcs_dict[nc]} AS {nc}")
        num_cols = ','.join(colqs)

        sql = f"""SELECT {rqf_txt} {args['dimensions']}{cm_txt}{num_cols}
FROM {args['project']}.{args['schema']}.{df_name} WHERE 1=1
"""
        for k, v in args.items():
            if k in self.add_filters:
                if ';' in v:
                    v2 = "('" + v.replace(";", "','") + "')"
                    wstr = f" AND CAST({k} AS STRING) IN {v2} "
                else:
                    wstr = f" AND CAST({k} AS STRING) = '{v}' "
                sql += wstr
            else:
                pass
        sql += gb_txt

        if (args['having'] != '') & (gb_txt != ''):
            sql += f" HAVING {args['having']} "

        obl_txt = f" ORDER BY {metrics[0]} DESC LIMIT {args['show_top_n']} "
        sql += obl_txt
        print(sql)
        return sql, metrics

    def plot_box(self, **params):
        import math
        from statistics import median
        import numpy as np

        df, metrics = self._handle_data(**params)
        metric = metrics[0]

        df[metric] = np.nan_to_num(df[metric])
        up_limit = int(round(math.ceil(max(df[metric])) + median(df[metric].values) * 0.1))
        down_limit = int(round(math.ceil(min(df[metric])) - median(df[metric].values) * 0.1))

        if up_limit == down_limit:
            down_limit = down_limit - 1

        try:
            groups = df.groupby(params['dimensions'])

            q1 = groups[metric].quantile(q=0.25).to_frame()
            q2 = groups[metric].quantile(q=0.5).to_frame()
            q3 = groups[metric].quantile(q=0.75).to_frame()
            iqr = q3 - q1
            upper = q3 + 1.5 * iqr
            lower = q1 - 1.5 * iqr
            upper.reset_index(inplace=True)
            lower.reset_index(inplace=True)
            q1.reset_index(inplace=True)
            q2.reset_index(inplace=True)
            q3.reset_index(inplace=True)

            p = figure(x_range=upper[params['dimensions']].astype(str).unique(),
                       y_range=[down_limit, up_limit],
                       plot_height=self.plot_height, plot_width=self.plot_width)

            qmin = groups[metric].quantile(q=0.00).to_frame()
            qmax = groups[metric].quantile(q=1.00).to_frame()

            upper[metric] = [min([x, y]) for (x, y) in zip(qmax.loc[:, metric], upper.loc[:, metric])]
            lower[metric] = [max([x, y]) for (x, y) in zip(qmin.loc[:, metric], lower.loc[:, metric])]

            p.segment(upper[params['dimensions']], upper[metric], upper[params['dimensions']], q3[metric], line_color="white")
            p.segment(lower[params['dimensions']], lower[metric], lower[params['dimensions']], q1[metric], line_color="white")

            p.vbar(q2[params['dimensions']], 0.7, q2[metric], q3[metric],
                   fill_color=self.f_color, line_color="white")
            p.vbar(q1[params['dimensions']], 0.7, q1[metric], q2[metric],
                   fill_color=self.f_color, line_color="white")

            p.rect(lower[params['dimensions']], lower[metric], 0.2, 0.01, line_color='white')
            p.rect(upper[params['dimensions']], upper[metric], 0.2, 0.01, line_color='white')
            p = self._style_plot(p)
            return p
        except KeyError as e:
            if params['dimensions'] == '':
                return 'Box chart requires grouping dimension'
            else:
                return str(e)

    def plot_time(self, **params):
        import math
        from statistics import median
        import numpy as np
        df, metrics = self._handle_data(**params)

        try:
            df.sort_values(params['dimensions'], inplace=True, ascending=True)
            df[params['dimensions']] = df[params['dimensions']].astype('str')
            source = ColumnDataSource(df)
            metric = metrics[0]

            df[metric] = np.nan_to_num(df[metric])
            up_limit = int(round(math.ceil(max(df[metric])) + median(df[metric].values) * 0.3))
            p2 = figure(x_range=source.data[params['dimensions']], y_range=[0, up_limit],
                        plot_height=self.plot_height, plot_width=self.plot_width)
            p2.line(y=metric, x=params['dimensions'], source=source, line_color=self.f_color)
            p2.xaxis.major_label_orientation = 0.9
            p2 = self._style_plot(p2)
            return p2
        except KeyError as e:
            if params['dimensions'] == '':
                return 'Line chart requires grouping dimension, ideally date one'
            else:
                return str(e)

    def plot_bar(self, **params):
        import math
        from statistics import median
        try:
            df, metrics = self._handle_data(**params)
            source_aggr = ColumnDataSource(df)
            metric = metrics[0]
            up_limit = int(round(math.ceil(max(df[metric])) + median(df[metric].values) * 0.1))
            df_aggr = source_aggr.data[params['dimensions']]
        except ValueError as e:
            return str(e)
        except KeyError as e:
            if params['dimensions'] == '':
                return 'Bar chart requires grouping dimension'
            else:
                return str(e)

        try:
            if df[params['dimensions']].nunique() != df.shape[0]:
                raise ValueError('Data is not aggregated. Please select aggregation type')

            p2 = figure(x_range=df_aggr,
                        y_range=[0, up_limit],
                        plot_height=self.plot_height,
                        plot_width=self.plot_width)
            p2.vbar(top=metric, x=params['dimensions'], source=source_aggr,
                    width=0.3, fill_color=self.f_color, line_color=self.f_color)
            p2 = self._style_plot(p2)
            p2.xaxis.major_label_orientation = 0.9
            p2.left[0].formatter.use_scientific = False
            return p2
        except ValueError as e:
            return str(e)

    def plot_points(self, **params):
        import math
        from statistics import median

        try:
            df, metrics = self._handle_data(**params)
            metric1 = metrics[0]
            metric2 = metrics[1]
            source_aggr = ColumnDataSource(df)
            up_limit1 = int(round(math.ceil(max(df[metric1])) + median(df[metric1].values) * 0.12))
            up_limit2 = int(round(math.ceil(max(df[metric2])) + median(df[metric2].values) * 0.12))
            down_limit1 = int(round(math.ceil(min(df[metric1])) - median(df[metric1].values) * 0.12))
            down_limit2 = int(round(math.ceil(min(df[metric2])) - median(df[metric2].values) * 0.12))

            if down_limit1 == up_limit1:
                down_limit1 = down_limit1 - 1

            if down_limit2 == up_limit2:
                down_limit2 = down_limit2 - 1
        except ValueError as e:
            return str(e)
        except IndexError as e:
            return "Points chart requires exactly 2 metrics"
        except KeyError as e:
            if params['dimensions'] == '':
                return 'Points chart requires grouping dimension'
            else:
                return str(e)
        try:
            if (params['dimensions'] == '') | (params['aggr_type'] == ''):
                raise KeyError
            p2 = figure(x_range=[down_limit1, up_limit1],
                        y_range=[down_limit2, up_limit2],
                        plot_height=self.plot_height,
                        plot_width=self.plot_width)

            type_sc = 'circle' #['circle','triangle','square','']
            p2.scatter(x=metric1, y=metric2,
                       marker=type_sc, source=source_aggr, fill_alpha=0.5, size=12,
                       line_color=self.bg_color, fill_color=self.f_color)
            p2.yaxis.axis_label = metric2
            p2.xaxis.axis_label = metric1
            p2.yaxis.axis_label_text_color = self.f_color
            p2.xaxis.axis_label_text_color = self.f_color

            p2.text(x=metric1, y=metric2,
                    text=params['dimensions'], source=source_aggr, text_color=self.f_color,
                    text_align="center", text_font_size="10pt")

            p2 = self._style_plot(p2)
        except KeyError as e:
            return 'Points chart requires grouping dimension and aggregation'

        return p2

    def plot_table(self, **params):
        from bokeh.models.widgets import DataTable, TableColumn
        df, metrics = self._handle_data(**params)

        columns = list()
        for col in df.columns.to_list():
            columns.append(TableColumn(field=col, title=col))
        source = ColumnDataSource(df)
        p2 = DataTable(columns=columns,
                       source=source,
                       fit_columns=True,
                       max_height=(self.plot_height - 20),
                       max_width=(self.plot_width - 40),
                       index_width=0)
        p2.width = (self.plot_width - 30)
        p2.height = (self.plot_height - 20)
        return p2

    def plot_shots(self, **params):
        try:
            df, metrics = self._handle_data(**params)
            df['made'] = df['made'].astype('str')
            source = ColumnDataSource(df)
            p2 = figure(width=470, height=460,
                        x_range=[-250, 250],
                        y_range=[422.5, -47.5],
                        min_border=0,
                        x_axis_type=None,
                        y_axis_type=None,
                        outline_line_color=self.bg_color)

            colors = factor_cmap('made', palette=['green', 'red'], factors=['1', '0'])
            p2.scatter(x="loc_x", y="loc_y",
                       source=source,
                       size=10,
                       color=colors,
                       alpha=0.4,
                       line_alpha=0.4)

            self._draw_court(p2, line_width=1)
            p2 = self._style_plot(p2)
        except KeyError as e:
            if params['aggr_type'] != '':
                return "Shotchart wont work with nonempty aggregation"
            else:
                return e
        return p2

    def _style_plot(self, p):
        p.toolbar.logo = None
        p.toolbar_location = 'below'
        p.xgrid.grid_line_color = self.f_color
        p.xgrid.grid_line_width = 0
        p.xgrid.grid_line_alpha = 0
        p.ygrid.grid_line_color = None
        p.xaxis.axis_line_width = 0
        p.yaxis.axis_line_width = 0
        p.xaxis.axis_line_color = None
        p.yaxis.minor_tick_line_color = None
        p.yaxis.major_tick_line_color = None
        p.xaxis.major_tick_line_color = None
        p.xaxis.minor_tick_line_color = None
        p.axis.major_label_text_color = self.f_color
        p.axis.major_label_text_font_size = '10px'
        p.background_fill_color = self.bg_color
        p.outline_line_width = 0
        p.border_fill_color = self.bg_color
        t = Title()
        t.text = self.title_text
        t.text_color = self.f_color
        p.title = t

        return p

    def _draw_court(self, figure, line_width=1):
        import numpy as np
        pi = 3.14
        # hoop
        figure.circle(x=0, y=0, radius=7.5, fill_alpha=0,
                      line_color=self.f_color, line_width=line_width)

        # backboard
        figure.line(x=range(-30, 31), y=-12.5, line_color=self.f_color)

        # The paint
        # outerbox
        figure.rect(x=0, y=47.5, width=160, height=190, fill_alpha=0,
                    line_color=self.f_color, line_width=line_width)
        # innerbox
        # left inner box line
        figure.line(x=-60, y=np.arange(-47.5, 143.5), line_color=self.f_color,
                    line_width=line_width)
        # right inner box line
        figure.line(x=60, y=np.arange(-47.5, 143.5), line_color=self.f_color,
                    line_width=line_width)

        # Restricted Zone
        figure.arc(x=0, y=0, radius=40, start_angle=pi, end_angle=0,
                   line_color=self.f_color, line_width=line_width)

        # top free throw arc
        figure.arc(x=0, y=142.5, radius=60, start_angle=pi, end_angle=0,
                   line_color=self.f_color)

        # bottome free throw arc
        figure.arc(x=0, y=142.5, radius=60, start_angle=0, end_angle=pi,
                   line_color=self.f_color, line_dash="dashed")

        # Three point line
        # corner three point lines
        figure.line(x=-220, y=np.arange(-47.5, 92.5), line_color=self.f_color,
                    line_width=line_width)
        figure.line(x=220, y=np.arange(-47.5, 92.5), line_color=self.f_color,
                    line_width=line_width)
        # # three point arc
        figure.arc(x=0, y=0, radius=237.5, start_angle=3.528, end_angle=-0.3863,
                   line_color=self.f_color, line_width=line_width)

        return figure

    def check_plot_cache(self, settings, url):
        if settings['plot_caching']:
            if settings['plot_cache_storage'] == 'local':
                import os.path
                return os.path.exists(settings['plot_local_cache'] + '/' + url + '.html')
            elif settings['plot_cache_storage'] == 'gcpbucket':
                path = f"{settings['plot_gcpbucket_path']}{url}.html"
                blob = bucket.blob(path)
                return blob.exists()
            else:
                return False
        else:
            return False
