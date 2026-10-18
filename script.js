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

enquiryForm.addEventListener('submit', async function (event) {
    event.preventDefault();

    const submitButton = enquiryForm.querySelector(
        'button[type="submit"]'
    );

    if (submitButton.disabled) {
        return;
    }

    validateForm();

    if (!enquiryForm.reportValidity()) {
        return;
    }

    const enquiry = {
        customerName: customerNameInput.value.trim(),
        customerEmail: document.querySelector('#customerEmail').value.trim(),
        serviceSelect: serviceSelect.value,
        preferredDate: preferredDateInput.value,
        message: document.querySelector('#message').value.trim()
    };

    const originalButtonText = submitButton.textContent;

    submitButton.disabled = true;
    submitButton.textContent = 'Sending…';
    enquiryForm.setAttribute('aria-busy', 'true');
    formFeedback.textContent = 'Sending your enquiry…';

    try {
        const response = await fetch('/api/enquiries', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(enquiry)
        });

        const result = await response.json();

        if (!response.ok) {
            if (result.fields) {
                formFeedback.textContent =
                    Object.values(result.fields).join(' ');

                const firstFieldId = Object.keys(result.fields)[0];
                const firstField = document.getElementById(firstFieldId);

                if (firstField) {
                    firstField.focus();
                }
            } else {
                formFeedback.textContent =
                    result.error || 'Your enquiry could not be saved.';
            }

            return;
        }

        if (result.saved !== true) {
            throw new Error('The server did not confirm saving.');
        }

        formFeedback.textContent =
            `Thank you, ${enquiry.customerName}. ` +
            `Your enquiry has been saved. Reference: ${result.enquiryId}. ` +
            'This is not a booking confirmation.';

    } catch (error) {
        formFeedback.textContent =
            "We couldn't confirm whether your enquiry was saved. " +
            'Please check with us before submitting again.';

        console.error('Enquiry request failed:', error);

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalButtonText;
        enquiryForm.removeAttribute('aria-busy');
    }
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


(function initialiseMovingPortfolio() {
    const section = document.querySelector('#portfolio');
    const track = document.querySelector('#portfolioTrack');
    const previous = document.querySelector('#portfolioPrevious');
    const next = document.querySelector('#portfolioNext');
    const toggle = document.querySelector('#portfolioToggle');
    const controls = section?.querySelector('.carousel-controls');

    if (!track || !previous || !next || !toggle || !controls) {
        return;
    }

    const photos = Array.from(track.children);
    if (photos.length === 0) return;

    const reducedMotion = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    );

    const speed = 30; // Pixels per second.

    let paused = false;
    let hovering = false;
    let visible = false;
    let looping = false;
    let distance = 0;
    let cycleWidth = 0;
    let position = 0;
    let previousTime = null;

    // Copies on both sides make the loop visually continuous.
    // Each copy includes the photograph AND its caption.
    function createCopies() {
        const fragment = document.createDocumentFragment();

        photos.forEach(function (photo) {
            const copy = photo.cloneNode(true);

            copy.setAttribute('data-portfolio-copy', '');
            copy.setAttribute('aria-hidden', 'true');
            copy.inert = true;

            // Avoid duplicate HTML IDs.
            copy.removeAttribute('id');
            copy.querySelectorAll('[id]').forEach(function (element) {
                element.removeAttribute('id');
            });

            fragment.append(copy);
        });

        return fragment;
    }

    track.prepend(createCopies());
    track.append(createCopies());

    function setPaused(value) {
        paused = value;
        previousTime = null;

        toggle.textContent = paused ? 'Play' : 'Pause';
        toggle.setAttribute(
            'aria-label',
            paused ? 'Play portfolio animation' : 'Pause portfolio animation'
        );
    }

    // Return an equivalent position within the middle set.
    function normalise(value) {
        return cycleWidth +
            ((value - cycleWidth) % cycleWidth + cycleWidth) %
            cycleWidth;
    }

    function updateLayout() {
        const gap = parseFloat(getComputedStyle(track).columnGap) || 0;

        distance = photos[0].getBoundingClientRect().width + gap;
        cycleWidth = distance * photos.length;

        const canScroll = cycleWidth - gap > track.clientWidth + 2;

        looping = canScroll && !reducedMotion.matches;
        track.classList.toggle('is-looping', looping);

        previous.disabled = !canScroll;
        next.disabled = !canScroll;
        toggle.hidden = !looping;

        position = looping ? cycleWidth : 0;
        track.scrollLeft = position;
        previousTime = null;
    }

    function movePortfolio(direction) {
        setPaused(true);

        let target;

        if (looping) {
            const current = normalise(track.scrollLeft);

            track.scrollLeft = current;
            target = current + direction * distance;
        } else {
            const maximum = track.scrollWidth - track.clientWidth;
            const current = track.scrollLeft;

            target = current + direction * distance;

            if (direction > 0 && current >= maximum - 2) {
                target = 0;
            } else if (direction < 0 && current <= 2) {
                target = maximum;
            }

            target = Math.max(0, Math.min(target, maximum));
        }

        track.scrollTo({
            left: target,
            behavior: reducedMotion.matches ? 'instant' : 'smooth'
        });
    }

    previous.addEventListener('click', function () {
        movePortfolio(-1);
    });

    next.addEventListener('click', function () {
        movePortfolio(1);
    });

    toggle.addEventListener('click', function () {
        setPaused(!paused);
    });

    // Temporarily stop while a mouse is over a photograph.
    track.addEventListener('pointerenter', function (event) {
        if (event.pointerType === 'mouse') hovering = true;
    });

    track.addEventListener('pointerleave', function () {
        hovering = false;
    });

    // Manual browsing pauses automatic movement until Play is pressed.
    track.addEventListener('pointerdown', function () {
        setPaused(true);
    });

    track.addEventListener('wheel', function () {
        setPaused(true);
    }, { passive: true });

    section.addEventListener('focusin', function (event) {
        if (event.target !== toggle) setPaused(true);
    });

    // Only animate while the gallery is on screen.
    const visibilityObserver = new IntersectionObserver(function (entries) {
        visible = entries[0].isIntersecting;
    });

    visibilityObserver.observe(track);

    function animate(time) {
        const canMove =
            looping &&
            !paused &&
            !hovering &&
            visible &&
            !document.hidden;

        if (canMove) {
            if (previousTime === null) {
                position = normalise(track.scrollLeft);
            } else {
                const elapsed = Math.min(time - previousTime, 50);
                position = normalise(position + speed * elapsed / 1000);
            }

            track.scrollLeft = position;
            previousTime = time;
        } else {
            previousTime = null;
        }

        requestAnimationFrame(animate);
    }

    controls.hidden = false;
    setPaused(false);
    updateLayout();

    const resizeObserver = new ResizeObserver(updateLayout);
    resizeObserver.observe(track);

    reducedMotion.addEventListener('change', updateLayout);

    requestAnimationFrame(animate);
})();


// Reveal selected content once when it enters the viewport.
(function initialiseScrollReveals() {
    const motionPreference = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    );

    if (
        motionPreference.matches ||
        !('IntersectionObserver' in window)
    ) {
        return;
    }

    const revealElements = document.querySelectorAll(
        '#services > h2, ' +
        '.portfolio-heading, ' +
        '.about-image, ' +
        '.about-copy, ' +
        '#contact h2'
    );

    const revealObserver = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) {
                    return;
                }

                entry.target.classList.add('reveal-visible');
                revealObserver.unobserve(entry.target);
            });
        },
        {
            threshold: 0.1
        }
    );

    revealElements.forEach(function (element) {
        element.classList.add('reveal-pending');
        revealObserver.observe(element);
    });

    // Reveal a block immediately if someone tabs into it.
    document.addEventListener('focusin', function (event) {
        const block = event.target.closest('.reveal-pending');

        if (block) {
            block.classList.add('reveal-visible');
            revealObserver.unobserve(block);
        }
    });

    // Stop hiding or animating content if the preference changes.
    motionPreference.addEventListener('change', function (event) {
        if (event.matches) {
            revealObserver.disconnect();

            revealElements.forEach(function (element) {
                element.classList.add('reveal-visible');
            });
        }
    });
})();

(function initialiseBeautyRibbon() {
    const ribbon = document.querySelector('.beauty-ribbon');
    const toggle = document.querySelector('.beauty-ribbon-toggle');

    if (!ribbon || !toggle) {
        return;
    }

    const motionPreference = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    );

    function updateRibbonMotion() {
        const allowMotion = !motionPreference.matches;

        ribbon.classList.toggle('is-ready', allowMotion);
        toggle.hidden = !allowMotion;
    }

    toggle.addEventListener('click', function () {
        const isPaused = ribbon.classList.toggle('is-paused');

        toggle.textContent = isPaused ? 'Play' : 'Pause';

        toggle.setAttribute(
            'aria-label',
            isPaused ? 'Play moving text' : 'Pause moving text'
        );
    });

    motionPreference.addEventListener('change', updateRibbonMotion);

    updateRibbonMotion();
})();


(function initialiseServiceStack() {
    const stack = document.querySelector('.service-stack');
    const header = document.querySelector('.site-header');

    if (!stack) {
        return;
    }

    const cards = Array.from(stack.children);
    const motionPreference = window.matchMedia(
        '(prefers-reduced-motion: reduce)'
    );

    function updateStack() {
        let headerHeight = 0;

        if (header) {
            const position = getComputedStyle(header).position;

            if (position === 'sticky' || position === 'fixed') {
                headerHeight = header.getBoundingClientRect().height;
            }
        }

        const top = Math.ceil(headerHeight) + 24;
        const tallestCard = Math.max(
            ...cards.map(function (card) {
                return card.offsetHeight;
            })
        );

        const lastOffset = Math.max(0, cards.length - 1) * 18;
        const availableHeight = document.documentElement.clientHeight;

        const cardsFit =
            tallestCard + top + lastOffset + 24 <= availableHeight;

        stack.style.setProperty('--stack-top', `${top}px`);

        stack.classList.toggle(
            'stack-enabled',
            cardsFit && !motionPreference.matches
        );
    }

    const sizeObserver = new ResizeObserver(updateStack);

    cards.forEach(function (card) {
        sizeObserver.observe(card);
    });

    if (header) {
        sizeObserver.observe(header);
    }

    window.addEventListener('resize', updateStack);
    motionPreference.addEventListener('change', updateStack);

    updateStack();
})();