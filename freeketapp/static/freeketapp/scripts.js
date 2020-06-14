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

    const eventos_div = $('#replaceableContent')
    const endpoint = '/eventos/'
    const delay_by_in_ms = 100
    let scheduled_function = false

    let ajax_call = function (endpoint, request_parameters) {
        $.getJSON(endpoint, request_parameters)
            .done(response => {

                    html_content = "";
                    for (i = 0; i < response.length; i++) {

                      html_content += '<div class="elemento-busqueda"><a href="/evento/'+response[i]["fields"]["url_id"]+'"> <div style="background-image: url(/media/' + response[i]["fields"]["img"] + ')" class="image-busqueda"></div><div class="text-busqueda"><div class="text-main-busqueda"><strong>'+response[i]["fields"]["titulo"]+'</strong></div></div></a></div>'

                    }
                    eventos_div.html(html_content)

                })
            }



    user_input.on('keyup', function () {
        if ($(this).val()==''){
            eventos_div.html("");
            $("#box-busqueda").addClass("d-none");

        } else {
            $('#box-busqueda').removeClass('d-none');
            const request_parameters = {
                titulo: $(this).val() // value of user_input: the HTML element with ID user-input

            }


            // if scheduled_function is NOT false, cancel the execution of the function
            if (scheduled_function) {
                clearTimeout(scheduled_function)
            }

            // setTimeout returns the ID of the function to be executed
            scheduled_function = setTimeout(ajax_call, delay_by_in_ms, endpoint, request_parameters)
        }
    });

    $("#btnOrganizador").click(function(){
        $("#infoOrg").removeClass("d-none")
        $("#btnOrganizador").addClass("btnSideActive")
        $("#btnAmbos").removeClass("btnSideActive")
        $("#btnAsistente").removeClass("btnSideActive")
        $("#userType").val('org')
    });
    $("#btnAmbos").click(function(){
        $("#infoOrg").removeClass("d-none")
        $("#btnOrganizador").removeClass("btnSideActive")
        $("#btnAmbos").addClass("btnSideActive")
        $("#btnAsistente").removeClass("btnSideActive")
        $("#userType").val('both')
    });
    $("#btnAsistente").click(function(){
        $("#infoOrg").addClass("d-none")
        $("#btnOrganizador").removeClass("btnSideActive")
        $("#btnAmbos").removeClass("btnSideActive")
        $("#btnAsistente").addClass("btnSideActive")
        $("#userType").val('assist')
    });

    $(".custom-file-input").on("change", function() {
      var fileName = $(this).val().split("\\").pop();
      $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
    });
    let s_function = false
    var url_id = $('#urlId').val()
    const endpoint_read = '/reader/'
    delay_by_in_ms_read = 100
     let ajax_call_read = function (endpoint_read, request_parameters) {
        $.getJSON(endpoint_read, request_parameters)
            .done(response => {

                    if (response['resp'] == true)
                        alert("Correcto!");

                    else {
                        if (response['resp'] == 'ya validada')
                            alert("La entrada ya se ha usadoo")
                    }

                })
            }
    function onScanSuccess(qrCodeMessage) {

          // if scheduled_function is NOT false, cancel the execution of the function

        const request_parameters = {
                id: qrCodeMessage,
                url: url_id // value of user_input: the HTML element with ID user-input

        }

        if (s_function) {
            clearTimeout(s_function)
        }

        // setTimeout returns the ID of the function to be executed
        s_function = setTimeout(ajax_call_read, delay_by_in_ms_read, endpoint_read, request_parameters)

    }
    var w = $('.contReader').width() / 2;
    if (url_id != null) {
    var html5QrcodeScanner = new Html5QrcodeScanner(

    "qr-reader", { fps: 10, qrbox: w });
    html5QrcodeScanner.render(onScanSuccess);
    }

    let s_function_salida = false
    var url_id_salida = $('#urlIdSalida').val()
    const endpoint_read_salida = '/reader-salida/'
    delay_by_in_ms_read_salida = 100
     let ajax_call_read_salida = function (endpoint_read_salida, request_parameters_salida) {
        $.getJSON(endpoint_read_salida, request_parameters_salida)
            .done(response => {

                    if (response['resp'] == true)
                        alert("Correcto! Puede salir");

                    else {
                        if (response['resp'] == 'n')
                            alert("No puede salir. La entrada no se ha utilizado para entrar")
                    }

                })
            }
    function onScanSuccessSalida(qrCodeMessage) {

          // if scheduled_function is NOT false, cancel the execution of the function

        const request_parameters_salida = {
                id: qrCodeMessage,
                url: url_id_salida // value of user_input: the HTML element with ID user-input

        }

        if (s_function_salida) {
            clearTimeout(s_function_salida)
        }

        // setTimeout returns the ID of the function to be executed
        s_function_salida = setTimeout(ajax_call_read_salida, delay_by_in_ms_read, endpoint_read_salida, request_parameters_salida)

    }
    if (url_id_salida != null ){
    var wSalida = $('.contReader').width() / 2;
    var html5QrcodeScannerSalida = new Html5QrcodeScanner(

    "qr-reader", { fps: 10, qrbox: wSalida });
    html5QrcodeScannerSalida.render(onScanSuccessSalida);
    }

});