// script 1
(function () {
    // ==================== دیتا ====================
    const services = [
        {icon: "🖨️", title: "پرینت و اسکن", desc: "پرینت رنگی، اسکن مدارک", price: "۵,۰۰۰ تومان"},
        {icon: "🏛️", title: "خدمات دولتی", desc: "استعلام و ثبت نام", price: "۱۵,۰۰۰ تومان"},
        {icon: "🌐", title: "ثبت نام اینترنتی", desc: "کنکور، مهاجرت", price: "۲۰,۰۰۰ تومان"},
        {icon: "🎓", title: "خدمات دانشجویی", desc: "پایان‌نامه، جزوه", price: "۱۰,۰۰۰ تومان"},
        {icon: "✍️", title: "تایپ و طراحی", desc: "رزومه، تایپ فارسی", price: "۸,۰۰۰ تومان"},
        {icon: "📦", title: "پیگیری سفارشات", desc: "رهگیری مرسوله", price: "۳,۰۰۰ تومان"},
        {icon: "⚙️", title: "خدمات سفارشی", desc: "سفارش خاص شما", price: "تماس بگیرید"}
    ];

    const newsItems = [
        {text: "تخفیف ویژه چاپ و پرینت تا پایان هفته", date: "امروز"},
        {text: "ثبت‌نام آزمون‌های سراسری آغاز شد", date: "دیروز"},
        {text: "خدمات جدید تایپ و ترجمه در کافی‌نت", date: "۲ روز پیش"},
        {text: "ساعت کاری کافی‌نت در تابستان افزایش یافت", date: "۳ روز پیش"},
        {text: "طرح ویژه دانشجویان با ۲۰٪ تخفیف", date: "۴ روز پیش"},
        {text: "قابلیت رهگیری آنلاین سفارشات فعال شد", date: "هفته گذشته"}
    ];

    // ==================== المنت‌ها ====================
    const container = document.getElementById('servicesListContainer');
    const modalOverlay = document.getElementById('modalOverlay');
    const modalMessage = document.getElementById('modalMessage');
    const discountInput = document.getElementById('discountCodeInput');
    const applyDiscountBtn = document.getElementById('applyDiscountBtn');

    const registerSection = document.getElementById('registerSection');
    const loginSection = document.getElementById('loginSection');

    const newsSidebar = document.getElementById('newsSidebar');
    const newsListContainer = document.getElementById('newsListContainer');
    const newsMobileListContainer = document.getElementById('newsMobileListContainer');
    const floatingNewsBtn = document.getElementById('floatingNewsBtn');
    const newsMobileModal = document.getElementById('newsMobileModal');
    const closeNewsMobileBtn = document.getElementById('closeNewsMobileBtn');

    // ==================== توابع کمکی ====================
    function showModal(text) {
        modalMessage.textContent = text;
        modalOverlay.classList.add('active');
    }

    function hideModal() {
        modalOverlay.classList.remove('active');
    }

    function hideAllAuth() {
        registerSection.style.display = 'none';
        loginSection.style.display = 'none';
    }

    function showRegister() {
        hideAllAuth();
        registerSection.style.display = 'flex';
    }

    function showLogin() {
        hideAllAuth();
        loginSection.style.display = 'flex';
    }

    // ==================== رندر اخبار ====================
    function renderNews(containerEl) {
        containerEl.innerHTML = '';
        newsItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'news-item';
            div.innerHTML = `
            <div>${item.text}</div>
            <div class="news-date">📅 ${item.date}</div>
          `;
            containerEl.appendChild(div);
        });
    }

    renderNews(newsListContainer);
    renderNews(newsMobileListContainer);

    // ==================== رندر سرویس‌ها ====================
    function renderServices() {
        container.innerHTML = '';
        services.forEach((svc, index) => {
            const row = document.createElement('div');
            row.className = 'service-row';
            row.innerHTML = `
            <div class="row-header">
              <div class="row-icon">${svc.icon}</div>
              <div class="row-info">
                <div class="row-title">${svc.title}</div>
                <div class="row-desc">${svc.desc}</div>
              </div>
              <div class="row-price">💲 ${svc.price}</div>
            </div>
            <textarea class="description-input" placeholder="توضیحات سفارش خود را بنویسید..." rows="2"></textarea>
            <button class="order-btn" data-index="${index}">📋 ثبت سفارش</button>
          `;
            container.appendChild(row);
        });

        document.querySelectorAll('.order-btn').forEach(btn => {
            btn.addEventListener('click', function (e) {
                const idx = this.dataset.index;
                const serviceTitle = services[idx].title;
                const servicePrice = services[idx].price;
                const rowElement = this.closest('.service-row');
                const textarea = rowElement.querySelector('.description-input');
                const userDesc = textarea.value.trim();
                const discountVal = discountInput.value.trim();

                let message = `✅ سفارش "${serviceTitle}" ثبت شد.\n💰 هزینه: ${servicePrice}`;
                if (userDesc) {
                    message += `\n📝 توضیحات: ${userDesc}`;
                }
                if (discountVal) {
                    message += `\n🏷️ کد تخفیف فعال: ${discountVal}`;
                }
                showModal(message);
            });
        });
    }

    renderServices();

    // ==================== ایونت‌ها ====================
    document.getElementById('closeModalBtn').addEventListener('click', hideModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) hideModal();
    });

    // کد تخفیف
    applyDiscountBtn.addEventListener('click', () => {
        const code = discountInput.value.trim();
        if (code === '') {
            showModal('⚠️ لطفاً یک کد تخفیف وارد کنید.');
        } else {
            showModal(`🎉 کد تخفیف «${code}» با موفقیت اعمال شد!`);
        }
    });

    // نوار پایین
    document.getElementById('navCol')?.addEventListener('click', () => showModal('🤝 مشارکت در کار (دمو)'));
    document.getElementById('navReg')?.addEventListener('click', showRegister);
    document.getElementById('navLog')?.addEventListener('click', showLogin);
    //document.getElementById('navPan').addEventListener('click', () => showModal('📊 پنل کاربری'));

    // پروفایل
    //document.getElementById('profileBtn').addEventListener('click', () => showModal('👤 پروفایل کاربری'));

    // اخبار موبایل
    if (floatingNewsBtn) {
        floatingNewsBtn.addEventListener('click', () => {
            newsMobileModal.classList.add('active');
        });
        closeNewsMobileBtn.addEventListener('click', () => {
            newsMobileModal.classList.remove('active');
        });
        newsMobileModal.addEventListener('click', (e) => {
            if (e.target === newsMobileModal) newsMobileModal.classList.remove('active');
        });
    }


    // بستن auth با کلیک خارج
    registerSection.addEventListener('click', function (e) {
        if (e.target === registerSection) hideAllAuth();
    });
    loginSection.addEventListener('click', function (e) {
        if (e.target === loginSection) hideAllAuth();
    });

    // ==================== فرم ثبت‌نام ====================
    document.getElementById('registerForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const fullName = document.getElementById('fullNameInput').value.trim();
        const phone = document.getElementById('phoneInput').value.trim();

        if (fullName && phone.match(/09[0-9]{9}/)) {
            showModal(`✅ ثبت‌نام با موفقیت انجام شد!\n👤 ${fullName}\n📱 ${phone}`);
            hideAllAuth();
            this.reset();
        } else {
            showModal('⚠️ لطفاً نام کامل و شماره تلفن معتبر وارد کنید.');
        }
    });

    // ==================== فرم ورود ====================
    document.getElementById('loginForm').addEventListener('submit', function (e) {
        e.preventDefault();
        const username = document.getElementById('usernameInput').value.trim();
        const password = document.getElementById('passwordInput').value.trim();

        if (username && password.length >= 4) {
            showModal(`🔐 خوش آمدید ${username}!\n(حالت دمو: ورود شبیه‌سازی شد)`);
            hideAllAuth();
            this.reset();
        } else {
            showModal('⚠️ نام کاربری و رمز عبور (حداقل ۴ کاراکتر) را وارد کنید.');
        }
    });

    // نمایش/مخفی رمز عبور
    document.getElementById('togglePasswordBtn').addEventListener('click', function () {
        const passInput = document.getElementById('passwordInput');
        const type = passInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passInput.setAttribute('type', type);
        this.textContent = type === 'password' ? '👁️' : '🙈';
    });

    // Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModal();
            hideAllAuth();
            newsMobileModal.classList.remove('active');
        }
    });

    // تنظیمات اولیه برای نمایش صحیح در لود
    window.addEventListener('resize', () => {
        if (window.innerWidth > 1100) {
            newsMobileModal.classList.remove('active');
        }
    });

})();


//کنترل دکمه مدیریت پنل
let navPan = document.getElementById("navPan");
if (navPan) {
    navPan.addEventListener("click", () => {
        window.location.href = "admin-panel";
    })
}






