import logging

class SqlBuilder:
    '''
    SQl builder class should receive information about:
        - metrics
        - dimensions
        - table name
        - project
        - schema
        - required fields
        - calculations
        - filters
        - limits
    '''

    def __init__(self, **kwargs):
        self.metrics = kwargs['metrics'].split(';')
        self.dimensions = kwargs['dimensions'].split(';')
        self.source = kwargs['source']
        self.aggr_type = kwargs['aggr_type']

        self.add_filters = kwargs['add_filters']
        self.filters = kwargs['filters']
        self.having = kwargs['having']
        self.show_top_n = kwargs['show_top_n']

        self.data_source = kwargs['data_source']
        self.meta_source = kwargs['meta_source']

        self.project = self.meta_source['project']
        self.file_format = self.meta_source['file_format']
        self.schema = self.meta_source['schema']

        self.df_name = None
        self.calculations = None

        self.req_fields = None
        if 'req_fields' in kwargs.keys():
            self.req_fields = kwargs['req_fields']


    def _no_aggr_select(self, **args):
        select_list = list()

        if (self.dimensions.__len__() > 0) & (self.dimensions != ['']):
            dim_txt = ', '.join(self.dimensions)
            select_list.append(dim_txt)

        if (self.dimensions.__len__() > 0) & (self.metrics != ['']):
            metrics_txt = ', '.join(self.metrics)
            select_list.append(metrics_txt)

        # required fields
        if self.req_fields is not None:
            select_list.append(self.req_fields)

        where_str = self._gen_where_statements()
        ord_txt = self._gen_order_statement()

        select_txt = ','.join(select_list)
        sql = f"""SELECT {select_txt} FROM {self.project}.{self.schema}.{self.df_name} 
WHERE 1=1 {where_str} {ord_txt}"""
        return sql

    def _gb_aggr_select(self, **args):
        select_list = list()
        gb_txt = ''
        metric_queries = list()
        hv_txt = ''

        if (self.dimensions.__len__() > 0) & (self.dimensions != ['']):
            dim_txt = ', '.join(self.dimensions)
            select_list.append(dim_txt)
            gb_txt = f'GROUP BY {dim_txt}'
            hv_txt = self._gen_having_statement(gb_txt)

        for nc in self.metrics:
            if nc not in self.calculations:
                metric_queries.append(f"{self.aggr_type}({nc}) AS {nc}")

        metrics_txt = ','.join(metric_queries)
        select_list.append(metrics_txt)
        select_txt = ','.join(select_list)

        where_str = self._gen_where_statements()
        ord_txt = self._gen_order_statement()
        sql = f"""SELECT {select_txt} FROM {self.project}.{self.schema}.{self.df_name} 
WHERE 1=1 {where_str} {gb_txt} {hv_txt} {ord_txt}"""

        return sql


    def _window_aggr_select(self):
        return NotImplementedError()


    def make_query(self, **args):
        # read table name
        self.df_name = self.data_source[self.source]['table']

        # calculations
        if self.check_key(self.data_source[self.source], 'calculations'):
            possible_calcs = self.data_source[self.source]['calculations']
            calcs_dict = dict((key, d[key]) for d in possible_calcs for key in d)
            self.calculations = list(calcs_dict.keys())

        sql_switch = {'':   self._no_aggr_select,
                      'sum': self._gb_aggr_select,
                      'mean': self._gb_aggr_select,
                      'count': self._gb_aggr_select,
                      'quantiles': self._window_aggr_select}
        sql = sql_switch[self.aggr_type](**args)

        return sql


    def _gen_where_statements(self):
        where_str = ''
        for k, v in self.filters.items():
            if k in self.add_filters:
                if ';' in v:
                    v2 = "('" + v.replace(";", "','") + "')"
                    wstr = f" AND CAST({k} AS STRING) IN {v2} "
                else:
                    wstr = f" AND CAST({k} AS STRING) = '{v}' "
                where_str += wstr
            else:
                pass
        return where_str

    def _gen_having_statement(self, gb_txt):
        hv_txt = ''
        if (gb_txt != '') & (self.having != ''):
            hv_txt = f'HAVING {self.having} '
        return hv_txt

    def _gen_order_statement(self):
        ord_txt = ''
        if (self.metrics.__len__() > 0) & (int(self.show_top_n) > 0):
            ord_txt = f" ORDER BY {self.metrics[0]} DESC LIMIT {self.show_top_n} "
        return ord_txt

    @staticmethod
    def check_key(dict, key):
        if key in dict.keys():
            return True
        else:
            return False