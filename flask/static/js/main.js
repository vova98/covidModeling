function set_date(id) {
    var date = new Date();
    document.getElementById(id).value = date.getFullYear() + '-' + ('0' + (date.getMonth() + 1)).slice(-2) + '-' + ('0' + date.getDate()).slice(-2);
}

function get_graph(city=null, model=null, date=true, field=null) {
    if(!city){
        city = document.getElementById("cities").value;
    }
    var url = `/graph/${city}`;
    if(model){
        var models = new Object()
        for(var key in model) {
            models[key] = document.getElementById(`checkbox_models_${key}`).checked ? 1: 0
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