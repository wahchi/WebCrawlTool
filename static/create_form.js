/**
 * Created by wahchi on 17-6-15.
 */
/**
 * 模拟post提交
 */
function createForm(params, url) {
    var tempform = document.createElement("form");
    tempform.action = url;
    tempform.method = 'post';

    for(i in params) {
        var opt = document.createElement("input");
        opt.name = i;
        opt.value = params[i]
        tempform.appendChild(opt)
    }
    var opt = document.createElement('input');
    opt.type = 'submit';
    tempform.appendChild(opt);
    document.body.appendChild(tempform);
    tempform.submit();
    document.body.removeChild(tempform);

}