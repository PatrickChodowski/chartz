

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
        self.df_name = kwargs['source']['table']
        self.project = kwargs['project']
        self.schema = kwargs['schema']
        self.possible_calcs = kwargs['source']['possible_calcs']
        self.filters = kwargs['filters']
        self.add_filters = kwargs['add_filters']
        self.having = kwargs['having']
        self.show_top_n = kwargs['show_top_n']
        self.data_sources = kwargs['data_sources']

    def _no_aggr_select(self, **args):
        select_txt = ''

        if self.dimensions.__len__() > 0:
            dim_txt = ', '.join(self.dimensions)
            select_txt += dim_txt
            select_txt += ','

        if self.metrics.__len__() > 0:
            metrics_txt = ', '.join(self.metrics)
            select_txt += metrics_txt

        where_str = self._gen_where_statements()
        ord_txt = self._gen_order_statement()

        sql = f"""SELECT {select_txt} FROM {args['project']}.{args['schema']}.{args['df_name']} 
WHERE 1=1 {where_str} {ord_txt}"""
        return sql

    def _gb_aggr_select(self, **args):
        select_txt = ''
        gb_txt = ''
        metric_queries = list()
        hv_txt = ''

        if self.dimensions.__len__() > 0:
            dim_txt = ', '.join(self.dimensions)
            select_txt += dim_txt
            select_txt += ','
            gb_txt = f'GROUP BY {dim_txt}'
            hv_txt = self._gen_having_statement(gb_txt)

        for nc in self.metrics:
            if nc not in args['calcs']:
                metric_queries.append(f"{args['aggr_type']}({nc}) AS {nc}")

        metrics_txt = ','.join(metric_queries)
        select_txt += metrics_txt

        where_str = self._gen_where_statements()
        ord_txt = self._gen_order_statement()
        sql = f"""SELECT {select_txt} FROM {args['project']}.{args['schema']}.{args['df_name']} 
WHERE 1=1 {where_str} {gb_txt} {hv_txt} {ord_txt}"""

        return sql


    def _window_aggr_select(self):
        return NotImplementedError()


    def make_query(self, **args):
        # read table name
        df_name = self.data_sources[args['source']]['table']
        args['df_name'] = df_name

        # calculations
        if self.check_key(self.data_sources[args['source']], 'calculations'):
            possible_calcs = self.data_sources[args['source']]['calculations']
            calcs_dict = dict((key, d[key]) for d in possible_calcs for key in d)
            calcs = list(calcs_dict.keys())
        else:
            calcs = list()

        # required fields
        if self.check_key(self.data_sources[args['source']], 'req_fields'):
            req_fields = self.data_sources[args['source']]['req_fields']
            # remove from req fields if given fields is already in dimensions or metrics:
            req_fields2 = [rq for rq in req_fields if (rq not in args['metrics']) & (rq != args['dimensions'])]
            rqf_txt = ','.join(req_fields2) + ','
        else:
            rqf_txt = ''

        sql_switch = {'':   self._no_aggr_select,
                      'sum': self._gb_aggr_select,
                      'mean': self._gb_aggr_select,
                      'quantiles': self._window_aggr_select}
        sql = sql_switch[args['aggr_type']](**args)

        return sql


    def _gen_where_statements(self):
        where_str = ''
        for k, v in self.filters:
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
        if (self.metrics.__len__() > 0) & (self.show_top_n > 0):
            ord_txt = f" ORDER BY {self.metrics[0]} DESC LIMIT {self.show_top_n} "
        return ord_txt

    @staticmethod
    def check_key(dict, key):
        if key in dict.keys():
            return True
        else:
            return False