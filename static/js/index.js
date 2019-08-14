function init() {
    console.log('hi');

    $('.ui.dropdown')
        .dropdown({transition: 'drop', on: 'hover' });

    $('#about-menu').click(function() {
        window.location.href = '/about.html';
        return false;
    });

    $('#contribute-menu').click(function() {
        window.location.href = '/contribute.html';
        return false;
    });

    $('.twitter').click(function() {
        var entryId = $(this).attr('entry-id');
        var href = 'https://twitter.com/intent/tweet';
        var url = href.concat('?text=', window.location.href, entryId);

        // open a popup with the link to the post
        !window.open(url, 'Twitter', 'width=500,height=500');

        return false;
    });
}


window.onload = init;
