var howtoScript = [
    // element id, plament, show button, trigger, message
    [
        '#snatch-input-handle', 'bottom', 'Continue', 'blur keyup',
        'Hello! Welcome to Snatch!<br>First, please enter your name here.',
    ],
    [
        '#snatch-button-new-game', 'bottom', false, 'click',
        'Next, click this button to create a game.',
    ],
    [
        '#snatch-display-name', 'bottom', 'Continue', '',
        'This is the Game ID. Other players can join your game using this code.',
    ],
    [
        '#snatch-display-add-bot', 'bottom', false, 'click',
        `Optionally you can add a bot to play with. For the tutorial, let's
        click the green button to add a bot with difficulty 2`
    ],
    [
        '#snatch-button-start', 'top', false, 'click',
        'When you\'re ready, click this button to start the game.',
    ],
    [
        '#snatch-display-players', 'bottom', 'Continue', '',
        'Gray letter tiles will start appearing here.'
    ],
    [
        '.snatch-word-wrapper', 'bottom', 'Continue', '',
        ()=>`If you can make a word (minimum length ${game.min_word}) with the gray tiles,
        type it here to claim it.
        <br><br>
        For example, if you see:
            <span class="badge badge-secondary">T</span>
            <span class="badge badge-secondary">P</span>
            <span class="badge badge-secondary">R</span>
            <span class="badge badge-secondary">A</span>,
        you can type in the word "PART".`
    ],
    [
        '.snatch-word-wrapper', 'bottom', 'Continue', '',
        `Furthermore, you can steal words by adding one or
        more gray letters to an existing word.
        <br><br>
        For example, if you or another player has
            <span class="badge badge-primary">HEAT</span>
        and a gray letter
            <span class="badge badge-secondary">C</span>
        appears, you can type in the word "TEACH".`
    ],
    [
        '.snatch-word-wrapper', 'bottom', 'Continue', '',
        `Lastly, you my combine two or more words to make
        a longer word!
        <br><br>
        For example, you may combine
            <span class="badge badge-primary">PET</span>
        and
            <span class="badge badge-primary">DRIP</span>
        to make
            <span class="badge badge-primary">TRIPPED</span>
        .`
    ],
    [
        '#snatch-display-players', 'bottom', 'Continue', '',
        'Whoever has the most letters at the end of the game wins!',
    ],
    [
        '#snatch-button-leave', 'bottom', 'Continue', 'click',
        `Lastly, you may click &times; to quit the current game,
        and return to the main screen.`,
    ],
    [
        '#snatch-display-players', 'bottom', 'End Tutorial', '',
        'Snatch is best played with friends, have fun!',
    ],
];

var howtoStep = 0;
var $openedPopover = false;

function dismissFunc(stop) {
    if(!$openedPopover) {
        return;
    }
    var $dismiss_button = $('.popover-dismiss');
    $dismiss_button.off('click', dismissFunc);
    $openedPopover.off($openedPopover.data('popoverTrigger'), dismissFunc);
    $openedPopover.popover('dispose');
    $openedPopover = false;
    if(stop !== true) {
        howtoStep ++;
        if(howtoScript[howtoStep]) {
            displayHelp(...howtoScript[howtoStep]);
        }
    }
}

function displayHelp(el_id, placement, button, trigger, message) {
    if($openedPopover) {
        dismissFunc(true);
    }

    var $el = $(el_id);

    if(!$el.is(':visible') || $el.height() < 1 ) {
        setTimeout(function () {
            displayHelp(el_id, placement, button, trigger, message);
        }, 100);
        return;
    }

    var button_html = `
            <button type="button" class="btn btn-warning btn-sm ml-2 mb-2 popover-dismiss">
                ${button}
            </button>
        `;
    if(!button) {
        button_html = '';
    }
    $el.popover({
        container: 'body',
        title: `Tutorial<small class="text-muted float-right popover-close">
            Dismiss Tutorial
        </small>`,
        content: message,
        placement: placement,
        html: true,
        trigger: 'manual',
        template: `
            <div class="popover" role="tooltip">
                <div class="arrow"></div>
                <div class="popover-header"></div>
                <div class="popover-body text-info"></div>
                ${ button_html }
            </div>
        `
    })

    $el.popover('show');
    $el.data('popoverTrigger', trigger);
    $openedPopover = $el;

    var $dismiss_button = $('.popover-dismiss');
    $dismiss_button.one('click', dismissFunc);
    $el.one(trigger, dismissFunc);

    $('.popover-close').click(function () {
        dismissFunc(true);
    })
}
