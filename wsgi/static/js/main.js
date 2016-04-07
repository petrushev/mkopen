function get_query(){
    if (location.search=='') {return {};}
    var parts = location.search.substring(1) .split('&');
    var q = {};
    $.each(parts, function(_, item) {
        item = item.split('=');
        q[item[0]] = item[1];
    });
    return q;
}

function prepare_query(q) {
    var query = '';
    $.each(q, function(key, value) {
        query = query + key + '=' + encodeURIComponent(value) + '&';
    });
    query = query.substring(0, query.length-1);
    return query;
}

function getCachedJson(url, callback) {
    var body = $('body');
    var cache = body.data(url);
    if (cache) {
        callback(cache);
    } else {
        $.getJSON(url, {}, function(json) {
            body.data(url, json);
            callback(json);
        });
    }
}

$(document).ready(function(){
  $('a.orig_url').click(function(){
    $(this).hide();
    $('span#orig_url').show();
    return false;
  });
});
