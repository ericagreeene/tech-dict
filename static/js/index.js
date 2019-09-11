function init() {

    $('#about-menu').click(function() {
        window.location.href = '/about.html';
        return false;
    });

    $('#contribute-menu').click(function() {
        window.location.href = '/contribute.html';
        return false;
    });

    $('.fa-twitter').click(function() {
        var entryId = $(this).attr('entry-id');
        var href = 'http://twitter.com/intent/tweet';

        // SOOOOO HACKY
        var url = href.concat('?text=', window.location.origin, '/', entryId, '.html');

        // open a popup with the link to the post
        !window.open(url, 'Twitter', 'width=500,height=500');

        return false;
    });
}


window.onload = init;
