const storyButton = document.querySelector('#readMoreBtn');
const aboutDetails = document.querySelector('#aboutDetails');

const serviceLinks = document.querySelectorAll('.service-link');
const serviceSelect = document.querySelector('#serviceSelect');

const enquiryForm = document.querySelector('#enquiryForm');
const customerNameInput = document.querySelector('#customerName');
const preferredDateInput = document.querySelector('#preferredDate');
const formFeedback = document.querySelector('#formFeedback');


storyButton.addEventListener('click', function () {
    const isVisible = storyButton.getAttribute('aria-expanded') === 'true';

    if (isVisible) {
        aboutDetails.hidden = true;
        storyButton.setAttribute('aria-expanded', 'false');
        storyButton.textContent = 'Meet Zef Beauty';
    } else {
        aboutDetails.hidden = false;
        storyButton.setAttribute('aria-expanded', 'true');
        storyButton.textContent = 'Hide our story';
    }
});

serviceLinks.forEach(function (link) {
    link.addEventListener('click', function () {
        const selectedService = link.dataset.service;
        serviceSelect.value = selectedService;
    });
});


function getTodayDate() {
    const today = new Date();

    const year = today.getFullYear();

    const month = String(today.getMonth() +1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

preferredDateInput.min = getTodayDate();

function validateForm() {
    const customerName = customerNameInput.value.trim();

    customerNameInput.setCustomValidity(
        customerName === '' ? 'Please enter your name.' : ''
    );

    preferredDateInput.min = getTodayDate();
}

enquiryForm.addEventListener('input', function () {
    validateForm();
    formFeedback.textContent = '';
});

enquiryForm.addEventListener('submit', function (event) {
    event.preventDefault();
    validateForm();

    if(!enquiryForm.reportValidity()) {
        return;
    }

    const customerName = customerNameInput.value.trim();

    formFeedback.textContent = 
    `Thank you, ${customerName}, for your enquiry! ` + 
    "Nothing saved or sent, this is just a demo form.";
});   