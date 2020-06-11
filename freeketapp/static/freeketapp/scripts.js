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


    const user_input = $("#busqueda")
    const eventos_div = $('#replaceable-content')
    const endpoint = '/eventos/'
    const delay_by_in_ms = 100
    let scheduled_function = false

    let ajax_call = function (endpoint, request_parameters) {
        $.getJSON(endpoint, request_parameters)
            .done(response => {
                // fade out the artists_div, then:
                eventos_div.fadeTo('fast', 0).promise().then(() => {
                    // replace the HTML contents
                    eventos_div.html(response['html_from_view'])
                    // fade-in the div with new contents
                    eventos_div.fadeTo('fast', 1)
                })
            })
    }


    user_input.on('keyup', function () {

        const request_parameters = {
            titulo: $(this).val() // value of user_input: the HTML element with ID user-input
        }

        // if scheduled_function is NOT false, cancel the execution of the function
        if (scheduled_function) {
            clearTimeout(scheduled_function)
        }

        // setTimeout returns the ID of the function to be executed
        scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters)
    });

    $("#btnOrganizador").click(function(){
        $("#infoOrg").removeClass("d-none")
        $("#btnOrganizador").addClass("active")
        $("#btnAmbos").removeClass("active")
        $("#btnAsistente").removeClass("active")
        $("#userType").val('org')
    });
    $("#btnAmbos").click(function(){
        $("#infoOrg").removeClass("d-none")
        $("#btnOrganizador").removeClass("active")
        $("#btnAmbos").addClass("active")
        $("#btnAsistente").removeClass("active")
        $("#userType").val('both')
    });
    $("#btnAsistente").click(function(){
        $("#infoOrg").addClass("d-none")
        $("#btnOrganizador").removeClass("active")
        $("#btnAmbos").removeClass("active")
        $("#btnAsistente").addClass("active")
        $("#userType").val('assist')
    });

    $(".custom-file-input").on("change", function() {
      var fileName = $(this).val().split("\\").pop();
      $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
    });

});