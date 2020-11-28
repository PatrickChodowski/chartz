from bokeh.models import ColumnDataSource, Title
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
import logging


class Plots:
    '''
    Plots class handles the connection to database (big_query, postgres),
    initiates query builder class with arguments from client , sql builder send back the query and
    it reads the data and builds the plot
    '''

    def __init__(self, plot_height, plot_width, f_color, bg_color, add_filters, data_source, db_source, plot_caching):
        self.plot_height = plot_height
        self.plot_width = plot_width
        self.f_color = f_color
        self.bg_color = bg_color
        self.add_filters = add_filters
        self.db_source = db_source
        self.data_source = data_source
        self.plot_caching = plot_caching

        self.title_text = None
        self.client = None
        self.bucket = None
        self.query_source = None
        self.current_db_source = None


        self.con_q = {
            'bigquery': self._data_bigquery,
            'postgresql': self._data_sql
        }

    def _create_connection(self, query_source):
        '''
        1) It creates connection based on query_source argument
        param query_source come from data_sources.yaml and is specified for each table
        It should have the equivalent in settings[db_source]
        '''
        # which db_source for query_source:
        self.current_db_source = [d for d in self.db_source if d['name'] == query_source][0]
        self.query_source = query_source
        try:
            assert self.current_db_source['source'] in ['bigquery', 'postgresql']
            con_dict = {
                'bigquery': self._connect_bigquery,
                'postgresql': self._connect_postgresql
            }
            con_dict[self.current_db_source['source']]()
        except AssertionError:
            return 'Make sure that active source in settings is one of [bigquery. postgresql]'


    @staticmethod
    def _build_sql(**params):
        '''
        1) Creates SQLBuilder instance with parameters
        2) Calls make_query method
        returns query text and metrics list
        '''
        try:
            from chartz import SqlBuilder
            sql_builder = SqlBuilder(**params)
            sql = sql_builder.make_query()
            metrics = sql_builder.metrics
            return sql, metrics
        except Exception as e:
            raise

    def _handle_data(self, **params):
        '''
        1) creates sql query
        2) Sends query to df and retrieves data
        returns df, list of metrics
        '''
        try:
            params['add_filters'] = self.add_filters
            params['data_source'] = self.data_source
            params['current_db_source'] = self.current_db_source

            sql, metrics = self._build_sql(**params)

            print('QUERY:')
            print(sql)

            print('METRICS:')
            print(metrics)

            df = self.con_q[self.current_db_source['source']](sql)
            print('DATA:')
            print(df.head())

            return df, metrics
        except Exception as e:
            raise

    def _connect_bigquery(self):
        from google.cloud import bigquery
        from google.oauth2 import service_account

        if self.current_db_source['connection_type'] == 'service_account':
            credentials = service_account.Credentials.from_service_account_file(self.current_db_source['sa_path'])
            self.client = bigquery.Client(
                credentials=credentials,
                project=self.current_db_source['project'],
            )
        elif self.current_db_source['connection_type'] == 'personal_account':
            # personal account ran from identification before
            # gcloud auth application-default login
            self.client = bigquery.Client(
                project=self.current_db_source['project'],
            )

    def _connect_postgresql(self):
        from sqlalchemy import create_engine
        db_string = f"postgres://{self.current_db_source['user']}:{self.current_db_source['password']}@{self.current_db_source['host']}:{self.current_db_source['port']}/{self.current_db_source['database']}"
        self.client = create_engine(db_string)

    def _data_bigquery(self, sql):
        try:
            df = self.client.query(query=sql).to_dataframe()
            df = df.round(3)
            if df.shape[0] == 0:
                raise Exception(f"""Empty dataset. Please double check query: {sql}""")

            return df
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

    def _data_sql(self, sql):
        try:
            import pandas as pd
            df = pd.read_sql(sql, con=self.client)
            df = df.round(3)
            if df.shape[0] == 0:
                raise Exception(f"""Empty dataset. Please double check query: {sql}""")
            return df
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

    def plot_box(self, **params):
        import math
        from statistics import median
        import numpy as np
        try:
            if ';' in params['dimensions']:
                raise Exception(f"""Please provide max. one dimension for boxplot""")

            df, metrics = self._handle_data(**params)
            metric = metrics[0]

            df[metric] = np.nan_to_num(df[metric])
            up_limit = int(round(math.ceil(max(df[metric])) + median(df[metric].values) * 0.1))
            down_limit = int(round(math.ceil(min(df[metric])) - median(df[metric].values) * 0.1))

            if up_limit == down_limit:
                down_limit = down_limit - 1

            # for empty dimensions
            if (params['dimensions'] != '') & (params['dimensions'] != ['']):
                group_key_name = params['dimensions']
            else:
                group_key_name = 'groupkey'
                df[group_key_name] = '1'

            groups = df.groupby(group_key_name)

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

            p = figure(x_range=upper[group_key_name].astype(str).unique(),
                       y_range=[down_limit, up_limit],
                       plot_height=self.plot_height, plot_width=self.plot_width)

            qmin = groups[metric].quantile(q=0.00).to_frame()
            qmax = groups[metric].quantile(q=1.00).to_frame()

            upper[metric] = [min([x, y]) for (x, y) in zip(qmax.loc[:, metric], upper.loc[:, metric])]
            lower[metric] = [max([x, y]) for (x, y) in zip(qmin.loc[:, metric], lower.loc[:, metric])]

            p.segment(upper[group_key_name], upper[metric], upper[group_key_name], q3[metric], line_color="white")
            p.segment(lower[group_key_name], lower[metric], lower[group_key_name], q1[metric], line_color="white")

            p.vbar(q2[group_key_name], 0.7, q2[metric], q3[metric],
                   fill_color=self.f_color, line_color="white")
            p.vbar(q1[group_key_name], 0.7, q1[metric], q2[metric],
                   fill_color=self.f_color, line_color="white")

            p.rect(lower[group_key_name], lower[metric], 0.2, 0.01, line_color='white')
            p.rect(upper[group_key_name], upper[metric], 0.2, 0.01, line_color='white')
            p = self._style_plot(p)
            return p
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

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
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

    def plot_bar(self, **params):
        import math
        from statistics import median
        try:
            if (params['dimensions'] == '') | (';' in params['dimensions']):
                raise Exception("Bar Chart requires exactly one dimension")

            if (params['aggr_type'] == ''):
                raise Exception("Bar Chart requires an aggregation")

            df, metrics = self._handle_data(**params)
            source_aggr = ColumnDataSource(df)
            metric = metrics[0]
            up_limit = int(round(math.ceil(max(df[metric])) + median(df[metric].values) * 0.1))
            df_aggr = source_aggr.data[params['dimensions']]

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
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

    def plot_points(self, **params):
        import math
        from statistics import median
        try:
            if params['metrics'].split(';').__len__() != 2:
                raise Exception("Points Chart requires exactly 2 metrics")

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

            p2 = figure(x_range=[down_limit1, up_limit1],
                        y_range=[down_limit2, up_limit2],
                        plot_height=self.plot_height,
                        plot_width=self.plot_width)

            type_sc = 'circle'  # ['circle','triangle','square','']
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
            return p2
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

    def plot_table(self, **params):
        try:
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
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

    def plot_shots(self, **params):
        try:
            if (params['aggr_type'] != ''):
                raise Exception("Shot Chart cant have an aggregation")

            params['req_fields'] = 'loc_y,loc_x,shot_made_flag'
            df, metrics = self._handle_data(**params)
            df['shot_made_flag'] = df['shot_made_flag'].astype(str)
            source = ColumnDataSource(df)
            p2 = figure(width=470, height=460,
                        x_range=[-250, 250],
                        y_range=[422.5, -47.5],
                        min_border=0,
                        x_axis_type=None,
                        y_axis_type=None,
                        outline_line_color=self.bg_color)

            colors = factor_cmap('shot_made_flag', palette=['green', 'red'], factors=['1', '0'])
            p2.scatter(x="loc_x", y="loc_y",
                       source=source,
                       size=10,
                       color=colors,
                       alpha=0.4,
                       line_alpha=0.4)

            self._draw_court(p2, line_width=1)
            p2 = self._style_plot(p2)

            return p2
        except Exception as e:
            return f"<br><br> Plot error: <br> {str(e)}"

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

    def _check_local_cache(self, url):
        '''
        :return:  True/False  if the plot is cached and created within cache time
        '''
        import os.path
        import datetime as dt
        if os.path.exists(self.plot_caching['cache_path'] + '/' + url + '.html'):
            time_created = dt.datetime.fromtimestamp(
                os.path.getctime(self.plot_caching['cache_path'] + '/' + url + '.html'))
            return (dt.datetime.now() - time_created).total_seconds() <= self.plot_caching['cache_time']
        else:
            return False

    def _connect_gcp_bucket(self):
        '''
        :return: creates connection to gcp bucket using big query credentials from settings['data_source']
        '''
        from google.oauth2 import service_account
        from google.cloud import storage

        if self.current_db_source['connection_type'] == 'service_account':
            credentials = service_account.Credentials.from_service_account_file(self.current_db_source['sa_path'])
            bucket_client = storage.Client(
                credentials=credentials,
                project=self.current_db_source['project'],
            )
        elif self.current_db_source['connection_type'] == 'personal_account':
            # personal account ran from identification before
            # gcloud auth application-default login
            bucket_client = storage.Client(
                project=self.current_db_source['project'],
            )

        self.bucket = bucket_client.get_bucket(self.plot_caching['cache_bucket'])

    def _check_gcp_cache(self, url):
        '''
        :return: True/False if the plot is cached or not in the gcp bucket
        '''
        import datetime as dt
        if self.bucket is None:
            self._connect_gcp_bucket()
        path = f"{self.plot_caching['cache_path']}{url}.html"
        blob = self.bucket.blob(path)

        if blob.exists():
            time_created = blob.time_created
            return (dt.datetime.now() - time_created).total_seconds() <= self.plot_caching['cache_time']
        else:
            return False

    def check_plot_cache(self, url):
        '''
        :return: True/False if the plot is cached and is up to date (was created within time specified in self.plot_caching['cache_time']
        If caching is switched off, then returns False and lets code make query, run query and create plot
        '''
        if self.plot_caching['active']:
            cache_dict = {'local': self._check_local_cache,
                          'gcpbucket': self._check_gcp_cache}
            plot_exists = cache_dict[self.plot_caching['cache_storage']](url)
            return plot_exists
        else:
            return False

    def get_cached_plot(self, url):
        '''
        :param url: url of the plot, already checked if its cached
        :return: return plot file
        '''
        cache_dict = {'local': self._get_plot_local,
                      'gcpbucket': self._get_plot_gcp}
        return cache_dict[self.plot_caching['cache_storage']](url)

    def _get_plot_local(self, url):
        with open(f"{self.plot_caching['cache_path']}/{url}.html") as f:
            p = f.read()
            return p

    def _get_plot_gcp(self, url):
        path = f"{self.plot_caching['cache_path']}{url}.html"
        blob = self.bucket.blob(path)
        p = blob.download_as_string()
        return p

