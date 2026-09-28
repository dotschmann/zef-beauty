const serviceLinks = document.querySelectorAll('.service-link');
const serviceSelect = document.querySelector('#serviceSelect');

const enquiryForm = document.querySelector('#enquiryForm');
const customerNameInput = document.querySelector('#customerName');
const preferredDateInput = document.querySelector('#preferredDate');
const formFeedback = document.querySelector('#formFeedback');

const siteHeader = document.querySelector('.site-header');
const menuToggle = document.querySelector('.menu-toggle');
const mainNavigation = document.querySelector('#mainNavigation');
const mobileMenuQuery = window.matchMedia('(max-width: 1023px)');

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

function updateHeaderHeight() {
    const headerHeight = siteHeader.getBoundingClientRect().height;

    siteHeader.style.setProperty(
        '--mobile-header-height',
        `${headerHeight}px`
    );

    document.documentElement.style.scrollPaddingTop =
        mobileMenuQuery.matches ? `${headerHeight + 16}px` : '';
}

function setMenuOpen(isOpen) {
    const shouldOpen = mobileMenuQuery.matches && isOpen;

    siteHeader.classList.toggle('menu-open', shouldOpen);
    document.body.classList.toggle('menu-locked', shouldOpen);

    menuToggle.setAttribute('aria-expanded', String(shouldOpen));
    menuToggle.setAttribute(
        'aria-label',
        shouldOpen ? 'Close menu' : 'Open menu'
    );

    // Closed mobile links must not receive keyboard focus.
    mainNavigation.inert =
        mobileMenuQuery.matches && !shouldOpen;
}

menuToggle.addEventListener('click', function () {
    const isOpen =
        menuToggle.getAttribute('aria-expanded') === 'true';

    setMenuOpen(!isOpen);
});

mainNavigation.querySelectorAll('a').forEach(function (link) {
    link.addEventListener('click', function () {
        if (mobileMenuQuery.matches) {
            setMenuOpen(false);
            menuToggle.focus({ preventScroll: true });
        }
    });
});

document.addEventListener('keydown', function (event) {
    if (!siteHeader.classList.contains('menu-open')) {
        return;
    }

    if (event.key === 'Escape') {
        setMenuOpen(false);
        menuToggle.focus();
    }

    // Keep keyboard navigation within the open menu and header.
    if (event.key === 'Tab') {
        const focusable = siteHeader.querySelectorAll(
            'button:not([disabled]), a[href]'
        );

        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    }
});


let menuResizeTimer;

window.addEventListener('resize', function () {
    siteHeader.classList.add('menu-resizing');

    clearTimeout(menuResizeTimer);

    menuResizeTimer = setTimeout(function () {
        siteHeader.classList.remove('menu-resizing');
    }, 200);
});

mobileMenuQuery.addEventListener('change', function () {
    siteHeader.classList.add('menu-resizing');
    setMenuOpen(false);
    updateHeaderHeight();
});

siteHeader.classList.add('menu-ready');
setMenuOpen(false);
updateHeaderHeight();

const headerObserver = new ResizeObserver(updateHeaderHeight);
headerObserver.observe(siteHeader);


const portfolioTrack = document.querySelector('#portfolioTrack');
const portfolioPrevious = document.querySelector('#portfolioPrevious');
const portfolioNext = document.querySelector('#portfolioNext');
const carouselControls = document.querySelector('.carousel-controls');

const carouselReducedMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)'
);

function updatePortfolioButtons() {
    const canScroll =
        portfolioTrack.scrollWidth > portfolioTrack.clientWidth + 2;

    // Both arrows stay available whenever there are more photos to show.
    portfolioPrevious.disabled = !canScroll;
    portfolioNext.disabled = !canScroll;
}

function movePortfolio(direction) {
    const firstPhoto = portfolioTrack.querySelector('.portfolio-item');

    if (!firstPhoto) {
        return;
    }

    const gap =
        parseFloat(getComputedStyle(portfolioTrack).columnGap) || 0;

    const distance = firstPhoto.getBoundingClientRect().width + gap;
    const maximumScroll =
        portfolioTrack.scrollWidth - portfolioTrack.clientWidth;

    const currentPosition = portfolioTrack.scrollLeft;
    let nextPosition = currentPosition + direction * distance;

    if (direction === 1 && currentPosition >= maximumScroll - 2) {
        // Next at the end returns to the beginning.
        nextPosition = 0;
    } else if (direction === -1 && currentPosition <= 2) {
        // Previous at the beginning returns to the end.
        nextPosition = maximumScroll;
    }

    portfolioTrack.scrollTo({
        left: Math.max(0, Math.min(nextPosition, maximumScroll)),
        behavior: carouselReducedMotion.matches ? 'instant' : 'smooth'
    });
}

portfolioPrevious.addEventListener('click', function () {
    movePortfolio(-1);
});

portfolioNext.addEventListener('click', function () {
    movePortfolio(1);
});

carouselControls.hidden = false;

const portfolioObserver = new ResizeObserver(updatePortfolioButtons);

portfolioObserver.observe(portfolioTrack);
updatePortfolioButtons();