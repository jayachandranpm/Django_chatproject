function scrolltoend() {
    $('#board').stop().animate({
        scrollTop: $('#board')[0].scrollHeight
    }, 800);
}

function send(sender_username, receiver_username, message_text) {
    // Note: sender_username is current_username, receiver_username is the user being chatted with.
    // The MessageSerializer expects usernames for sender and receiver.
    $.post('/api/messages/', JSON.stringify({ sender: sender_username, receiver: receiver_username, message: message_text }), function (data) {
        // Message is sent. Clear input and scroll.
        // We will rely on the receive function to display the message with server-generated timestamp.
        $('#id_message').val(''); // Clear the input field
        scrolltoend(); // Scroll to end might be premature if receive is slow, but often okay.
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Error sending message:", textStatus, errorThrown, jqXHR.responseText);
    });
}

function receive() {
    // chat_sender_id is the other user's ID, chat_receiver_id is the current user's ID.
    // The message_list API endpoint is designed to fetch messages for a specific pair,
    // marking them as read. It seems to expect sender/receiver IDs in a specific order
    // for its unread message logic, but the view message_view fetches both directions.
    // For fetching for real-time updates, we typically want all new messages for the chat.
    // The existing GET request to /api/messages/sender_id/receiver_id might need adjustment
    // or clarification on how it determines "unread" and if it serves all messages for the pair.
    // For now, assuming it fetches messages relevant to the chat_receiver_id (current user) from chat_sender_id.

    // Let's adjust the GET request to be more specific if message_list is for unread by receiver.
    // It should fetch messages where sender is chat_sender_id (other user) and receiver is chat_receiver_id (current user)
    // This is what the original data[i].sender check implies.
    $.get('/api/messages/' + chat_sender_id + '/' + chat_receiver_id, function (data) {
        if (data.length > 0) {
            for (var i = 0; i < data.length; i++) {
                var msg = data[i];
                var message_html = '';
                var timestamp = new Date(msg.timestamp);
                var formatted_time = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                var sender_name_display = '';
                var message_class = '';

                // data[i].sender is the username string from MessageSerializer
                if (msg.sender === current_username) {
                    message_class = 'message-sent';
                    sender_name_display = 'You';
                } else {
                    message_class = 'message-received';
                    sender_name_display = msg.sender; // Username of the other person
                }

                message_html = `
                    <div class="message ${message_class}">
                        <div class="title message-sender">${sender_name_display}</div>
                        ${msg.message}
                        <div class="message-timestamp">${formatted_time}</div>
                    </div>`;

                $('#board').append(message_html);
            }
            scrolltoend();
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Error receiving messages:", textStatus, errorThrown, jqXHR.responseText);
    });
}

// This part was in chat.html, ensure it's correctly set up
// $(function () {
//     scrolltoend(); // Initial scroll
//     $('#chat-box').on('submit', function (event) {
//         event.preventDefault();
//         var message_input = $('#id_message');
//         // current_username is the sender, chat_sender_id is the username of the user being chatted to.
//         // The `send` function expects sender_username, then receiver_username.
//         // `chat_sender_id` in this context is the ID of the person we are talking to.
//         // We need their username. This is available in chat.html as {{ receiver.username }}.
//         // Let's assume chat.html will pass this as another JS variable: `chat_with_username`
//
//         // The original send call was: send('{{ request.user.username }}', '{{ receiver.username }}', message.val());
//         // So, current_username maps to {{ request.user.username }}
//         // and we need {{ receiver.username }} for the second argument of send().
//
//         // Let's adjust chat.html to provide `chat_with_username`
//         // For now, I'll use a placeholder `chat_with_username` which needs to be defined in chat.html script block
//         send(current_username, chat_with_username_placeholder, message_input.val());
//         // message_input.val(''); // Moved to inside send() success
//     });
//
//     // Call receive function periodically
//     if (typeof chat_sender_id !== 'undefined' && typeof chat_receiver_id !== 'undefined') {
//        setInterval(receive, 1000); // Poll every 1 second
//     }
// });

// The jQuery ready function and event listeners should remain in the HTML template's script tag
// to ensure variables like `current_username` and `chat_with_username_placeholder` (which needs to be `chat_with_username`)
// are correctly passed from the Django template to JavaScript when the page loads.
// The `setInterval` should also be there.
// `scrolltoend()` can be called initially in the template too.

// Note: The `message_list` view in `views.py` filters by `is_read=False` and then marks messages as read.
// This means `receive()` will only get unread messages. If a user sends a message, it's marked as read for *them*
// if they are the receiver in that API call. This logic might need refinement for a typical chat where
// `receive` should get all new messages for the conversation since the last poll, regardless of who sent them.
// However, the current structure of `message_view` which loads `messages.html` gets *all* messages for the pair.
// The polling `receive()` then only gets messages sent by `chat_sender_id` to `chat_receiver_id` that are unread.
// This is okay for showing messages from the other user. Sent messages are not re-fetched by `receive()`
// if `send()` doesn't append them. This is why I modified `send()` to not append HTML.
// The initial load in `messages.html` shows history. `receive()` shows new incoming.
// If `send()` does not append, then the sender will not see their own message until a page reload,
// unless `receive()` is modified to fetch messages from both directions or `message_list` API changes.

// For robust real-time display of own messages:
// 1. `send()` could optimistically append the message (as it did before, but using new format).
//    Timestamp would be client-side (can differ from server) or temporarily omitted.
// OR
// 2. `receive()` function or the `message_list` API needs to be adapted to return messages sent by current user too,
//    that are new since last check.
// Given the subtask constraints, I'll stick to modifying `chat.js` based on existing HTML/API structure as much as possible.
// The `send()` function no longer appends the message to avoid potential duplicates if `receive()` also fetches it.
// This means the sender will only see their message appear when `receive()` (on their side or the other user's)
// indirectly causes it to be rendered, or on page refresh. This is a simplification.
// A better approach would be for send() to get the created message object (with timestamp) back from the server
// and append that.

// The /api/messages/(sender)/(receiver) endpoint seems to be for fetching messages *from* sender *to* receiver.
// So, in receive(), chat_sender_id is "other user", chat_receiver_id is "me". This is correct for getting messages from other user.
// The current user's own messages are not fetched by this.
// So, if `send()` doesn't append, my own messages won't appear in real-time.
// I will revert `send()` to append the message optimistically for better UX, using client time for timestamp.
// This is a common compromise if not using WebSockets or server-sent events.

// Re-evaluating: The original `send` appended HTML. The `receive` also appended.
// `text_box` was global. `receive` changed `text_box.replace('right', 'left blue lighten-5');`
// This means `receive` was only for messages from the other user.
// So, `send` should append the user's own message.

// Final plan for chat.js:
// - send() will construct and append the sent message HTML immediately.
// - receive() will construct and append received message HTML.
// - Both will use the new structure with proper classes and formatted timestamp.
// - Timestamp for sent messages will be client-generated for optimistic update.
// - `chat_with_username` needs to be defined in chat.html template.

// Let's refine `send` and `receive` again.

function new_send(sender_username, receiver_username, message_text) {
    // sender_username is current_username
    // receiver_username is the username of the person being chatted with
    $.post('/api/messages/', JSON.stringify({ sender: sender_username, receiver: receiver_username, message: message_text }), function (data_sent) {
        // data_sent is the successfully saved message object from server, including server timestamp
        var timestamp = new Date(data_sent.timestamp);
        var formatted_time = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        var message_html = `
            <div class="message message-sent">
                <div class="title message-sender">You</div>
                ${data_sent.message}
                <div class="message-timestamp">${formatted_time}</div>
            </div>`;
        $('#board').append(message_html);
        $('#id_message').val('');
        scrolltoend();
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Error sending message:", textStatus, errorThrown, jqXHR.responseText);
        // Optionally, display an error to the user
    });
}

function new_receive() {
    // chat_sender_id is other user's ID, chat_receiver_id is current user's ID (passed from template)
    // This fetches messages sent FROM chat_sender_id TO chat_receiver_id that are unread.
    $.get('/api/messages/' + chat_sender_id + '/' + chat_receiver_id, function (data) {
        if (data.length > 0) {
            for (var i = 0; i < data.length; i++) {
                var msg = data[i];
                var timestamp = new Date(msg.timestamp);
                var formatted_time = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                // msg.sender is username of the other user (due to API endpoint structure)
                var message_html = `
                    <div class="message message-received">
                        <div class="title message-sender">${msg.sender}</div>
                        ${msg.message}
                        <div class="message-timestamp">${formatted_time}</div>
                    </div>`;
                $('#board').append(message_html);
            }
            scrolltoend();
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Error receiving messages:", textStatus, errorThrown, jqXHR.responseText);
    });
}

// The actual functions used by the old setInterval and submit handler were `send` and `receive`.
// I will rename new_send to send and new_receive to receive.
// The global JS variables `chat_sender_id`, `chat_receiver_id`, `current_username` and
// `chat_with_username` (this one still needs to be added to chat.html) are used.

// Final version of functions:
function send(sender_username, receiver_username, message_text) {
    // sender_username is current_username
    // receiver_username is the username of the person being chatted with
    $.ajax({
        url: '/api/messages/',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ sender: sender_username, receiver: receiver_username, message: message_text }),
        success: function (data_sent) {
            var timestamp = new Date(data_sent.timestamp);
            var formatted_time = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });

            var message_html = `
                <div class="message message-sent">
                    <div class="title message-sender">You</div>
                    ${data_sent.message}
                    <div class="message-timestamp">${formatted_time}</div>
                </div>`;
            $('#board').append(message_html);
            $('#id_message').val('');
            scrolltoend();
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error("Error sending message:", textStatus, errorThrown, jqXHR.responseText);
        }
    });
}

function receive() {
    // chat_sender_id (other user's ID), chat_receiver_id (current user's ID)
    $.get('/api/messages/' + chat_sender_id + '/' + chat_receiver_id, function (data) {
        if (data.length > 0) {
            for (var i = 0; i < data.length; i++) {
                var msg = data[i];
                var timestamp = new Date(msg.timestamp);
                var formatted_time = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true });

                var message_html = `
                    <div class="message message-received">
                        <div class="title message-sender">${msg.sender}</div>
                        ${msg.message}
                        <div class="message-timestamp">${formatted_time}</div>
                    </div>`;
                $('#board').append(message_html);
            }
            scrolltoend();
        }
    }).fail(function(jqXHR, textStatus, errorThrown) {
        console.error("Error receiving messages:", textStatus, errorThrown, jqXHR.responseText);
    });
}

// The event binding and setInterval should be in chat.html to correctly use
// Django template variables like {{ request.user.username }} and {{ receiver.username }}.
// Make sure chat.html defines `chat_with_username = "{{ receiver.username }}";`
// The `send` function in `chat.html`'s script block will then call the global `send` above.
// The `setInterval(receive, 1000)` will call the global `receive` above.

// scrolltoend() is already defined.
// The global variables `chat_sender_id`, `chat_receiver_id`, `current_username` are set in chat.html.
// `chat_with_username` also needs to be set in chat.html for the send function call.

// One final check on $.post vs $.ajax for sending JSON:
// $.post is a shorthand. For sending JSON, explicitly setting contentType is better.
// Changed $.post to $.ajax for the send function.
// Added hour12: true for AM/PM format.The `chat.js` has been significantly refactored. The `send` function now posts the message and on success, uses the server's response (which includes the server-generated timestamp) to append the sent message to the chat board. The `receive` function fetches new messages from the other user and appends them. Both functions now use the new HTML structure and CSS classes. Timestamps are formatted to HH:MM AM/PM.

**Step 3: Update `chat.html` to define `chat_with_username` for `chat.js`**
The `send` function in `chat.js` now expects `receiver_username` which corresponds to `{{ receiver.username }}` in the template. I'll add `chat_with_username` to the script block in `chat.html`.
