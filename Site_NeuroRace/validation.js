function validateName(name) {
    const re = /^[A-Za-zÀ-ú\s]+$/;
    return re.test(String(name));
}

function validatePhone(phone) {
    const re = /^\(\d{2}\) 9 \d{4}-\d{4}$/;
    return re.test(String(phone));
}

function applyPhoneMask(event) {
    let input = event.target;
    let value = input.value.replace(/\D/g, '').substring(0, 11);
    let formattedValue = '';
    if (value.length > 0) formattedValue = '(' + value.substring(0, 2);
    if (value.length > 2) formattedValue += ') ' + value.substring(2, 3);
    if (value.length > 3) formattedValue += ' ' + value.substring(3, 7);
    if (value.length > 7) formattedValue += '-' + value.substring(7, 11);
    input.value = formattedValue;
}

document.addEventListener('DOMContentLoaded', () => {
    const phoneInput = document.getElementById('reg-phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', applyPhoneMask);
    }
});