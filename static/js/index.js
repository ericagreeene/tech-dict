function init() {
    console.log('hi');

    $('.ui.dropdown')
        .dropdown({transition: 'drop', on: 'hover' });

    $('#about-menu').click(function() {
        window.location.href = '/about.html';
        return false;
    });
}



window.onload = init;
