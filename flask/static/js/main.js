function set_date(id) {
    var date = new Date();
    document.getElementById(id).value = date.getFullYear() + '-' + ('0' + (date.getMonth() + 1)).slice(-2) + '-' + ('0' + date.getDate()).slice(-2);
}

function hashCode(str) { // java String#hashCode
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

var chart = null

function parse_json_to_graph(data, field=null){
    var datasets = [];
    for(var key in data){
        for(var fi in field){
            if(field[fi]==1){
                var datas = []
                for(var item in data[key]){
                    var dat = {
                        x: new Date(data[key][item]['date'].replace(/(\d+).(\d+).(\d+)/, "$2/$1/$3")),
                        y: data[key][item][fi]
                    }
                    datas.push(dat)
                }
                var legend = key + ' ' + fi
                var dataSeries = {data: datas,
                                  label: legend, 
                                  fill: false, 
                                  backgroundColor: intToRGB(hashCode(legend)),
                                  borderColor: intToRGB(hashCode(legend))};
                datasets.push(dataSeries)
            }
        }
    }

    if(chart){
        chart.destroy()
    }

    chart = new Chart(document.getElementById("graphJS"), {
        type: 'line',
        data: {
            datasets: datasets,
        },
        options: {
            scales: {
              xAxes: [{
                type: 'time'
              }]
            },
            tooltips: {
                mode: 'label',
            },
            hover: {
                mode: 'label'
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
        var date = new Date(document.getElementById("date").value);
        url = url + `&date=${JSON.stringify(date.toLocaleDateString('ru'))}`;
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

function get_graph(city=null, model=null, date=true, field=null) {
    if(!city){
        city = document.getElementById("cities").value;
    }
    var url = `/graph/${city}`;
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
        var date = new Date(document.getElementById("date").value);
        url = url + `&date=${JSON.stringify(date.toLocaleDateString('ru'))}`;
    }
    var width = document.getElementById("graph_field").offsetWidth;
    var hight = document.getElementById("graph_field").offsetHeight;

    url = url + `&width=${width}&hight=${hight}`;

    url = url.replace('&', '?')
    
    const http = new XMLHttpRequest();
    http.open("GET", url, true);
    http.onreadystatechange = function () {
        if(http.readyState === XMLHttpRequest.DONE && http.status === 200) {
            document.getElementById("graph").src = http.responseText;
        };
    }
    http.send();
}