const storyButton = document.querySelector('#readMoreBtn');
const aboutDetails = document.querySelector('#aboutDetails');

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