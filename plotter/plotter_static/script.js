
$("document").ready(function(){

    // read windows side so you know how many plots you can put there
    width = (window.innerWidth > 0) ? window.innerWidth : screen.width;
    var dash_grid = document.getElementById('dash_grid');
    dash_grid.style.width = width - 200;

    window.addEventListener("resize", function(event) {
        var dash_grid = document.getElementById('dash_grid');
        dash_grid.style.width = document.body.clientWidth - 200;
    });




    get_setup(what='settings');
    // global variables
    f_vars = {};
    query_logger = {};
    query_logger_list = [];
    var metrics_choices = new Choices('#metrics',
    {   'maxItemCount': -1,
        'itemSelectText': '',
        'placeholder': false,
        'placeholderValue': ''
    });

    // dictionary of functions to avoid if elses
    setup_handler_dict = {'settings':     handle_settings,
                          'filters':      handle_filters,
                          'data_sources': handle_data_sources,
                          'filter_info':  handle_filter_info};

    // handle filter_info - creating new filter
      function handle_filter_info(x){
        var nice_name = x['name'];
        var type = x['type'];
        var id = x['value'];
        var options = x['options'];
        var operators = x['operators'];

        var f_window = document.getElementById('add_filters_window_list');
        f_window.insertAdjacentHTML('beforeend', `<div class="row selected_filter_area" id="sfa_${filter_name}"> <button id="rm_${id}" class="rm_button"> X </button></div>`);

        var rm_button = document.getElementById(`rm_${id}`);
        rm_button.addEventListener('click', rm_filter, false );
        var f_div = document.getElementById(`sfa_${filter_name}`);

        if(['text','number'].indexOf(type) >= 0) {
            f_div.insertAdjacentHTML('beforeend', `<select id="ops_${id}" class="operator_selector">`);
            var ops_select = document.getElementById(`ops_${id}`);
            $.each(operators, function() {
                    ops_select.append('<option value="'+this+'"> '+this+' </option>');
            });
        };
        if(type === 'select'){
            f_div.insertAdjacentHTML('beforeend', `<select id="${id}" class="filter_value">`);
            var select = document.getElementById(id);
            add_options(select, options);
            select.insertAdjacentHTML('beforeend', `<label for="${id}" style="margin-left: 1px;" >${nice_name}</label>`);
            select.addEventListener('change', handle_new_input, false);
        } else if (type === 'choices'){

            f_div.insertAdjacentHTML('beforeend', `<select id="${id}" class="filter_value" multiple>`);
            var select = document.getElementById(id);
            add_options(select, options);
            select.insertAdjacentHTML('beforeend', `<label for="${id}" style="margin-left: 1px;" >${nice_name}</label>`);
            select.addEventListener('change', handle_new_input, false);
                var metrics_choices = new Choices(`#${id}`,
                    {   'maxItemCount': -1,
                        'itemSelectText': '',
                        'placeholder': false,
                        'placeholderValue': ''
                    }
                );

        } else if (type === 'number'){
            f_div.insertAdjacentHTML('beforeend', `<input type="number" id="${id}" class="filter_value" min=${options.min} max=${options.max} style="margin-left: 25px;">`);
            var nmb = document.getElementById(id);
            nmb.insertAdjacentHTML('beforeend', `<label for="${id}" style="margin-left: 1px;" >${nice_name}</label>`);
            nmb.addEventListener('change', handle_new_input, false);
        } else if (type === 'text'){
            f_div.insertAdjacentHTML('beforeend', `<input type="text" id="${id}" class="filter_value" style="margin-left: 25px;">`);
            var txt = document.getElementById(id);
            txt.insertAdjacentHTML('beforeend', `<label for="${id}" style="margin-left: 1px;" >${nice_name}</label>`);
            txt.addEventListener('change', handle_new_input, false);
        } else if (type === 'radio'){
            f_div.insertAdjacentHTML('beforeend', `<div class="form-check form-check-inline filter_value" id="${id}">`);
            var radio = document.getElementById(id);
            options.forEach(function(x, index){
                radio.insertAdjacentHTML('beforeend', `<input class="form-check-input" type="radio" name="${x}" id="${x}${index}" value="${x}"> <label class="form-check-label" for="${x}${index}" style="margin-right: 10px;">${x}</label>`);
            });
            radio.addEventListener('change', handle_new_input, false);
        } else if (type === 'checkbox'){
            f_div.insertAdjacentHTML('beforeend', `<div class="form-check form-check-inline filter_value" id="${id}">`);
            var check = document.getElementById(id);
            options.forEach(function(x, index){
                check.insertAdjacentHTML('beforeend', `<input class="form-check-input" type="${type}" name="${x}" id="${x}${index}" value="${x}"> <label class="form-check-label" for="${x}${index}" style="margin-right: 10px;">${x}</label>`);
            });
            check.addEventListener('change', handle_new_input, false);
        };
        let filters_select = document.querySelector('#dim_filters');
        for (var i=0; i< filters_select.length; i++) {
            if (filters_select.options[i].value == id)
                filters_select.remove(i);
            };
    };

    // handle settings info
    function handle_settings(x){
        let root = document.documentElement;
        root.style.setProperty('--bg-color', x['bg_color']);
        root.style.setProperty('--f-color', x['f_color']);
        root.style.setProperty('--filters-bg-color', x['filters_bg_color']);
        root.style.setProperty('--plot-width', x['plot_width']);
        root.style.setProperty('--plot-height', x['plot_height']);

    };

    // handle filters info
    function handle_filters(x){
        let filters_select = document.getElementById('dim_filters');
        let filters = Object.keys(x);
        add_options(filters_select, filters);
    };

    function close_filter() {
        document.getElementById("filters_grid").style.display = "none";
        document.getElementById("open_menu").style.display = "block";
        document.getElementById("dash_content").style.paddingLeft = "20px";
        document.getElementById("dash_content").style.paddingTop = "20px";
     };

    function open_filter() {
        document.getElementById("filters_grid").style.display = "block";
        document.getElementById("open_menu").style.display = "none";
        document.getElementById("dash_content").style.paddingLeft = "0px";
        document.getElementById("dash_content").style.paddingTop = "0px";
    };

    var filters_close_btn = document.getElementById("filters_close");
    filters_close_btn.addEventListener('click', close_filter);
    var open_menu_btn = document.getElementById("open_menu");
    open_menu_btn.addEventListener('click', open_filter);


    // handle info about data sources
    function handle_data_sources(x){
        try{
            let dimensions = x['dimensions'];
            let metrics = x['metrics'];
            let calculations = x['calculations'];
            let fixed_filters = x['fixed_filters'];
            let plots = x['plots'];
            let table = x['value'];
            f_vars['source'] = table;
            f_vars['fixed_filters'] = fixed_filters;

            //remove old filters
            var add_filter_list = document.getElementById('add_filters_window_list');

              for(i = 0; i < add_filter_list.childNodes.length; i++){
                   if(typeof add_filter_list.childNodes[i].id !== "undefined"){
                        var f_id = add_filter_list.childNodes[i].id.replace('sfa_','');
                        delete f_vars[f_id];
                   };
                };
            add_filter_list.innerHTML = "";

            // add plots
            let plots_select = document.getElementById('plot_type');
            add_options(plots_select, plots);

            // add new filters
            let dimensions_select = document.getElementById('dimensions');
            add_options(dimensions_select, dimensions);

            // feeding choices.js metrics
            metrics_choices.clearStore();

            if(typeof calculations !== "undefined"){
                var calcs = calculations.map(function(x){ return Object.keys(x)[0]; });
                var all_choices = metrics.concat(calcs);
            } else {
                var all_choices = metrics;
            }
            var metrics_dict = [];
            all_choices.forEach(element => metrics_dict.push({value: element, label: element, disabled: false }));
            metrics_choices.setChoices(metrics_dict);

            // filters
            get_setup(what='filters', data_source=table);

        } catch (error) {
            alert(error);
        };
    };

    // create new option for select
    function create_select_option(ddl, option){
        var opt = document.createElement('option');
        opt.value = option;
        opt.text = option;
        ddl.options.add(opt);
    };

    // add new options for select (remove old ones first)
    function add_options(ddl, options_arr) {
        for (i = ddl.length - 1; i >= 0; i--) {
            ddl.remove(i);
        };
       for (i = 0; i < options_arr.length; i++) {
           create_select_option(ddl, options_arr[i]);
       };
    };


    // getting yamls based on promises
    function get_setup(what, data_source='', filter_name=''){
        axios.post(`/get_setup/${what}?data_source=${data_source}&filter_name=${filter_name}`)
        .then((response) => {
            setup_handler_dict[what](response['data']);
        }, (error) => {
          console.log(error);
        });
    };

   // catching ds_select value updates
    const ds_select = document.querySelector('#ds');
    let ds_value = ds_select.value;
    ds_select.addEventListener('change', (event) => {
          let ds_value = ds_select.value;
          get_setup(what='data_sources', data_source = ds_value);
    });

    // initial setup
    get_setup(what='data_sources', data_source = ds_select.value);

    // function for making unique plot id
    function makeid(length) {
        var result = '';
        var chars = 'ABCDEFGHIJKLMNOPQRSTUWZXabcddefghijklmnopqrstuwzx0123456789';
        var charlength = chars.length;
        for (var i = 0; i < length; i++){
            result += chars.charAt(Math.floor(Math.random() * charlength));
        }
        return result;
     }

    function handle_new_input(v){
          var target = v.target;
          var target_class = target.className;

          if(target_class.indexOf('choices__input') > 0){
            // handle choices class input
                var ch_values = [];
                var target_options_n = target.options.length;;
                for (var i = 0; i < target_options_n; i++){
                    ch_values.push(target.options[i].value);
                };
                var v_value = ch_values.join(";");
                var v_id = target.id;
                f_vars[v_id] = v_value;

          } else if(target_class.indexOf('form-check-input') > 0 | target_class === 'form-check-input') {
                var v_id = target.parentNode.id;
                var ch_values = [];
                var childs = document.getElementById(v_id).children;
                for (var i = 0; i < childs.length; i++){
                    if(childs[i].className == 'form-check-input'){
                        if(childs[i].checked){
                            ch_values.push(childs[i].value);
                        };
                    };
                };
                var v_value = ch_values.join(";");
                f_vars[v_id] = v_value;
          } else {
                var v_value = target.value;
                var v_id = target.id;
                f_vars[v_id] = v_value;
          };
          console.log(f_vars);
    };

    // loop through main filters and assign variable:
     var main_filters = document.querySelectorAll(".main_filter");
     function assign_f_var(v){
          var v_type = v.type;
          var v_value = v.value;
          var v_id = v.id;
          if(['select-one','number'].indexOf(v_type) >= 0){
               f_vars[v_id] = v_value;
          } else if (v_type === 'radio'){
               f_vars[v_id] = $(`input[name="${v_value}"]:checked`).val();
          } else if (v_type === 'checkbox'){
               f_vars[v_id] = $(`input[name="${v_value}"]:checked`).val();
          }else if (v_type === 'select-multiple'){
               f_vars[v_id] = v.value;
          };
          v.addEventListener('change', handle_new_input, false);
     };
    main_filters.forEach(element => assign_f_var(element));

    // handle additional filters here
    var dim_filters = document.querySelector("#dim_filters");
    dim_filters.addEventListener('change', open_new_filter, false);

    function open_new_filter(v){
       var v_value = v.target.value;
       get_setup(what='filter_info', data_source='', filter_name=v_value);
    };

    // remove filter button logic:
    function rm_filter(x){
        var filter_id =  x.target.id;
        var filter_name = filter_id.replace('rm_','');
        var sfa = document.getElementById(`sfa_${filter_name}`);
        sfa.remove();
        let filters_select = document.getElementById('dim_filters');
        create_select_option(filters_select, filter_name);
        delete f_vars[filter_name];
    };

    function rm_having(x){
        var filter_id =  x.target.id;
        var filter_name = filter_id.replace('rm_','');
        var sfa = document.getElementById(`sfa_${filter_name}`);
        sfa.remove();
        let filters_select = document.getElementById('having_metrics');
        create_select_option(filters_select, filter_name);
        delete f_vars[filter_name];
    };


    function build_title(){
        var f_texts = [];
        for (const [key, value] of Object.entries(f_vars)) {
           if(['show_top_n', 'aggr_type', 'dimensions', 'plot_type', 'ds', 'metrics', 'source', 'fixed_filters', 'having'].indexOf(key) < 0){
             var f_txt = `${key}: ${value}`;
             f_texts.push(f_txt);
           };
        };
        if(f_vars['fixed_filters'] !=''){
            f_texts.push(f_vars['fixed_filters'].replaceAll('=',': ').replaceAll('&', ' '))
        };

        if(f_vars['having'] == ''){
            var hv_txt = '';
        } else {
            var hv_txt = `HAVING: ${f_vars['having'] }`;
        };

        if(f_vars['dimensions'] == ''){
            var dim_txt = '';
        } else {
            var dim_txt = `BY ${f_vars['dimensions'] }`;
        };


        var f_text = f_texts.join(" ");
        var plot_title = `${f_vars['aggr_type']} ${f_vars['metrics']} ${dim_txt} ${hv_txt} ${f_text}`.toUpperCase();
        return plot_title
    }

    function adding_plot(){
        document.body.style.cursor = 'wait';
        var plot_info = {};
        var q_args = '';
        f_vars['having'] = document.getElementById('having_metrics').value;

        if (f_vars['metrics'] === ''){
            alert('Please pick at least one metric');
        }
          else {
            for (const [key, value] of Object.entries(f_vars)) {
                if(['plot_type','fixed_filters'].indexOf(key) < 0){
                    q_args = q_args+ '&'+key+'='+value;
                }
            };
            var plot_id = makeid(5);
            plot_info['plot_id'] = plot_id;
            var url_plot = `plot/${f_vars['plot_type']}?`+q_args+f_vars['fixed_filters'];
            plot_info['url_plot'] = url_plot;
            //check if given plot doesnt exist already:
            if (Object.values(query_logger_list).indexOf(url_plot) >= 0){
                document.body.style.cursor = 'default';
                alert("Given plot already exists");
            } else {
               var plot_title = build_title();
               plot_info['plot_title'] = plot_title;
               jQuery.post(url_plot)
                 .done(function( data ) {
                  $(`<div class="col-xs-1 plot_frame" id="${plot_id}"><div class = "plot_menu"><a class="plot_title">${plot_title}</a><button class="rm_plot" id="bpr_${plot_id}"> X </button><a class="button_link" href="${url_plot}" target="_blank">O</a> </div> ${data} </div>`).appendTo('#dash_grid');
                  query_logger[plot_id] = plot_info;
                  query_logger_list[plot_id] = url_plot;
                })
                .fail(function() {
                    alert('This query wont work');
                })
                 .always(function() {
                   document.body.style.cursor = 'default';
                });
            };
        };
    };

    var add_plot_btn = document.getElementById('add_plot');
    add_plot_btn.addEventListener('click', adding_plot);


    // remove plot button
    $(document).on('click','.rm_plot', function(event){
        event.stopPropagation();
        event.stopImmediatePropagation();
        var button_id =  this.id;
        var plot_id = button_id.replace('bpr_','');
        $('#'+plot_id).remove();
        delete query_logger[plot_id];
        delete query_logger_list[plot_id];
        }
    );


    // filters window modal code:
    var modal = document.getElementById("filters_window");
    var btn = document.getElementById("open_filters");
    var span = document.getElementsByClassName("close")[0];
    btn.onclick = function() {
      modal.style.display = "block";
    };
    span.onclick = function() {
      modal.style.display = "none";
    };
    window.onclick = function(event) {
      if (event.target == modal) {
        modal.style.display = "none";
      }
    };

    // save view function
    function save_view(){
        var v_name = prompt("Please enter the view name", "view name...");
        axios.post(`/save_view`, data={query_log: query_logger, view_name: v_name})
        .then((response) => {
            console.log('view saved');
        }, (error) => {
          console.log(error);
        });
    };
    var save_view_btn = document.getElementById('save_view');
    save_view_btn.addEventListener('click', save_view);

    function list_views(){
        axios.post(`/list_views`)
        .then((response) => {
            document.getElementById('view_select_div').style.display = 'block';
            var view_select = document.getElementById('view_select');
            var view_options =  response.data.split(';');
            view_options.splice(0, 0, "");
            add_options(view_select, view_options);
        }, (error) => {
          console.log(error);
        });
    };
    var list_view_btn = document.getElementById('list_view');
    list_view_btn.addEventListener('click', list_views);

    function load_view(){
         var v_name = document.getElementById('view_select').value;
         document.getElementById('view_select_div').style.display = 'none';
         axios.post(`/load_view`, data={view_name: v_name})
        .then((response) => {
            var query_log = response.data;
            //for each plot_info in query_log run load_from_logger function
            for (const [key, value] of Object.entries(query_log)) {
                load_from_logger(value);
            };
        }, (error) => {
          console.log(error);
        });
    };

    var load_view_btn = document.getElementById('load_view');
    load_view_btn.addEventListener('click', load_view);

    function load_from_logger(x){
        console.log(x);
        var plot_info = {};
        plot_info['plot_id'] = x['plot_id'];
        plot_info['plot_title'] = x['plot_title'];
        plot_info['url_plot'] = x['url_plot'];
        jQuery.post(x['url_plot'])
           .done(function( data ) {
            $(`<div class="col-xs-1 plot_frame" id="${x['plot_id']}"><div class = "plot_menu"><a class="plot_title">${x['plot_title']}</a><button class="rm_plot" id="bpr_${x['plot_id']}"> X </button><a class="button_link" href="${x['url_plot']}" target="_blank">O</a> </div> ${data} </div>`).appendTo('#dash_grid');
            query_logger[x['plot_id']] = plot_info;
            query_logger_list[x['plot_id']] = x['url_plot'];
        });
    };

});


