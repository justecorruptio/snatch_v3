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

function renderBoard() {
    $('#snatch-display-name').text(name);
}

function apiCreateGame() {
    return $.ajax(settings.baseUrl, {
        type: 'POST',
    }).done(function(data) {
        name = data.name;
    });
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
    }).then(apiPollGame);
}

$(function() {
    $('body').on('touchmove', function(event) {
        event.preventDefault();
        event.stopPropagation();
    });

    $('#snatch-input-handle').on('change', cleanInput);
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
        apiJoinGame();
    })

    // XXX:testing
    name = 'XKJRN';
    showPage(1);
    renderBoard();
});
