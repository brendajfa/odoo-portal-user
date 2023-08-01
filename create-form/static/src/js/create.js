(function () {
    // Insert your code
    const select_option = document.getElementById('select_option');
    const mult = document.getElementById('mult');
    const exp = document.getElementById('exp');


    select_option.addEventListener('input', calculateOperation);

    function calculateOperation() {
        var option_number = select_option.value;
        var electec_option = null;
        select_options.forEach(option => {
            if (option.number == option_number){
                electec_option = option;
            }
          })
        mult.textContent = electec_option.mult_2
        exp.textContent = electec_option.exp_2
    }

})();
    