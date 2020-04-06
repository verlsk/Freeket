$(document).ready(function () {
    $("#fechaEvento").datepicker({minDate: '1', dateFormat: 'dd-mm-yy'});

    $('#horaEvento').timepicker({
    timeFormat: 'H:mm',
    interval: 15,
    minTime: '00',
    maxTime: '23:55',
    defaultTime: '00:00',
    startTime: '00:00',
    dynamic: false,
    dropdown: true,
    scrollbar: true
    });

    var nmax = $('#nMaxInput').val();
    for (var i = 1; i <= nmax; i++){
        $('#nComprarEntradas').append(new Option(i, i));
    }

});