// ============================================
// home.js - فایل یکپارچه اسکریپت‌های صفحه اصلی
// ============================================

(function () {
    'use strict';

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
            signupPasswordInput: document.getElementById('signupPasswordInput'),
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

   // ==================== اخبار (از سرور) ====================
    async function loadNews() {
        try {
            const response = await fetch('/api/news/');
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.success && data.news) {
                // رندر اخبار در هر دو نما
                renderNews(elements.newsListContainer, data.news);
                renderNews(elements.newsMobileListContainer, data.news);
            } else {
                // خطا یا خبری موجود نیست
                const emptyNews = [{
                    title: 'خبری برای نمایش وجود ندارد',
                    date: '',
                    icon: '📭',
                    link: null,
                    summary: 'لطفاً بعداً مراجعه کنید'
                }];
                renderNews(elements.newsListContainer, emptyNews);
                renderNews(elements.newsMobileListContainer, emptyNews);
            }
        } catch (error) {
            console.error('Error loading news:', error);
            // در صورت خطا، نمایش خبرهای fallback
            const fallbackNews = [
                {
                    title: 'تخفیف ویژه چاپ و پرینت تا پایان هفته',
                    date: 'امروز',
                    icon: '📰',
                    summary: 'تخفیف ویژه خدمات چاپ'
                },
                {
                    title: 'خدمات جدید تایپ و ترجمه در کافی‌نت',
                    date: '۲ روز پیش',
                    icon: '📰',
                    summary: 'خدمات تایپ و ترجمه'
                },
                {
                    title: 'خطا در بارگذاری اخبار',
                    date: 'لطفاً صفحه را refresh کنید',
                    icon: '⚠️',
                    summary: 'خطا در ارتباط با سرور'
                }
            ];
            renderNews(elements.newsListContainer, fallbackNews);
            renderNews(elements.newsMobileListContainer, fallbackNews);
        }
    }

    function renderNews(containerEl, items) {
        if (!containerEl) return;

        containerEl.innerHTML = items.map(item => {
            const newsLink = item.link || '#';
            const isExternal = item.link && (item.link.startsWith('http://') || item.link.startsWith('https://'));
            const targetAttr = isExternal ? 'target="_blank" rel="noopener noreferrer"' : '';

            // اضافه کردن کلاس pinned برای خبرهای سنجاق شده
            const pinnedClass = item.is_pinned ? 'pinned' : '';

            return `
                <a href="${newsLink}" ${targetAttr} class="news-item ${pinnedClass}" 
                   style="text-decoration: none; color: inherit; display: block;">
                    <div class="news-item-header">
                        <span class="news-icon">${item.icon || '📰'}</span>
                        <div class="news-text">
                            <div class="news-title">${item.title || 'بدون عنوان'}</div>
                            ${item.summary ? `<div class="news-summary">${item.summary}</div>` : ''}
                        </div>
                        ${item.is_pinned ? '<span class="pinned-badge">📌</span>' : ''}
                    </div>
                    <div class="news-date">
                        ${item.date ? '📅 ' + item.date : ''}
                        ${item.is_pinned ? ' • سنجاق شده' : ''}
                    </div>
                </a>
            `;
        }).join('');

        // اگر خبری لینک داره، از propagation جلوگیری کن (اختیاری)
        containerEl.querySelectorAll('.news-item').forEach(item => {
            item.addEventListener('click', function(e) {
                // می‌تونی اینجا tracking یا analytics اضافه کنی
                console.log('News clicked:', this.querySelector('.news-title')?.textContent);
            });
        });
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
                {icon: "🖨️", title: "پرینت و اسکن", description: "پرینت رنگی، اسکن مدارک", price: 5000},
                {icon: "🏛️", title: "خدمات دولتی", description: "استعلام و ثبت نام", price: 15000},
                {icon: "🌐", title: "ثبت نام اینترنتی", description: "کنکور، مهاجرت", price: 20000},
                {icon: "🎓", title: "خدمات دانشجویی", description: "پایان‌نامه، جزوه", price: 10000},
                {icon: "✍️", title: "تایپ و طراحی", description: "رزومه، تایپ فارسی", price: 8000},
                {icon: "📦", title: "پیگیری سفارشات", description: "رهگیری مرسوله", price: 3000},
                {icon: "⚙️", title: "خدمات سفارشی", description: "سفارش خاص شما", price: 0}
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
        // نمایش/مخفی رمز عبور
        if (elements.togglePasswordBtn && (elements.loginPasswordInput || elements.signupPasswordInput)) {
            elements.togglePasswordBtn.addEventListener('click', function () {
                let targetInput = elements.loginPasswordInput || elements.signupPasswordInput;

                if (targetInput) {
                    const type = targetInput.getAttribute('type') === 'password' ? 'text' : 'password';
                    targetInput.setAttribute('type', type);
                    this.textContent = type === 'password' ? '👁️' : '🙈';
                }
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
            elements.registerSection.addEventListener('click', function (e) {
                if (e.target === elements.registerSection) hideAllAuth();
            });
        }
        if (elements.loginSection) {
            elements.loginSection.addEventListener('click', function (e) {
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

        console.log('عناصر یافت شده:', {
            navReg: !!elements.navReg,
            registerSection: !!elements.registerSection,
            loginSection: !!elements.loginSection,
            newsSidebar: !!elements.newsListContainer,
            newsMobile: !!elements.newsMobileListContainer
        });

        // بارگذاری اخبار از سرور
        loadNews();  // جایگزین renderNews استاتیک

        // بارگذاری خدمات
        loadServices();

        // تنظیم رویدادها
        initFormEvents();
        initGlobalEvents();

        // رفرش خودکار اخبار هر ۵ دقیقه
        setInterval(loadNews, 5 * 60 * 1000);
    }

    // شروع بعد از بارگذاری کامل DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    // ==================== مدیریت وضعیت دکمه‌ها ====================
    // آبجکت برای ذخیره تایمرهای غیرفعال بودن دکمه‌ها
    const disabledButtons = {};

    // فعال کردن دکمه بعد از مدت زمان مشخص
    function enableButtonAfterDelay(btn, index, delayMs = 60000) {
        // اگر قبلاً تایمری برای این دکمه وجود داره، پاکش کن
        if (disabledButtons[index]) {
            clearTimeout(disabledButtons[index]);
        }

        // تنظیم تایمر جدید
        disabledButtons[index] = setTimeout(() => {
            btn.disabled = false;
            btn.textContent = '📋 ثبت سفارش';
            btn.classList.remove('btn-disabled');
            delete disabledButtons[index];
        }, delayMs);
    }

    // غیرفعال کردن دکمه
    function disableButton(btn, message = '⏳ لطفاً صبر کنید...') {
        btn.disabled = true;
        btn.textContent = message;
        btn.classList.add('btn-disabled');
    }

    async function handleOrderClick(event) {
        const btn = event.currentTarget;
        const index = parseInt(btn.dataset.index);
        const svc = servicesList[index];
        const row = btn.closest('.service-row');
        const textarea = row?.querySelector('.description-input');
        const description = textarea?.value || '';

        // بررسی اینکه دکمه قبلاً غیرفعال نشده باشه
        if (btn.disabled) {
            return; // اگر غیرفعاله، هیچ کاری نکن
        }

        // بررسی احراز هویت
        const isAuthenticated = window.userAuthenticated || false;

        if (!isAuthenticated) {
            showModal('⚠️ لطفاً ابتدا وارد حساب کاربری خود شوید', '🔐');
            showLogin();
            return;
        }

        // غیرفعال کردن دکمه قبل از ارسال درخواست
        disableButton(btn, '⏳ در حال ثبت...');

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

                // غیرفعال کردن دکمه برای ۱ دقیقه
                disableButton(btn, '✅ ثبت شد (۶۰ ثانیه)');
                enableButtonAfterDelay(btn, index, 60000); // 60000 میلی‌ثانیه = ۱ دقیقه

                // آپدیت شمارش معکوس
                startCountdown(btn, 60);
            } else {
                showModal('⚠️ ' + (data.error || 'خطا در ثبت سفارش'), '❌');
                // در صورت خطا، دکمه رو دوباره فعال کن
                btn.disabled = false;
                btn.textContent = '📋 ثبت سفارش';
                btn.classList.remove('btn-disabled');
            }
        } catch (error) {
            console.error('Order error:', error);
            showModal('⚠️ خطا در ارتباط با سرور', '❌');
            // در صورت خطا، دکمه رو دوباره فعال کن
            btn.disabled = false;
            btn.textContent = '📋 ثبت سفارش';
            btn.classList.remove('btn-disabled');
        }
    }

    // شمارش معکوس روی دکمه
    function startCountdown(btn, seconds) {
        let remaining = seconds;

        const countdownInterval = setInterval(() => {
            remaining--;

            if (remaining <= 0) {
                clearInterval(countdownInterval);
                return;
            }

            if (!btn.disabled) {
                // اگر دکمه به هر دلیلی فعال شد، شمارش معکوس رو متوقف کن
                clearInterval(countdownInterval);
                return;
            }

            btn.textContent = `✅ ثبت شد (${remaining} ثانیه)`;
        }, 1000);
    }
})();


// کنترل نمایش پیغام ها

const toastMessage = document.querySelector(".toast");
if(toastMessage){
    toastMessage.classList.add('show');
    setTimeout(() => {
        toastMessage.classList.remove('show');
        toastMessage.remove();
    },3400);
}