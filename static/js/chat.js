var text_box = '<div class="card-panel right" style="width: 75%; position: relative">' +
        '<div style="position: absolute; top: 0; left:3px; font-weight: bolder" class="title">{sender}</div>' +
        '{message}' +
        '</div>';

function scrolltoend() {
    $('#board').stop().animate({
        scrollTop: $('#board')[0].scrollHeight
    }, 800);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie('csrftoken');

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function send(sender, receiver, message) {
    $.post('/api/messages/', {sender: sender, receiver: receiver, message: message}, function (data) {
        console.log(data);
        var box = text_box.replace('{sender}', "You");
        box = box.replace('{message}', message);
        $('#board').append(box);
        scrolltoend();
    })
}

function receive() {
    $.get('/api/messages/'+ sender_id + '/' + receiver_id, function (data) {
        console.log(data);
        if (data.length !== 0)
        {
            for(var i=0;i<data.length;i++) {
                console.log(data[i]);
                var box = text_box.replace('{sender}', data[i].sender);
                box = box.replace('{message}', data[i].message);
                box = box.replace('right', 'left blue lighten-5');
                $('#board').append(box);
                scrolltoend();
            }
        }
    })
}
