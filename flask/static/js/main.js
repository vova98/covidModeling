function set_date(id, string=null) {
    var date = new Date();
    if(string){
       date = new Date(string.replace(/(\d+).(\d+).(\d+)/, "$2/$1/$3"));
    }
    document.getElementById(id).value = date.getFullYear() + '-' + ('0' + (date.getMonth() + 1)).slice(-2) + '-' + ('0' + date.getDate()).slice(-2);
}

function hashCode(str) {
    var hash = 0;
    for (var i = 0; i < str.length; i++) {
       hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return hash;
} 

function intToRGB(i){
    var c = (i & 0x00FFFFFF)
        .toString(16)
        .toUpperCase();

    return "#"+"00000".substring(0, 6 - c.length) + c;
}

function parse_json_to_graph(data, field=null) {
    var datasets = [];
    for(var key in data){
        for(var fi in field){
            if(field[fi]==1){
                var datas = []
                for(var item in data[key]){
                    var date = new Date(data[key][item]['date'].replace(/(\d+).(\d+).(\d+)/, "$2/$1/$3"))
                    var date_from = new Date(document.getElementById("plot_date_from").value)
                    var date_to = new Date(document.getElementById("plot_date_to").value)
                    if(date_from <= date && date <= date_to){
                        var dat = {
                            x: date,
                            y: data[key][item][fi]
                        }
                        datas.push(dat)
                    }
                }
                var legend = key + ' ' + fi
                var dataSeries = {data: datas,
                                  label: legend, 
                                  fill: false, 
                                  backgroundColor: intToRGB(hashCode(legend)),
                                  borderColor: intToRGB(hashCode(legend)), 
                                  pointHitRadius: -1, 
                                  pointRadius: 3};
                datasets.push(dataSeries)
            }
        }
    }

    if(window.chart){
        window.chart.destroy()
    }

    window.chart = new Chart(document.getElementById("graphJS"), {
        type: 'line',
        data: {
            datasets: datasets,
        },
        options: {
            tooltips: {
                mode: 'x',
                intersect: false,
            },
            hover: {
                mode: 'x',
                intersect: false
            },
            scales: {
                xAxes: [{
                    type: 'time',
                    distribution: 'series',
                    ticks: {
                      min: 8,
                      max: 16,
                      stepSize: 1,
                      fixedStepSize: 1,
                    }
                }]
            },
        }
    });
}

function plot_graph_from_json(city=null, model=null, date=true, field=null) {
    if(!city){
        city = document.getElementById("cities").value;
    }
    var url = `/json/${city}`;
    if(model){
        var models = new Object()
        for(var key in model) {
            models[key] = new Object()
            models[key]['use'] = document.getElementById(`checkbox_models_${key}`).checked ? 1: 0
            models[key]['parameters'] = new Object()

            for(var par in model[key]['parameters']){
                models[key]['parameters'][par] = new Object()
                if(model[key]['parameters'][par]['type'] == 'choise'){
                    for(var val in model[key]['parameters'][par]['values']){
                        if(document.getElementById(`checkbox_models_${key}_params_${par}_${model[key]['parameters'][par]['values'][val]}`).checked){
                            models[key]['parameters'][par] = model[key]['parameters'][par]['values'][val]
                        }
                    }
                }else if(model[key]['parameters'][par]['type'] == 'continues'){
                    models[key]['parameters'][par] = document.getElementById(`models_${key}_params_${par}`).value
                }
            }
        }
        
        url = url + `&models=${JSON.stringify(models)}`;
    }
    if(field){
        var fields = new Object()
        for(var key in field) {
            fields[key] = document.getElementById(`checkbox_fields_${key}`).checked ? 1: 0
        }
        
        url = url + `&fields=${JSON.stringify(fields)}`;
    }
    if(date){
        var tmp_predict_date_to = new Date(document.getElementById("predict_date_to").value)
        var tmp_use_date_from = new Date(document.getElementById("use_date_from").value)
        var tmp_use_date_to = new Date(document.getElementById("use_date_to").value)

        var date = {
            predict_date_to: tmp_predict_date_to.toLocaleDateString('ru'),
            use_date_from: tmp_use_date_from.toLocaleDateString('ru'),
            use_date_to: tmp_use_date_to.toLocaleDateString('ru'),
        };

        url = url + `&date=${JSON.stringify(date)}`;
    }

    url = url.replace('&', '?')
    
    const http = new XMLHttpRequest();
    http.open("GET", url, true);
    http.onreadystatechange = function () {
        if(http.readyState === XMLHttpRequest.DONE && http.status === 200) {
            parse_json_to_graph(JSON.parse(http.responseText), fields)
        };
    }
    http.send();
}

function update_data() {
    const url = '/update';
    const http = new XMLHttpRequest();
    http.open("GET", url, true);
    http.send();
}