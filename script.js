// Initialize AOS Animation Library
document.addEventListener('DOMContentLoaded', function () {
    AOS.init({ duration: 800, easing: 'ease-in-out', once: true, offset: 100 });
});

// ─── Preloader ───────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', function () {
    const preloader = document.getElementById('preloader');
    setTimeout(() => {
        preloader.style.opacity = '0';
        setTimeout(() => preloader.style.display = 'none', 300);
    }, 500);
});

// ─── Sticky Navbar ───────────────────────────────────────────────────────────
window.addEventListener('scroll', function () {
    const navbar = document.getElementById('navbar');
    navbar.classList.toggle('sticky', window.scrollY > 50);
});

// ─── Mobile Menu ─────────────────────────────────────────────────────────────
const hamburger = document.querySelector('.hamburger');
const navLinks  = document.querySelector('.nav-links');

if (hamburger) {
    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        const icon = hamburger.querySelector('i');
        icon.classList.toggle('fa-bars', !navLinks.classList.contains('active'));
        icon.classList.toggle('fa-times',  navLinks.classList.contains('active'));
    });
}

document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
        if (navLinks.classList.contains('active')) {
            navLinks.classList.remove('active');
            hamburger.querySelector('i').classList.replace('fa-times', 'fa-bars');
        }
    });
});

// ─── Dark Mode ───────────────────────────────────────────────────────────────
const darkModeToggle = document.getElementById('dark-mode-toggle');
const htmlElement    = document.documentElement;
const dmIcon         = darkModeToggle.querySelector('i');

if (localStorage.getItem('theme') === 'dark') {
    htmlElement.setAttribute('data-theme', 'dark');
    dmIcon.classList.replace('fa-moon', 'fa-sun');
}

darkModeToggle.addEventListener('click', () => {
    const isDark = htmlElement.getAttribute('data-theme') === 'dark';
    isDark ? htmlElement.removeAttribute('data-theme') : htmlElement.setAttribute('data-theme', 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    dmIcon.classList.toggle('fa-sun', !isDark);
    dmIcon.classList.toggle('fa-moon', isDark);
});

// ─── Image Slider (static + dynamic event photos) ────────────────────────────
const prevBtn = document.querySelector('.slider-btn.prev');
const nextBtn = document.querySelector('.slider-btn.next');
const slider  = document.querySelector('.slider');
let   currentIdx = 0;
let   slideTimer;
let   allSlides  = [];

function updateSlider() {
    allSlides = Array.from(slider.querySelectorAll('.slide'));
    if (!allSlides.length) return;
    slider.style.transform = `translateX(-${currentIdx * 100}%)`;
    allSlides.forEach((s, i) => s.classList.toggle('active', i === currentIdx));
}
function nextSlide() {
    allSlides = Array.from(slider.querySelectorAll('.slide'));
    currentIdx = (currentIdx + 1) % allSlides.length;
    updateSlider();
}
function prevSlide() {
    allSlides = Array.from(slider.querySelectorAll('.slide'));
    currentIdx = (currentIdx - 1 + allSlides.length) % allSlides.length;
    updateSlider();
}
function resetTimer() { clearInterval(slideTimer); slideTimer = setInterval(nextSlide, 5000); }

if (prevBtn && nextBtn) {
    nextBtn.addEventListener('click', () => { nextSlide(); resetTimer(); });
    prevBtn.addEventListener('click', () => { prevSlide(); resetTimer(); });
}

// Fetch uploaded event gallery photos and append to slider
// Dynamically detect server origin — works on any device (phone, tablet, laptop)
const API = window.location.origin;

(async function loadEventSlides() {
    try {
        const res   = await fetch(`${API}/api/gallery`);
        const photos = await res.json();
        if (!photos.length) { slideTimer = setInterval(nextSlide, 5000); return; }
        photos.forEach(p => {
            const slide = document.createElement('div');
            slide.className = 'slide';
            const alt   = p.title || 'Event Photo';
            const cap   = p.caption ? `<div class="slide-caption">${p.caption}</div>` : '';
            slide.innerHTML = `<img src="${API}/${p.url}" alt="${alt}" onerror="this.parentElement.remove()">${cap}`;
            slider.appendChild(slide);
        });
        updateSlider();
    } catch (_) { /* server not running – skip */ }
    slideTimer = setInterval(nextSlide, 5000);
})();


// ═══════════════════════════════════════════════════════════════════════════
//  BOOKING PORTAL  (3-Step Flow connected to Python/Flask backend)
// ═══════════════════════════════════════════════════════════════════════════

// State
let bookingState = {
    checkIn: '', checkOut: '', guests: 2,
    roomTypeId: null, roomId: null, roomName: '', roomPrice: 0,
    totalNights: 0, totalAmount: 0
};

// ─── Step helpers ────────────────────────────────────────────────────────────
function goToStep(n) {
    [1, 2, 3].forEach(i => {
        document.getElementById(`booking-step-${i}`).classList.toggle('hidden', i !== n);
        const ind = document.getElementById(`step-ind-${i}`);
        ind.classList.toggle('active',    i <= n);
        ind.classList.toggle('completed', i < n);
    });
}

// ─── Set date minimums ───────────────────────────────────────────────────────
const checkInInput  = document.getElementById('check-in');
const checkOutInput = document.getElementById('check-out');
if (checkInInput) {
    const today = new Date().toISOString().split('T')[0];
    checkInInput.min  = today;
    checkOutInput.min = today;
    checkInInput.addEventListener('change', function () {
        checkOutInput.min = this.value;
        if (checkOutInput.value && checkOutInput.value <= this.value) {
            const d = new Date(this.value);
            d.setDate(d.getDate() + 1);
            checkOutInput.value = d.toISOString().split('T')[0];
        }
    });
}

// ─── Step 1: Search Available Rooms ─────────────────────────────────────────
const bookingForm = document.getElementById('booking-form');
if (bookingForm) {
    bookingForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        bookingState.checkIn  = checkInInput.value;
        bookingState.checkOut = checkOutInput.value;
        bookingState.guests   = parseInt(document.getElementById('guests').value);

        const btn = document.getElementById('check-avail-btn');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Searching...';
        btn.disabled  = true;

        try {
            // Calculate nights
            const ci = new Date(bookingState.checkIn);
            const co = new Date(bookingState.checkOut);
            bookingState.totalNights = Math.round((co - ci) / 86400000);

            // Fetch room types WITH availability for chosen dates
            const params = new URLSearchParams({
                check_in:  bookingState.checkIn,
                check_out: bookingState.checkOut
            });
            const res   = await fetch(`${API}/api/rooms?${params}`);
            const rooms = await res.json();

            renderRoomCards(rooms);
            goToStep(2);
        } catch (err) {
            alert('Could not reach the server. Make sure app.py is running on port 5000.');
        } finally {
            btn.innerHTML = '<i class="fas fa-search"></i> Search Available Rooms';
            btn.disabled  = false;
        }
    });
}

// ─── Step 2: Render Room Cards ───────────────────────────────────────────────
function renderRoomCards(rooms) {
    const grid = document.getElementById('room-selection-grid');
    grid.innerHTML = '';

    if (!rooms || rooms.length === 0) {
        grid.innerHTML = '<p style="color:#aaa;text-align:center;padding:40px">No room types found.</p>';
        return;
    }

    rooms.forEach(room => {
        const nights    = bookingState.totalNights;
        const total     = room.price_per_night * nights;
        const avail     = room.available_count;
        const isFull    = avail === 0;
        const card      = document.createElement('div');
        card.className  = 'room-select-card' + (isFull ? ' room-unavailable' : '');

        // Availability badge text
        let availBadge;
        if (isFull) {
            availBadge = `<span class="avail-badge avail-none"><i class="fas fa-ban"></i> No Availability</span>`;
        } else if (avail <= 2) {
            availBadge = `<span class="avail-badge avail-low"><i class="fas fa-exclamation-triangle"></i> Only ${avail} left!</span>`;
        } else {
            availBadge = `<span class="avail-badge avail-ok"><i class="fas fa-check-circle"></i> ${avail} room${avail > 1 ? 's' : ''} available</span>`;
        }

        // No-availability message panel
        const noAvailMsg = isFull ? `
            <div class="no-avail-panel">
                <i class="fas fa-door-closed"></i>
                <strong>All ${room.name}s are fully booked</strong> for your selected dates.
                <br>Please select a different room type or change your dates.
            </div>` : '';

        const btnHtml = isFull
            ? `<button class="btn btn-disabled" disabled>Not Available</button>`
            : `<button class="btn btn-primary" onclick="selectRoom(${room.id}, '${room.name}', ${room.price_per_night}, ${total})">
                   <i class="fas fa-check"></i> Select This Room
               </button>`;

        card.innerHTML = `
            <div class="rsc-img-wrap">
                <img src="${room.image}" alt="${room.name}" onerror="this.src='https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400'">
                ${availBadge}
            </div>
            <div class="rsc-info">
                <h3>${room.name}</h3>
                <p>${room.description}</p>
                <div class="rsc-meta">
                    <span><i class="fas fa-users"></i> Up to ${room.max_guests} guests</span>
                    <span class="rsc-price">₹${room.price_per_night.toLocaleString()} / night</span>
                </div>
                <!-- Enhanced Inventory Display -->
                <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid #334155; border-radius: 8px; padding: 12px; margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.85rem; color: #cbd5e1; margin-bottom: 8px;">
                        <span><i class="fas fa-hotel"></i> Total: <b>${room.total_rooms}</b></span>
                        <span style="color: #f87171;"><i class="fas fa-calendar-times"></i> Booked: <b>${room.booked_count}</b></span>
                        <span style="color: #4ade80;"><i class="fas fa-door-open"></i> Empty: <b>${avail}</b></span>
                    </div>
                    <!-- Progress bar -->
                    <div style="width: 100%; height: 6px; background: #334155; border-radius: 3px; overflow: hidden; display: flex;">
                        <div style="width: ${(room.booked_count / room.total_rooms) * 100}%; background: #f87171;"></div>
                        <div style="width: ${(avail / room.total_rooms) * 100}%; background: #4ade80;"></div>
                    </div>
                </div>
                <div class="rsc-total">Total for ${nights} night${nights > 1 ? 's' : ''}: <strong>₹${total.toLocaleString()}</strong></div>
                ${noAvailMsg}
                ${btnHtml}
            </div>`;
        grid.appendChild(card);
    });
}

function selectRoom(typeId, name, price, total) {
    bookingState.roomTypeId  = typeId;
    bookingState.roomName    = name;
    bookingState.roomPrice   = price;
    bookingState.totalAmount = total;
    renderBookingSummary();
    goToStep(3);
}

// ─── Step 3: Summary & Payment ───────────────────────────────────────────────
function renderBookingSummary() {
    const s = bookingState;
    document.getElementById('booking-summary').innerHTML = `
        <div class="summary-row"><span>🏨 Room</span><strong>${s.roomName}</strong></div>
        <div class="summary-row"><span>📅 Check-in</span><strong>${formatDate(s.checkIn)}</strong></div>
        <div class="summary-row"><span>📅 Check-out</span><strong>${formatDate(s.checkOut)}</strong></div>
        <div class="summary-row"><span>🌙 Nights</span><strong>${s.totalNights}</strong></div>
        <div class="summary-row"><span>👤 Guests</span><strong>${s.guests}</strong></div>
        <div class="summary-row total-row"><span>💰 Total Amount</span><strong>₹${s.totalAmount.toLocaleString()}</strong></div>`;
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' });
}

// Payment option radio highlight
document.querySelectorAll('.pay-opt input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', () => {
        document.querySelectorAll('.pay-opt').forEach(l => l.classList.remove('active'));
        radio.parentElement.classList.add('active');
    });
});

// ─── Step 3 Form Submit → Flask API ─────────────────────────────────────────
const guestForm = document.getElementById('guest-details-form');
if (guestForm) {
    guestForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        const btn = document.getElementById('confirm-booking-btn');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        btn.disabled  = true;

        const payMethod = document.querySelector('input[name="payment"]:checked').value;

        const payload = {
            name:           document.getElementById('guest-name').value.trim(),
            email:          document.getElementById('guest-email').value.trim(),
            phone:          document.getElementById('guest-phone').value.trim(),
            room_type_id:   bookingState.roomTypeId,
            check_in:       bookingState.checkIn,
            check_out:      bookingState.checkOut,
            guests:         bookingState.guests,
            payment_method: payMethod
        };

        try {
            const res  = await fetch(`${API}/api/book`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(payload)
            });
            const data = await res.json();

            if (data.success) {
                showBookingModal(data);
                guestForm.reset();
                goToStep(1);
            } else {
                alert('Booking failed: ' + data.message);
            }
        } catch (err) {
            alert('Server error. Please make sure app.py is running.');
        } finally {
            btn.innerHTML = '<i class="fas fa-check-circle"></i> Confirm Booking';
            btn.disabled  = false;
        }
    });
}

// ─── Navigation Buttons ──────────────────────────────────────────────────────
if (document.getElementById('back-to-step1')) document.getElementById('back-to-step1').addEventListener('click', () => goToStep(1));
if (document.getElementById('back-to-step2')) document.getElementById('back-to-step2').addEventListener('click', () => goToStep(2));

// ─── Success Modal ───────────────────────────────────────────────────────────
function showBookingModal(data) {
    document.getElementById('modal-booking-details').innerHTML = `
        <div class="modal-detail-row"><i class="fas fa-bed"></i> <span>${data.room_name} &nbsp;<small style="color:#d4af37">(Room ${data.room_number})</small></span></div>
        <div class="modal-detail-row"><i class="fas fa-moon"></i> <span>${data.total_nights} Night${data.total_nights > 1 ? 's' : ''}</span></div>
        <div class="modal-detail-row"><i class="fas fa-rupee-sign"></i> <span>₹${data.total_amount.toLocaleString()} <strong style="color:var(--primary-color)">(Pay on Arrival)</strong></span></div>
        <div class="modal-detail-row"><i class="fas fa-hashtag"></i> <span>Booking #${data.booking_id}</span></div>
        <div class="modal-detail-row txn"><i class="fas fa-concierge-bell"></i> <span>Payment Method: Pay at Hotel</span></div>`;
    document.getElementById('booking-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('booking-modal').classList.add('hidden');
}

// ─── Feedback System ─────────────────────────────────────────────────────────
const fbModal = document.getElementById('feedback-modal');
const fbStars = document.querySelectorAll('.feedback-stars i');
let currentFbRating = 0;

function openFeedbackModal() {
    if (fbModal) fbModal.classList.add('active');
}
function closeFeedbackModal() {
    if (fbModal) {
        fbModal.classList.remove('active');
        if (document.getElementById('feedbackForm')) document.getElementById('feedbackForm').reset();
        currentFbRating = 0;
        updateFbStars(0);
    }
}

// Star Click Handler
fbStars.forEach(star => {
    star.addEventListener('click', (e) => {
        const val = parseInt(e.target.dataset.val);
        currentFbRating = val;
        document.getElementById('fbRating').value = val;
        updateFbStars(val);
    });
    star.addEventListener('mouseover', (e) => updateFbStars(parseInt(e.target.dataset.val)));
    star.addEventListener('mouseout', () => updateFbStars(currentFbRating));
});

function updateFbStars(val) {
    fbStars.forEach(star => {
        if (parseInt(star.dataset.val) <= val) {
            star.style.color = '#d4af37';
        } else {
            star.style.color = '#cbd5e1';
        }
    });
}

// Submit Feedback API Call
async function submitFeedback(e) {
    e.preventDefault();
    if (currentFbRating === 0) {
        alert("Please select a star rating!");
        return;
    }
    const btn = document.getElementById('fbSubmitBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';

    const payload = {
        name: document.getElementById('fbGuestName').value,
        rating: currentFbRating,
        message: document.getElementById('fbMessage').value
    };

    try {
        const res = await fetch(`${API}/api/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            alert('Thank you for your feedback! It means a lot to us.');
            closeFeedbackModal();
        } else {
            alert('Failed: ' + data.message);
        }
    } catch (err) {
        alert('Server unreachable right now.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Submit Review';
    }
}

// Close modal on overlay click
if (document.getElementById('booking-modal')) {
    document.getElementById('booking-modal').addEventListener('click', function (e) {
        if (e.target === this) closeModal();
    });
}
if (document.getElementById('all-reviews-modal')) {
    document.getElementById('all-reviews-modal').addEventListener('click', function (e) {
        if (e.target === this) closeAllReviewsModal();
    });
}

// View All Reviews Modal Logic
const allReviewsModal = document.getElementById('all-reviews-modal');
function openAllReviewsModal() {
    if (allReviewsModal) {
        allReviewsModal.classList.add('active');
        loadTopFeedbacks(); // Always refresh reviews when opening modal
    }
}
function closeAllReviewsModal() {
    if (allReviewsModal) allReviewsModal.classList.remove('active');
}

// Load top feedback to the website page
async function loadTopFeedbacks() {
    const grid = document.getElementById('testimonial-grid');
    const allReviewsList = document.getElementById('all-reviews-list');

    try {
        const res = await fetch(`${API}/api/feedback`);
        const allFeedbacks = await res.json();
        
        // 1. Update the Main Grid Top 3 Feedbacks
        if (grid) {
            // Default static reviews fallback
            const defaultReviews = [
                { name: "Rajesh Kumar", message: "Amazing stay, very comfortable! The staff was incredibly welcoming and the view from our room was spectacular.", rating: 5, isReal: false },
                { name: "Amit Sharma", message: "One of the best hotels I've ever visited. The food at the restaurant is a must-try. Highly recommended.", rating: 5, isReal: false },
                { name: "Priya Patel", message: "Beautiful property with exceptional service. The spa treatment was exactly what I needed to relax.", rating: 4.5, isReal: false }
            ];

            // Filter real 5-star feedbacks
            const topFeedbacks = allFeedbacks.filter(fb => fb.rating === 5).map(fb => ({ ...fb, isReal: true }));
            
            // We need 3 total to show on home page, prioritizing real 5-star reviews
            const displayReviews = [...topFeedbacks, ...defaultReviews].slice(0, 3);
            
            grid.innerHTML = ''; 
            
            displayReviews.forEach((fb, index) => {
                const delay = (index + 1) * 100;
                const card = document.createElement('div');
                card.className = 'testimonial-card';
                card.setAttribute('data-aos', 'fade-up');
                card.setAttribute('data-aos-delay', delay.toString());

                // Highlight the actual guest 5-star review
                if (fb.isReal) {
                    card.style.border = '2px solid #d4af37';
                    card.style.position = 'relative';
                    const badge = document.createElement('div');
                    badge.innerHTML = '<i class="fas fa-check-circle"></i> Verified Guest';
                    badge.style.position = 'absolute';
                    badge.style.top = '-12px';
                    badge.style.right = '20px';
                    badge.style.background = '#d4af37';
                    badge.style.color = '#fff';
                    badge.style.padding = '4px 10px';
                    badge.style.borderRadius = '20px';
                    badge.style.fontSize = '0.75rem';
                    badge.style.fontWeight = 'bold';
                    card.appendChild(badge);
                }
                
                let starsHtml = '';
                for (let i = 1; i <= 5; i++) {
                    if (i <= Math.floor(fb.rating)) {
                        starsHtml += '<i class="fas fa-star"></i>';
                    } else if (i - fb.rating === 0.5) {
                        starsHtml += '<i class="fas fa-star-half-alt"></i>';
                    } else {
                        starsHtml += '<i class="far fa-star"></i>';
                    }
                }

                card.innerHTML += `
                    <div class="stars">${starsHtml}</div>
                    <p>"${fb.message}"</p>
                    <div class="guest-name">- ${fb.name}</div>
                `;
                grid.appendChild(card);
            });
        }
        
        // 2. Update the "All Reviews" Modal list
        if (allReviewsList) {
            if (allFeedbacks.length === 0) {
                allReviewsList.innerHTML = '<div style="text-align:center; padding: 40px; color:#64748b;"><i class="fas fa-comment-slash" style="font-size:2rem; margin-bottom:10px; display:block;"></i>No reviews yet.</div>';
            } else {
                allReviewsList.innerHTML = '';
                allFeedbacks.forEach(fb => {
                    let starsHtml = '';
                    for (let i = 1; i <= 5; i++) {
                        if (i <= fb.rating) starsHtml += '<i class="fas fa-star" style="color:#d4af37;"></i>';
                        else starsHtml += '<i class="fas fa-star" style="color:#cbd5e1;"></i>';
                    }
                    const date = new Date(fb.created_at).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' });
                    
                    allReviewsList.innerHTML += `
                        <div style="background:#1e293b; padding:20px; border-radius:10px; margin-bottom:15px; border:1px solid #2d3f5a;">
                            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:10px;">
                                <div>
                                    <div style="font-weight:bold; color:#e2e8f0; font-size:1.05rem;">${fb.name}</div>
                                    <div style="font-size:0.8rem; color:#64748b;">${date}</div>
                                </div>
                                <div style="font-size:0.9rem;">${starsHtml}</div>
                            </div>
                            <div style="color:#cbd5e1; font-style:italic; line-height:1.6; font-size:0.95rem;">"${fb.message}"</div>
                        </div>
                    `;
                });
            }
        }

    } catch (err) {
        console.log('Error loading feedback:', err);
    }
}

// Initialize dynamically when script loads
loadTopFeedbacks();

// ─── Policies Modal ──────────────────────────────────────────────────────────
const policyModal = document.getElementById('policy-modal');
const policyTitle = document.getElementById('policy-title');
const policyBody  = document.getElementById('policy-body');

const policies = {
    privacy: {
        title: "Privacy Policy",
        content: `
            <p style="margin-bottom:10px;"><strong>Last Updated:</strong> March 2026</p>
            <p>At The Mountain Crown, we are committed to protecting your privacy. This policy explains how your personal information is collected, used, and protected when you use our website or services.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">1. Information We Collect</h3>
            <p>We collect personal information such as your name, email address, phone number, and booking details when you make a reservation or contact us. We also collect non-personal data such as your IP address and browser type for site analytics.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">2. How We Use Your Information</h3>
            <p>Your information operates our booking system, communicates with you about your stay, and helps us improve our services. We do not sell your personal data to third parties.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">3. Data Security</h3>
            <p>We implement strict security measures to ensure your data is safe and protected against unauthorized access.</p>
        `
    },
    terms: {
        title: "Terms of Service",
        content: `
            <p style="margin-bottom:10px;"><strong>Welcome to The Mountain Crown!</strong></p>
            <p>By using our website and booking our services, you agree to comply with the following terms and conditions:</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">1. Booking & Check-in</h3>
            <p>Guests must be at least 18 years old to make a reservation. Valid government-issued photo ID is required upon check-in. Standard check-in time is 2:00 PM, and check-out is at 11:00 AM.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">2. Hotel Rules</h3>
            <p>We promote a peaceful environment. Parties, excessive noise, and illegal activities are strictly prohibited. The hotel holds the right to evict guests who violate these policies without refund.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">3. Liability</h3>
            <p>The hotel is not responsible for any lost, stolen, or damaged personal belongings. Guests are advised to use the in-room safes provided.</p>
        `
    },
    cancellation: {
        title: "Cancellation Policy",
        content: `
            <p>We understand that plans can change. Here is our cancellation and refund policy:</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">1. Free Cancellation</h3>
            <p>Bookings can be cancelled completely free of charge up to <strong>48 hours</strong> before the scheduled check-in date.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">2. Late Cancellation</h3>
            <p>If you cancel within 48 hours of your check-in date, a cancellation fee equal to the first night's room rate will be charged.</p>
            <h3 style="margin-top:20px; color:var(--primary-color); font-size:1.1rem; margin-bottom:8px;">3. No-Shows</h3>
            <p>Failure to arrive on your check-in date without prior notice will result in the cancellation of your entire reservation and a charge of 100% of the booking amount.</p>
        `
    }
};

function openPolicyModal(type) {
    if (policyModal && policies[type]) {
        policyTitle.innerHTML = policies[type].title;
        policyBody.innerHTML  = policies[type].content;
        policyModal.classList.add('active');
    }
}
function closePolicyModal() {
    if (policyModal) policyModal.classList.remove('active');
}

// Ensure clicking outside closes modal
if (document.getElementById('policy-modal')) {
    document.getElementById('policy-modal').addEventListener('click', function(e){
        if(e.target === this) closePolicyModal();
    });
}

// ─── Cancel Booking Modal ──────────────────────────────────────────────────
const cancelModal = document.getElementById('cancel-modal');
function openCancelModal() {
    if (cancelModal) cancelModal.classList.add('active');
}
function closeCancelModal() {
    if (cancelModal) {
        cancelModal.classList.remove('active');
        if (document.getElementById('cancelForm')) document.getElementById('cancelForm').reset();
    }
}
if (document.getElementById('cancel-modal')) {
    document.getElementById('cancel-modal').addEventListener('click', function (e) {
        if (e.target === this) closeCancelModal();
    });
}

async function submitCancellation(e) {
    e.preventDefault();
    const btn = document.getElementById('cancel-submit-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

    const payload = {
        booking_id: parseInt(document.getElementById('cancel-booking-id').value, 10),
        email: document.getElementById('cancel-email').value.trim()
    };

    try {
        const res = await fetch(`${API}/api/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            alert('✅ Success: ' + data.message);
            closeCancelModal();
        } else {
            alert('⚠️ ' + data.message);
        }
    } catch (err) {
        alert('Server unreachable right now. Please try again later.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// ─── Check Booking Modal ───────────────────────────────────────────────────
const checkBookingModal = document.getElementById('check-booking-modal');
const checkBookingResult = document.getElementById('check-booking-result');

function openCheckBookingModal() {
    if (checkBookingModal) {
        checkBookingModal.classList.add('active');
        checkBookingResult.style.display = 'none';
        checkBookingResult.innerHTML = '';
    }
}
function closeCheckBookingModal() {
    if (checkBookingModal) {
        checkBookingModal.classList.remove('active');
        if (document.getElementById('checkBookingForm')) document.getElementById('checkBookingForm').reset();
    }
}
if (checkBookingModal) {
    checkBookingModal.addEventListener('click', function (e) {
        if (e.target === this) closeCheckBookingModal();
    });
}

async function submitCheckBooking(e) {
    e.preventDefault();
    const btn = document.getElementById('check-submit-btn');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
    checkBookingResult.style.display = 'none';

    const payload = {
        booking_id: parseInt(document.getElementById('check-booking-id').value, 10),
        phone: document.getElementById('check-phone').value.trim()
    };

    try {
        const res = await fetch(`${API}/api/check-booking`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.success) {
            const b = data.booking;
            let badgeColor = b.status === 'confirmed' ? '#28a745' : b.status === 'pending' ? '#ffc107' : '#dc3545';
            checkBookingResult.innerHTML = `
                <strong style="font-size:1.1rem; color:var(--primary-color);">Booking #${b.id}</strong><br>
                <div style="margin-top:10px;">
                    <b>Name:</b> ${b.name}<br>
                    <b>Room:</b> ${b.room_name} (Room ${b.room_number || 'TBA'})<br>
                    <b>Dates:</b> ${b.check_in} to ${b.check_out}<br>
                    <b>Guests:</b> ${b.guests}<br>
                    <b>Total Amount:</b> ₹${b.total_amount.toLocaleString('en-IN')}<br>
                    <b>Status:</b> <span style="color:${badgeColor}; font-weight:bold;">${b.status.toUpperCase()}</span>
                </div>
            `;
            checkBookingResult.style.display = 'block';
        } else {
            checkBookingResult.innerHTML = `<span style="color:#dc3545;"><i class="fas fa-exclamation-triangle"></i> ${data.message}</span>`;
            checkBookingResult.style.display = 'block';
        }
    } catch (err) {
        checkBookingResult.innerHTML = `<span style="color:#dc3545;"><i class="fas fa-exclamation-triangle"></i> Server unreachable right now.</span>`;
        checkBookingResult.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

