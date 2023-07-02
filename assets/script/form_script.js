document.addEventListener('DOMContentLoaded', function() {
    var passwordInput = document.querySelectorAll('input[type="password"]');
    var hidden = document.querySelectorAll('.pass-hide');
    var regForm = document.querySelector('.register-form');

    function togglePasswordVisibility(i) {
        if (passwordInput[i].type === 'password') {
            passwordInput[i].type = 'text';
            hidden[i].classList.remove('fa-eye-slash');
            hidden[i].classList.add('fa-eye');
        } else {
            passwordInput[i].type = 'password';
            hidden[i].classList.remove('fa-eye');
            hidden[i].classList.add('fa-eye-slash');
        }
    }

    hidden.forEach(function(icon, i) {
        icon.addEventListener('click', function() {
            togglePasswordVisibility(i);
        });
    });

    regForm.addEventListener('submit', function(event) {
        var password = passwordInput[0].value;
        var reenterPassword = passwordInput[1].value;

        if (password !== reenterPassword) {
            passwordInput[0].placeholder = "Passwords do not match";
            passwordInput[1].placeholder = "Passwords do not match";
        }
    });
});