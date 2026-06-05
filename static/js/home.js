// ============================================
// home.js - فایل یکپارچه اسکریپت‌های صفحه اصلی
// ============================================

(function() {
    'use strict';

    // ==================== دیتاهای استاتیک ====================
    const newsItems = [
        {text: "تخفیف ویژه چاپ و پرینت تا پایان هفته", date: "امروز"},
        {text: "ثبت‌نام آزمون‌های سراسری آغاز شد", date: "دیروز"},
        {text: "خدمات جدید تایپ و ترجمه در کافی‌نت", date: "۲ روز پیش"},
        {text: "ساعت کاری کافی‌نت در تابستان افزایش یافت", date: "۳ روز پیش"},
        {text: "طرح ویژه دانشجویان با ۲۰٪ تخفیف", date: "۴ روز پیش"},
        {text: "قابلیت رهگیری آنلاین سفارشات فعال شد", date: "هفته گذشته"}
    ];

    // ==================== المنت‌های DOM ====================
    let elements = {};

    function cacheElements() {
        elements = {
            container: document.getElementById('servicesListContainer'),
            modalOverlay: document.getElementById('modalOverlay'),
            modalMessage: document.getElementById('modalMessage'),
            modalIcon: document.getElementById('modalIcon'),
            closeModalBtn: document.getElementById('closeModalBtn'),
            discountInput: document.getElementById('discountCodeInput'),
            applyDiscountBtn: document.getElementById('applyDiscountBtn'),
            registerSection: document.getElementById('registerSection'),
            loginSection: document.getElementById('loginSection'),
            newsListContainer: document.getElementById('newsListContainer'),
            newsMobileListContainer: document.getElementById('newsMobileListContainer'),
            newsMobileModal: document.getElementById('newsMobileModal'),
            closeNewsMobileBtn: document.getElementById('closeNewsMobileBtn'),
            registerForm: document.getElementById('registerForm'),
            loginForm: document.getElementById('loginForm'),
            togglePasswordBtn: document.getElementById('togglePasswordBtn'),
            loginPasswordInput: document.getElementById('loginPasswordInput'),
            loginPhoneInput: document.getElementById('loginPhoneInput'),
            regPasswordInput: document.getElementById('regPasswordInput'),
            fullNameInput: document.getElementById('fullNameInput'),
            phoneInput: document.getElementById('phoneInput'),
            navPan: document.getElementById('navPan'),
            floatingNewsBtn: document.getElementById('floatingNewsBtn'),
            // دکمه‌های جدید
            navReg: document.getElementById('navReg'),
            profileBtn: document.getElementById('profileBtn')
        };
    }

    // ==================== توابع کمکی ====================
    function formatPrice(price) {
        if (price === 0 || price === "0") return 'تماس بگیرید';
        if (typeof price === 'number') return price.toLocaleString('fa-IR') + ' تومان';
        return price;
    }

    function showModal(text, icon = '✨') {
        if (elements.modalMessage) elements.modalMessage.textContent = text;
        if (elements.modalIcon) elements.modalIcon.textContent = icon;
        if (elements.modalOverlay) elements.modalOverlay.classList.add('active');
    }

    function hideModal() {
        if (elements.modalOverlay) elements.modalOverlay.classList.remove('active');
    }

    function hideAllAuth() {
        if (elements.registerSection) elements.registerSection.style.display = 'none';
        if (elements.loginSection) elements.loginSection.style.display = 'none';
    }

    function showRegister() {
        hideAllAuth();
        if (elements.registerSection) {
            elements.registerSection.style.display = 'flex';
            console.log('نمایش فرم ثبت نام');
        } else {
            console.error('عنصر registerSection یافت نشد');
            showModal('خطا: فرم ثبت نام پیدا نشد', '❌');
        }
    }

    function showLogin() {
        hideAllAuth();
        if (elements.loginSection) {
            elements.loginSection.style.display = 'flex';
            console.log('نمایش فرم ورود');
        } else {
            console.error('عنصر loginSection یافت نشد');
            showModal('خطا: فرم ورود پیدا نشد', '❌');
        }
    }

    // ==================== اخبار ====================
    function renderNews(containerEl, items) {
        if (!containerEl) return;
        containerEl.innerHTML = items.map(item => `
            <div class="news-item">
                <div>${item.text}</div>
                <div class="news-date">📅 ${item.date}</div>
            </div>
        `).join('');
    }

    // ==================== خدمات (از سرور) ====================
    let servicesList = [];

    async function loadServices() {
        try {
            const response = await fetch('/api/home-services/');
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            servicesList = data.services || [];
            renderServices();
        } catch (error) {
            console.error('Error loading services:', error);
            // Fallback: خدمات پیش‌فرض
            servicesList = [
                { icon: "🖨️", title: "پرینت و اسکن", description: "پرینت رنگی، اسکن مدارک", price: 5000 },
                { icon: "🏛️", title: "خدمات دولتی", description: "استعلام و ثبت نام", price: 15000 },
                { icon: "🌐", title: "ثبت نام اینترنتی", description: "کنکور، مهاجرت", price: 20000 },
                { icon: "🎓", title: "خدمات دانشجویی", description: "پایان‌نامه، جزوه", price: 10000 },
                { icon: "✍️", title: "تایپ و طراحی", description: "رزومه، تایپ فارسی", price: 8000 },
                { icon: "📦", title: "پیگیری سفارشات", description: "رهگیری مرسوله", price: 3000 },
                { icon: "⚙️", title: "خدمات سفارشی", description: "سفارش خاص شما", price: 0 }
            ];
            renderServices();
        }
    }

    function renderServices() {
        if (!elements.container) return;

        elements.container.innerHTML = servicesList.map((svc, i) => {
            const priceDisplay = svc.price_display || formatPrice(svc.price);
            const description = svc.description || svc.desc || '';

            return `
                <div class="service-row" data-service-index="${i}">
                    <div class="row-header">
                        <div class="row-icon">${svc.icon || '📄'}</div>
                        <div class="row-info">
                            <div class="row-title">${svc.title || 'بدون عنوان'}</div>
                            <div class="row-desc">${description}</div>
                        </div>
                        <div class="row-price">💲 ${priceDisplay}</div>
                    </div>
                    <textarea class="description-input" placeholder="توضیحات سفارش خود را بنویسید..." rows="2"></textarea>
                    <button class="order-btn" data-index="${i}">📋 ثبت سفارش</button>
                </div>
            `;
        }).join('');

        // attach order button events
        document.querySelectorAll('.order-btn').forEach(btn => {
            btn.removeEventListener('click', handleOrderClick);
            btn.addEventListener('click', handleOrderClick);
        });
    }

    async function handleOrderClick(event) {
        const btn = event.currentTarget;
        const index = parseInt(btn.dataset.index);
        const svc = servicesList[index];
        const row = btn.closest('.service-row');
        const textarea = row?.querySelector('.description-input');
        const description = textarea?.value || '';

        // بررسی احراز هویت
        const isAuthenticated = window.userAuthenticated || false;

        if (!isAuthenticated) {
            showModal('⚠️ لطفاً ابتدا وارد حساب کاربری خود شوید', '🔐');
            showLogin();
            return;
        }

        const csrf = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

        try {
            const response = await fetch('/api/service/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf,
                },
                body: JSON.stringify({
                    title: svc.title,
                    description: description || svc.description || '',
                    price: typeof svc.price === 'number' ? svc.price : 0,
                    priority: 'medium'
                })
            });

            const data = await response.json();

            if (data.success) {
                showModal(`✅ سفارش با موفقیت ثبت شد!\nکد پیگیری: ${data.tracking_code}\nمشاهده در پنل کاربری`, '🎉');
                if (textarea) textarea.value = '';
            } else {
                showModal('⚠️ ' + (data.error || 'خطا در ثبت سفارش'), '❌');
            }
        } catch (error) {
            console.error('Order error:', error);
            showModal('⚠️ خطا در ارتباط با سرور', '❌');
        }
    }

    // Helper: get cookie by name
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // ==================== رویدادهای فرم‌ها ====================
    function initFormEvents() {
        // ثبت‌نام
        if (elements.registerForm) {
            elements.registerForm.addEventListener('submit', async function(e) {
                e.preventDefault();
                const fullName = elements.fullNameInput?.value.trim() || '';
                const phone = elements.phoneInput?.value.trim() || '';
                const password = elements.regPasswordInput?.value.trim() || '';
                const csrf = getCookie('csrftoken') || document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';

                if (!fullName || !phone.match(/09[0-9]{9}/)) {
                    showModal('⚠️ لطفاً اطلاعات را صحیح وارد کنید', '❌');
                    return;
                }

                try {
                    const formData = new FormData();
                    formData.append('full_name', fullName);
                    formData.append('phone', phone);
                    formData.append('password', password || phone);
                    formData.append('csrfmiddlewaretoken', csrf);

                    const response = await fetch('/register/', {
                        method: 'POST',
                        body: formData,
                    });

                    if (response.redirected) {
                        window.location.href = response.url;
                    } else {
                        const result = await response.json();
                        if (result.success) {
                            showModal('✅ ثبت‌نام با موفقیت انجام شد!', '🎉');
                            hideAllAuth();
                            elements.registerForm.reset();
                        } else {
                            showModal('⚠️ ' + (result.error || 'خطا در ثبت‌نام'), '❌');
                        }
                    }
                } catch (error) {
                    console.error('Register error:', error);
                    showModal('⚠️ خطا در ثبت‌نام', '❌');
                }
            });
        }

        // نمایش/مخفی رمز عبور
        if (elements.togglePasswordBtn && elements.loginPasswordInput) {
            elements.togglePasswordBtn.addEventListener('click', function() {
                const type = elements.loginPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                elements.loginPasswordInput.setAttribute('type', type);
                this.textContent = type === 'password' ? '👁️' : '🙈';
            });
        }
    }

    // ==================== رویدادهای عمومی ====================
    function initGlobalEvents() {
        // بستن مودال
        if (elements.closeModalBtn) {
            elements.closeModalBtn.addEventListener('click', hideModal);
        }
        if (elements.modalOverlay) {
            elements.modalOverlay.addEventListener('click', (e) => {
                if (e.target === elements.modalOverlay) hideModal();
            });
        }

        // کد تخفیف
        if (elements.applyDiscountBtn) {
            elements.applyDiscountBtn.addEventListener('click', () => {
                const code = elements.discountInput?.value.trim() || '';
                if (code) {
                    showModal(`🎉 کد تخفیف «${code}» اعمال شد!`, '🏷️');
                } else {
                    showModal('⚠️ لطفاً کد تخفیف را وارد کنید', '🏷️');
                }
            });
        }

        // دکمه‌های ثبت نام و ورود
        if (elements.navReg) {
            elements.navReg.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('کلیک روی دکمه ثبت نام');
                showRegister();
            });
        } else {
            console.warn('دکمه navReg پیدا نشد');
        }

        // دکمه پروفایل
        if (elements.profileBtn) {
            elements.profileBtn.addEventListener('click', () => {
                if (window.userAuthenticated) {
                    window.location.href = '/profile/';
                } else {
                    showLogin();
                }
            });
        }

        // اخبار موبایل
        if (elements.floatingNewsBtn && elements.newsMobileModal) {
            elements.floatingNewsBtn.addEventListener('click', () => {
                elements.newsMobileModal.classList.add('active');
            });
        }
        if (elements.closeNewsMobileBtn && elements.newsMobileModal) {
            elements.closeNewsMobileBtn.addEventListener('click', () => {
                elements.newsMobileModal.classList.remove('active');
            });
            elements.newsMobileModal.addEventListener('click', (e) => {
                if (e.target === elements.newsMobileModal) {
                    elements.newsMobileModal.classList.remove('active');
                }
            });
        }

        // پنل مدیریت
        if (elements.navPan) {
            elements.navPan.addEventListener('click', () => {
                window.location.href = '/admin/';
            });
        }

        // بستن auth با کلیک خارج
        if (elements.registerSection) {
            elements.registerSection.addEventListener('click', function(e) {
                if (e.target === elements.registerSection) hideAllAuth();
            });
        }
        if (elements.loginSection) {
            elements.loginSection.addEventListener('click', function(e) {
                if (e.target === elements.loginSection) hideAllAuth();
            });
        }

        // کلید Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                hideModal();
                hideAllAuth();
                if (elements.newsMobileModal) {
                    elements.newsMobileModal.classList.remove('active');
                }
            }
        });

        // Resize: بستن مودال موبایل در دسکتاپ
        window.addEventListener('resize', () => {
            if (window.innerWidth > 1100 && elements.newsMobileModal) {
                elements.newsMobileModal.classList.remove('active');
            }
        });
    }

    // ==================== مقداردهی اولیه ====================
    function init() {
        cacheElements();

        // چک کردن وجود عناصر مهم
        console.log('عناصر یافت شده:', {
            navReg: !!elements.navReg,
            registerSection: !!elements.registerSection,
            loginSection: !!elements.loginSection
        });

        // بارگذاری اخبار
        renderNews(elements.newsListContainer, newsItems);
        renderNews(elements.newsMobileListContainer, newsItems);

        // بارگذاری خدمات
        loadServices();

        // تنظیم رویدادها
        initFormEvents();
        initGlobalEvents();
    }

    // شروع بعد از بارگذاری کامل DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();