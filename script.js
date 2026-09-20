const storyButton = document.querySelector('#readMoreBtn');
const aboutDetails = document.querySelector('#aboutDetails');
const serviceLinks = document.querySelectorAll('.service-link');
const serviceSelect = document.querySelector('#serviceSelect');

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