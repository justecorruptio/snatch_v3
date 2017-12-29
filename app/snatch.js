var name;
var nonce;
var step=null;

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
    $('#snatch-display-name').text(name);
    $('#snatch-display-bag').text(data.bag);
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
    switch(data.phase) {
        case 1:
            $('.snatch-area-inputs-start').show();
            break;
        case 2: case 3:
            $('.snatch-area-inputs-play').show();
            $('#snatch-input-word').focus();
            break;
    }
}

function apiCreateGame() {
    return $.ajax(settings.baseUrl, {
        type: 'POST',
    }).done(function(data) {
        name = data.name;
    });
}

function apiStartGame() {
    return $.ajax(settings.baseUrl + `/${name}/start`, {
        type: 'POST',
        data: JSON.stringify({
            nonce: nonce,
        })
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
    })
}

function apiPlayGame() {
    return $.ajax(settings.baseUrl + `/${name}/play`, {
        type: 'POST',
        data: JSON.stringify({
            nonce: nonce,
            word: $('#snatch-input-word').val()
        })
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
        $('#snatch-input-word').val('')
    })
}

function apiJoinGame() {
    return $.ajax(settings.baseUrl + `/${name}/join`, {
        type: 'POST',
        data: JSON.stringify({
            handle: $('#snatch-input-handle').val()
        })
    }).done(function(data) {
        if('error' in data) {
            alert(data.error);
            return Promise.reject();
        }
        nonce = data.nonce;
        startGame();
    })
}

function apiPollGame() {
    var query = '';
    if(step != null) {
        query = '?step=' + step;
    }
    return $.ajax(settings.baseUrl + `/${name}${query}`, {
        type: 'GET',
    }).done(function(data) {
        console.log(data);
        step = data.step;
        renderBoard(data);
    }).then(apiPollGame);
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
        if(!$('#snatch-input-handle').val()) {
            alert('Please enter a user name.');
            return;
        }
        apiCreateGame().then(apiJoinGame);
    });

    $('#snatch-button-join-game').on('click', function() {
        if(!$('#snatch-input-handle').val()) {
            alert('Please enter a user name.');
            return;
        }
        if(!$('#snatch-input-name').val()) {
            alert('Please enter a 5-Letter game ID');
            return;
        }
        name = $('#snatch-input-name').val().toUpperCase();
        apiJoinGame();
    })

    $('#snatch-button-start').on('click', function() {
        apiStartGame();
    });

    $('#snatch-button-play').on('click', function() {
        apiPlayGame();
    });

    for(var i = 0; i < 27; i++) {
        $('#snatch-keyboard').append(
            $(`<div>${"QWERTYUIOASDFGHJKLZXCVBNMP<"[i]}</div>`)
        );
    }
     $('#snatch-keyboard div').on('click', function() {
        var $el = $(this),
            $word = $('#snatch-input-word'),
            word = $word.val();
            c = $el.text();
        if(c == '<') {
            if(word.length > 0) {
                $word.val(word.substr(0, word.length - 1));
            }
        }
        else {
            $word.val(word + c);
        }
     });

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
