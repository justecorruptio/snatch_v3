var game = window.localStorage;
var countdownInterval = 0;
var lastLogStep = -1;
var pollXhr;

function showMessage(msg, level, duration) {
    var $el = $('.snatch-message');
    $el.find('.badge').attr('class', 'w-100 badge badge-' + level).text(msg);
    $el.stop(true);

    $el.css({opacity: 0})
        .animate({opacity: 1}, 100)
        .delay(duration)
        .animate({opacity: 0}, 100);
}

function hideMessage() {
    var $el = $('.snatch-message');
    $el.stop(true);
    $el.css({opacity: 0});
}

function alert(msg) {
    showMessage(msg, 'danger', 5000);
}

function log(msg) {
    showMessage(msg, 'info', 10000);
}

function doCountdown(timeLeft, prev) {
    var now = Date.now() / 1000;
    clearTimeout(countdownInterval);

    timeLeft -= now - prev;
    var tl = timeLeft | 0,
        status_msg;

    if (timeLeft > 0) {
        countdownInterval = setTimeout(function() {
            doCountdown(timeLeft , now);
        }, 100);
        status_msg = `Game ends in ${tl} seconds.`;
    }
    else {
        status_msg = 'Game over.';
    }
    $('#snatch-display-status').text(status_msg);
}

function updateSnatchWord(word) {
    $('.snatch-word').val(word);
    $('#snatch-overlay-word').text(word);
}

function cleanInput() {
    var $el = $(this),
        val = $el.val();

    val = val.replace(/^\s+|\s+$/g, '');
    val = val.replace(/\s+/g, ' ');
    $el.val(val);
}

function eventKeyboardIndex(event) {
    var $el = $('#snatch-keyboard');
    var offset = $el.offset();
    var x = event.pageX;
    var y = event.pageY;
    var h = $el.height();
    var w = $el.width();
    var idx = ((x - offset.left)*20/w|0) + 20 * ((y - offset.top)*3/h|0);
    return idx;
}

function showPage(page) {
    $('.snatch-page').hide();
    $('.snatch-page-' + page).show();
}

function startGame() {
    showPage(1);
    lastLogStep = -1;
    apiPollGame();
}

function reset() {
    delete game.name;
    delete game.nonce;
    delete game.step;
    delete game.phase;
    delete game.min_word;
    lastLogStep = 0;
    hideMessage();
    clearTimeout(countdownInterval);
    updateSnatchWord('');
    $('#snatch-input-name').val('');
    $('#snatch-display-table').html('');
    $('#snatch-display-players').html('');
    pollXhr.abort();
    showPage(0);
}

function renderBoard(data) {
    $('#snatch-display-name').text(game.name);
    var $table = $('#snatch-display-table');
    var i, j;

    $table.html('');
    for(i = 0; i < data.table.length; i++) {
        var letter = data.table[i];
        $table.append($(`<div class="snatch-tile snatch-tile-letter">${letter}</div>`));
    }

    var $players = $('#snatch-display-players');
    $players.html('');
    for(i = 0; i < data.players.length; i++) {
        var [h, words] = data.players[i],
            $row = $('<div class="d-flex flex-wrap align-items-baseline">'),
            score = 0;
        for(j = 0; j< words.length; j++) {
            score += words[j].length;
        }
        $row.append($(`<div class="snatch-handle snatch-handle-score snatch-handle-p-${i}">
            ${score}
        </div>`));
        $row.append($(`<div class="snatch-handle snatch-handle-p-${i}">${h}</div>`));
        for(j = 0; j< words.length; j++) {
            $row.append($(`<div class="snatch-tile snatch-tile-p-${i}">${words[j]}</div>`));
        }
        $players.append($row);
    }

    $('.snatch-area-inputs').hide();
    game.phase = data.phase;
    game.min_word = data.options.min_word;
    switch(data.phase) {
        case 1:
            $('.snatch-area-inputs-start').show();
            $(`#snatch-display-add-bot>label`).removeClass('active');
            $(`#snatch-display-add-bot>label[data-value="${data.options.bot_level}"]`)
                .addClass('active');
            $(`#snatch-display-min-word>label`).removeClass('active');
            $(`#snatch-display-min-word>label[data-value="${data.options.min_word}"]`)
                .addClass('active');
            $(`#snatch-display-game-length>label`).removeClass('active');
            $(`#snatch-display-game-length>label[data-value="${data.options.game_length}"]`)
                .addClass('active');
            break;
        case 2: case 3:
            $('.snatch-area-inputs-play').show();
            $('#snatch-input-word').focus();
            break;
        case 4:
            $('.snatch-area-next-game').show();
            $('.snatch-area-next-game button').hide();
            if(data.next_name) {
                game.next_name = data.next_name;
                $('#snatch-button-join-next-game').show();
            }else{
                delete game.next_name;
                $('#snatch-button-create-next-game').show();
            }
    }
    var status_msg;
    switch(data.phase) {
        case 1:
            status_msg = 'Waiting for players.';
            break;
        case 2:
            if(data.bag == 1) {
                status_msg = '1 tile left.';
            }
            else {
                status_msg = `${data.bag} tiles left.`;
            }
            break;
        case 3:
            doCountdown(data.time_left, Date.now() / 1000);
            status_msg = '';
            break;
        case 4:
            status_msg = 'Game over.';
            break;
    }
    $('#snatch-display-status').text(status_msg);

    var log_data = data.log[data.log.length - 1];
    if (log_data[0] > lastLogStep) {
        lastLogStep = log_data[0];
        //if(log_data[1] == 'join') {
        //    log(`${log_data[2]} has joined the game.`);
        //}
        if(log_data[1] == 'play') {
            log(`${data.players[log_data[3]][0]} plays ${log_data[2]}.`);
        }
        else if(log_data[1] == 'steal') {
            if(log_data[3] == log_data[5]) {
                log(`${data.players[log_data[3]][0]} makes ` +
                    `${log_data[2]} from ${log_data[4]}.`
                );
            }
            else {
                log(`${data.players[log_data[3]][0]} makes ` +
                    `${log_data[2]} stealing ${log_data[4]}.`
                );
            }
        }
    }
}

function apiCreateGame() {
    var post_data;
    if(game.name) {
        post_data = JSON.stringify({link: game.name});
    }
    else {
        post_data = '{}';
    }
    return $.ajax(settings.baseUrl, {
        type: 'POST',
        data: post_data,
    }).done(function(data) {
        game.name = data.name;
    });
}

function apiSetOptions(field, value) {
    var data = {
        nonce: game.nonce
    };
    data[field] = value;
    return $.ajax(settings.baseUrl + `/${game.name}/options`, {
        type: 'POST',
        data: JSON.stringify(data)
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
        }
    })
}

function apiStartGame() {
    return $.ajax(settings.baseUrl + `/${game.name}/start`, {
        type: 'POST',
        data: JSON.stringify({
            nonce: game.nonce,
        })
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
    })
}

function apiPlayGame() {
    var word = $('#snatch-input-word').val();
    if(word.length < game.min_word) {
        alert('Minimum word length is ' + game.min_word);
        updateSnatchWord('');
        return;
    }
    return $.ajax(settings.baseUrl + `/${game.name}/play`, {
        type: 'POST',
        data: JSON.stringify({
            nonce: game.nonce,
            word: word
        })
    }).done(function(data) {
        updateSnatchWord('');
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
    })
}

function apiJoinGame() {
    var game_name = game.name;
    if(game.phase == 4 && game.next_name) {
        game_name = game.next_name;
    }
    return $.ajax(settings.baseUrl + `/${game_name}/join`, {
        type: 'POST',
        data: JSON.stringify({
            handle: game.handle
        })
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
        game.name = game_name;
        game.nonce = data.nonce;
        startGame();
    })
}

function apiPollGame(step, halt) {
    var query = '';

    if(!game.name) {
        // how does this happen?
        return;
    }
    if(step != undefined) {
        query = '?step=' + step;
    }
    pollXhr = $.ajax(settings.baseUrl + `/${game.name}${query}`, {
        type: 'GET',
    });
    pollXhr.done(function(data) {
        if('error' in data) {
            alert(data.error);
            reset();
            return;
        }
        game.step = data.step;
        renderBoard(data);
        if(!halt) {
            apiPollGame(game.step);
        }
    }).fail(function (xhr, text_status) {
        if(text_status != 'abort') {
            alert('Network Error, reconnecting...');
            setTimeout(function() {
                apiPollGame();
            }, 1000);
        }
    });
    return pollXhr;
}

$(function() {
    $('body').on('touchmove', function(event) {
        event.preventDefault();
        event.stopPropagation();
    });
    $('body').bind('touchstart', function preventZoom(e) {
        var t2 = e.timeStamp,
            t1 = $(this).data('lastTouch') || t2,
            dt = t2 - t1,
            fingers = e.originalEvent.touches.length;
        $(this).data('lastTouch', t2);
        if (!dt || dt > 500 || fingers > 1) return;

        e.preventDefault();
        $(this).trigger('click').trigger('click');
    });


    $('#snatch-input-handle').on('change', cleanInput);
    $('#snatch-input-word').on('change', cleanInput);

    $('#snatch-input-word').on('keydown', function(event) {
        event.preventDefault();
        var i = event.which,
            c = '',
            $el = $(this),
            val = $el.val();
        if (i >= 97 && i <= 122){
            c = String.fromCharCode(i - 32);
        }
        else if (i >= 65 && i<= 90){
            c = String.fromCharCode(i);
        }

        if (c != '' && val.length < 15) {
            updateSnatchWord(val + c);
        }
        else if (i == 8 && val != '') {
            updateSnatchWord(val.substr(0, val.length - 1));
        }
        else if (i == 13) {
            apiPlayGame();
        }
        return false;
    });

    $('#snatch-input-name').on('keypress', function(event) {
        event.preventDefault();
        var i = event.which,
            c = '',
            $el = $(this),
            val = $el.val();
        if (i >= 97 && i <= 122){
            c = String.fromCharCode(i - 32);
        }
        else if (i >= 65 && i<= 90){
            c = String.fromCharCode(i);
        }

        if (c != '' && val.length < 5) {
            $el.val(val + c);
        }
        else if (i == 8 && val != '') {
            $el.val(val.substr(0, val.length - 1));
        }
        else if (i == 13) {
            apiJoinGame();
        }
    });

    $('#snatch-button-new-game').on('click', function() {
        game.handle = $('#snatch-input-handle').val();
        if(!game.handle) {
            alert('Please enter a user name.');
            return;
        }
        apiCreateGame().then(apiJoinGame);
    });

    $('#snatch-button-join-game').on('click', function() {
        game.handle = $('#snatch-input-handle').val();
        if(!game.handle) {
            alert('Please enter a user name.');
            return;
        }
        if(!$('#snatch-input-name').val()) {
            alert('Please enter a 5-Letter game ID');
            return;
        }
        game.name = $('#snatch-input-name').val().toUpperCase();
        apiJoinGame();
    });

    $('.snatch-button-howto').on('click', function() {
        howtoStep = $(this).data('step');
        displayHelp(...howtoScript[howtoStep]);
    });

    $('#snatch-display-add-bot>label').on('click', function(event) {
        var value = $(this).data('value');
        apiSetOptions('bot_level', parseInt(value));
    });

    $('#snatch-display-min-word>label').on('click', function(event) {
        var value = $(this).data('value');
        apiSetOptions('min_word', parseInt(value));
    });

    $('#snatch-display-game-length>label').on('click', function(event) {
        var value = $(this).data('value');
        apiSetOptions('game_length', parseInt(value));
    });

    $('#snatch-button-start').on('click', function() {
        apiStartGame();
    });

    $('#snatch-button-play').on('click', function() {
        apiPlayGame();
    });

    var key_layout = "QQWWEERRTTYYUUIIOOPP AASSDDFFGGHHJJKKLL   ZZXXCCVVBBNNMM <<<";
    for(var i = 0; i < key_layout.length; i++) {
        if (key_layout[i] == ' ') {
            $('#snatch-keyboard').append($('<div class="snatch-key-spacer"></div>'))
        }
        else {
            var classes = ' snatch-key-' + i;
            while(key_layout[i] == key_layout[i+1]) {
                i ++;
                classes += ' snatch-key-' + i;
            }
            $('#snatch-keyboard').append(
                $(`<div class="snatch-key ${classes}"><div>${key_layout[i]}</div></div>`)
            );
        }
    }

    $('#snatch-keyboard').on('touchstart touchmove touchend', function(event) {
        var touches = event.originalEvent.touches,
            idx;
        $('.snatch-key-active').removeClass('snatch-key-active');
        for(var i = 0; i < touches.length; i++){
            idx = eventKeyboardIndex(touches[i]);
            $('.snatch-key-' + idx).addClass('snatch-key-active');
        }
    });

    $('#snatch-keyboard').on('touchend', function(event) {
        var idx = eventKeyboardIndex(event.originalEvent.changedTouches[0]),
            word = $('.snatch-word').val(),
            c = key_layout[idx];

        if(c == '<') {
            if(word.length > 0) {
                updateSnatchWord(word.substr(0, word.length - 1));
            }
        }
        else if(c && c != ' ' && word.length < 15){
            updateSnatchWord(word + c);
        }
    });

    $('#snatch-button-create-next-game').on('click', function() {
        pollXhr.abort();
        apiCreateGame().then(apiJoinGame);
    });

    $('#snatch-button-join-next-game').on('click', function() {
        pollXhr.abort();
        apiJoinGame();
    });

     $('#snatch-button-leave').on('click', function() {
        if(game.phase == 4 || confirm('Leave game? (You cannot re-join.)')) {
            reset();
        }
     });

     if (game.handle) {
        $('#snatch-input-handle').val(game.handle);
     }
     if (game.name && game.nonce) {
        showPage(1);
        delete game.step;
        apiPollGame();
     }

    /*
    // XXX:testing
    name = 'XKJRN';
    showPage(1);
    renderBoard({
        phase: 3,
        bag: 56,
        table: "DOIWJOQIENKJWWW",
        players: [
            ['Jay', ['HAPPY', 'BIRTH', 'CHRISTMAS', 'MONTHLY', 'MARTYR']],
            ['Marissa', ['JEJUNE', 'AUGUST', 'HOPEFUL', 'FOUR']],
            ['Ruth', ['BARF']],
        ]
    });
    */
});
