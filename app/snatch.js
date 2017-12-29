var game = window.localStorage;
var countdownInterval = 0;
var lastLogStep = -1;
var pollXhr;

function alert(message) {
    var $el = $('#snatch-alert');
    $el.find('.badge').text(message);
    $el.clearQueue();
    $el.fadeIn(100).delay(1500).fadeOut();
}

function log(message) {
    var $el = $('#snatch-log');
    $el.find('.badge').text(message);
    $el.clearQueue();
    $el.fadeIn(100).delay(3000).fadeOut();
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

function cleanInput() {
    var $el = $(this),
        val = $el.val();

    val = val.replace(/^\s+|\s+$/g, '');
    val = val.replace(/\s+/g, ' ');
    $el.val(val);
}

function showPage(page) {
    $('.snatch-page').hide();
    $('.snatch-page-' + page).show();
}

function startGame() {
    showPage(1);
    apiPollGame();
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
            $row = $('<div class="d-flex flex-wrap align-items-baseline">');
            $row.append($(`<b>${h}</b>`));
        for(j = 0; j< words.length; j++) {
            $row.append($(`<div class="snatch-tile snatch-tile-p-${i}">${words[j]}</div>`));
        }
        $players.append($row);
    }

    $('.snatch-area-inputs').hide();
    game.phase = data.phase;
    switch(data.phase) {
        case 1:
            $('.snatch-area-inputs-start').show();
            if(data.has_bot) {
                $('#snatch-display-add-bot').hide();
            }
            else {
                $('#snatch-display-add-bot').show();
            }
            break;
        case 2: case 3:
            $('.snatch-area-inputs-play').show();
            $('#snatch-input-word').focus();
            break;
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
    console.log(log_data);
    if (log_data[0] > lastLogStep) {
        lastLogStep = log_data[0];
        if(log_data[1] == 'join') {
            log(`${log_data[2]} has joined the game.`);
        }
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
    return $.ajax(settings.baseUrl, {
        type: 'POST',
    }).done(function(data) {
        game.name = data.name;
    });
}

function apiAddBotGame(level) {
    return $.ajax(settings.baseUrl + `/${game.name}/addBot`, {
        type: 'POST',
        data: JSON.stringify({
            nonce: game.nonce,
            level: level,
        })
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
    return $.ajax(settings.baseUrl + `/${game.name}/play`, {
        type: 'POST',
        data: JSON.stringify({
            nonce: game.nonce,
            word: $('#snatch-input-word').val()
        })
    }).done(function(data) {
        $('#snatch-input-word').val('');
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
        apiPollGame(undefined, True);
    })
}

function apiJoinGame() {
    return $.ajax(settings.baseUrl + `/${game.name}/join`, {
        type: 'POST',
        data: JSON.stringify({
            handle: game.handle
        })
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
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
        game.step = data.step;
        renderBoard(data);
        if(!halt) {
            apiPollGame(game.step);
        }
    }).fail(function () {
        if(game.name) {
            // name is cleared before leaving
            alert('Network Error, reconnecting...');
            setTimeout(function() {
                apiPollGame(step);
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

    $('#snatch-input-handle').on('change', cleanInput);
    $('#snatch-input-word').on('change', cleanInput);

    $('#snatch-input-word').on('keypress', function(event) {
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
            $el.val(val + c);
        }
        else if (i == 8 && val != '') {
            $el.val(val.substr(0, val.length - 1));
        }
        else if (i == 13) {
            apiPlayGame();
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
    })

    $('#snatch-display-add-bot>button').on('click', function() {
        var $el = $(this),
            level = $el.text();
        apiAddBotGame(parseInt(level));
    });

    $('#snatch-button-start').on('click', function() {
        apiStartGame();
    });

    $('#snatch-button-play').on('click', function() {
        if($('#snatch-input-word').val().length < 4) {
            alert('Minimum word length is 4');
            return;
        }
        apiPlayGame();
    });

    for(var i = 0; i < 27; i++) {
        $('#snatch-keyboard').append(
            $(`<div><div>${"QWERTYUIOASDFGHJKLZXCVBNMP<"[i]}</div></div>`)
        );
    }
     $('#snatch-keyboard>div').on('click', function() {
        var $el = $(this),
            $word = $('#snatch-input-word'),
            word = $word.val(),
            c = $el.find('div').text();
        if(c == '<') {
            if(word.length > 0) {
                $word.val(word.substr(0, word.length - 1));
            }
        }
        else {
            $word.val(word + c);
        }
     });

     $('#snatch-button-leave').on('click', function() {
        if(game.phase == 4 || confirm('Leave game? (You cannot re-join.)')) {
            delete game.name;
            delete game.nonce;
            delete game.step;
            delete game.phase;
            lastLogStep = 0;
            clearTimeout(countdownInterval);
            $('#snatch-input-name').val('');
            $('#snatch-display-table').html('');
            $('#snatch-display-players').html('');
            pollXhr.abort();
            showPage(0);
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
        ]
    });
    */
});
