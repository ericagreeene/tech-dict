
function init() {
    console.log('hi');

    $('.browse').popup({
        inline     : true,
        hoverable  : true,
        position   : 'bottom left',
        lastResort: 'bottom left',
        delay: {
            show: 200,
            hide: 800
        }
    });
}

window.onload = init;
