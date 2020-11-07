

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
        self.metrics_txt = kwargs['metrics']
        self.dimensions_txt = kwargs['dimensions']
        self.df_name = kwargs['source']['table']
        self.project = kwargs['project']
        self.schema = kwargs['schema']
        self.possible_calcs = kwargs['source']['possible_calcs']










    def _no_aggr_select(self, **args):
        metrics = args['metrics'].split(';')
        dimensions = args['dimensions'].split(';')

        metrics_txt = ', '.join(metrics)
        if dimensions.__len__() > 0:
            dim_txt = ', '.join(dimensions)
            cm_txt = ', '
        else:
            dim_txt, cm_txt = '', ''

        sql = f"""SELECT {dim_txt}{cm_txt}{metrics_txt}
        FROM {args['project']}.{args['schema']}.{args['df_name']} WHERE 1=1
        """
        return sql

    def _gb_aggr_select(self, **args):
        metrics = args['metrics'].split(';')
        dimensions = args['dimensions'].split(';')

        if dimensions.__len__() > 0:
            dim_txt = ', '.join(dimensions)
            cm_txt = ', '
            gb_dm_txt = f'GROUP BY {dim_txt}'
        else:
            dim_txt, cm_txt, gb_dm_txt = '', '', ''

        for nc in metrics:
            if nc not in calcs:
                colqs.append(f"{args['aggr_type']}{prtn_txt_1}{nc}{prtn_txt_2} AS {nc}")





    def _window_aggr_select(self):
        NotImplementedError


    def _make_query(self, **args):
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
                      'quantiles':self._window_aggr_select}
        sql_base = sql_switch[args['aggr_type']](**args)



        colqs = list()
        for nc in metrics:
            if nc not in calcs:
                colqs.append(f"{args['aggr_type']}{prtn_txt_1}{nc}{prtn_txt_2} AS {nc}")
            else:
                colqs.append(f"{calcs_dict[nc]} AS {nc}")
        num_cols = ','.join(colqs)

        sql = f"""SELECT {rqf_txt} {gb_dim_txt}{cm_txt}{num_cols}
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

    @staticmethod
    def check_key(dict, key):
        if key in dict.keys():
            return True
        else:
            return False