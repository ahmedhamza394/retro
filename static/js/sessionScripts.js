function getQueryParams() {
    let params = new URLSearchParams(window.location.search);
    return {
        session_id: params.get('session_id'),
        session_password: params.get('session_password')
    };
}

let queryParams = getQueryParams();

if (queryParams.session_id != null) {
    localStorage.setItem('session_id', queryParams.session_id);
    console.log('Session ID:', queryParams.session_id);
}

var socket = io();
var sessionId = localStorage.getItem('session_id');

socket.emit('join_session', { session_id: sessionId });

socket.on('message_added', function(data) {
    showMessages();
});

socket.on('user_count', function(data) {
    document.getElementById('user-count').textContent = 'Users connected: ' + data.count;
});

function addMessage(category) {
    var message = document.getElementById('message-' + category).value;
    fetch('/add_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: sessionId,
            message: message,
            category: category
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'Message added') {
            console.log('Message added successfully');
            document.getElementById('message-' + category).value = '';
        } else {
            console.log('Error adding message:', data.error);
        }
    });
}

function leaveSession() {
    socket.emit('leave_session', { session_id: sessionId });
    localStorage.removeItem('session_id');
    window.location.href = '/';
}

function showMessages() {
    fetch('/get_messages/' + localStorage.getItem('session_id'))
        .then(response => response.json())
        .then(messages => {
            var happyList = document.getElementById('glad-list');
            var sadList = document.getElementById('sad-list');
            var madList = document.getElementById('mad-list');
            
            happyList.innerHTML = ''; // Clear the current list
            sadList.innerHTML = '';
            madList.innerHTML = '';

            messages.forEach(function(message) {
                var newItem = document.createElement('li');
                newItem.textContent = message.message;
                
                if (message.category === 'glad') {
                    happyList.appendChild(newItem);
                } else if (message.category === 'sad') {
                    sadList.appendChild(newItem);
                } else if (message.category === 'mad') {
                    madList.appendChild(newItem);
                }
            });
        });
}

window.onload = function() {
    showMessages();
}
