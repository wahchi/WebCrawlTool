/**
 * Created by wahchi on 17-5-17.
 */
document.body.addEventListener('click',function(e) {
    var xlid = $(e.target).attr('_xlid_');
    var t = $('[_xlid_='+xlid+']');
    var output = new Array();
    output['xlid'] = xlid;
    if (typeof t.attr('src') !== typeof undefined || typeof t.attr('href') !== typeof undefined) {
        output['link'] = t.attr('src') || t.attr('href');
    }
    if (typeof t.text() !== typeof undefined && t.text() !== false) {
        output['text'] = t.text();
    }
    parent.add_con(output);
},true)

