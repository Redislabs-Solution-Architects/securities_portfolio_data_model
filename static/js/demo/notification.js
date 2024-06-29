$(document).ready(function() {

    notification()

    function notification() {
        const socket = new WebSocket('ws://' + location.host + '/notification');
        socket.addEventListener('message', ev => {
            $('#ulid li.target div.target').html('<h6 class="dropdown-header">Notifications</h6>')
            data = JSON.parse(ev.data)
            $('#notifCountId').text(data.count)
            messages = data.messages
            messages.forEach(function(msg) {
                var anchor = $('#template').clone().removeClass('template').show();
                anchor.find('.alertmessage').text(msg);
                $('#ulid li.target div.target').append(anchor);
            });
        });
    }

});
