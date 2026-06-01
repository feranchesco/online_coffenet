(function () {
    // ==================== صاحبان سایت ====================
    const SITE_OWNERS = ['مهران سبزی', 'دانیال وفادارنژاد', 'ابوالفضل رحمانی'];
    const COMMISSION_RATE = 0.20; // ۲۰٪ کمیسیون سایت

    // ==================== دیتای پروژه‌ها ====================
    const projectsData = [
        {
            id: 1,
            icon: "🖨️",
            title: "پرینت و اسکن",
            desc: "پرینت ۵۰ برگ رنگی",
            price: 50000,
            status: "done",
            operator: "رضا احمدی",
            customer: "علی محمدی"
        },
        {
            id: 2,
            icon: "🎓",
            title: "تایپ پایان‌نامه",
            desc: "۸۰ صفحه تایپ",
            price: 120000,
            status: "done",
            operator: "مریم حسینی",
            customer: "محمد حسینی"
        },
        {
            id: 3,
            icon: "✍️",
            title: "طراحی رزومه",
            desc: "رزومه حرفه‌ای",
            price: 80000,
            status: "done",
            operator: "سارا رضایی",
            customer: "زهرا محمدی"
        },
        {
            id: 4,
            icon: "📄",
            title: "کپی و صحافی",
            desc: "۲۰۰ برگ + ۳ جلد",
            price: 90000,
            status: "done",
            operator: "رضا احمدی",
            customer: "امیر کریمی"
        },
        {
            id: 5,
            icon: "🌐",
            title: "ثبت‌نام اینترنتی",
            desc: "آزمون کارشناسی ارشد",
            price: 25000,
            status: "done",
            operator: "مریم حسینی",
            customer: "سارا محمدی"
        },
        {
            id: 6,
            icon: "🏛️",
            title: "خدمات دولتی",
            desc: "استعلام مدرک",
            price: 15000,
            status: "done",
            operator: "ابوالفضل رحمانی",
            customer: "حسین رضایی"
        },
        {
            id: 7,
            icon: "🖨️",
            title: "اسکن مدارک",
            desc: "اسکن ۳۰ برگ",
            price: 30000,
            status: "done",
            operator: "مهران سبزی",
            customer: "نرگس احمدی"
        },
        {
            id: 8,
            icon: "📦",
            title: "پیگیری مرسوله",
            desc: "رهگیری پستی",
            price: 10000,
            status: "progress",
            operator: "رضا احمدی",
            customer: "علی کریمی"
        },
        {
            id: 9,
            icon: "🎓",
            title: "صحافی جزوه",
            desc: "صحافی ۵ جلد",
            price: 60000,
            status: "progress",
            operator: "مریم حسینی",
            customer: "فاطمه موسوی"
        },
        {
            id: 10,
            icon: "✍️",
            title: "تایپ فارسی",
            desc: "۲۰ صفحه تایپ",
            price: 40000,
            status: "pending",
            operator: null,
            customer: "امید جعفری"
        },
        {
            id: 11,
            icon: "🖨️",
            title: "پرینت بنر",
            desc: "بنر ۲×۱ متر",
            price: 150000,
            status: "done",
            operator: "دانیال وفادارنژاد",
            customer: "شرکت آریا"
        },
        {
            id: 12,
            icon: "⚙️",
            title: "خدمات سفارشی",
            desc: "طراحی لوگو",
            price: 200000,
            status: "done",
            operator: "ابوالفضل رحمانی",
            customer: "فروشگاه کالا"
        }
    ];

    // ==================== وضعیت پرداخت اپراتورها ====================
    let operatorPayments = {};

    // ==================== المنت‌ها ====================
    const tabContent = document.getElementById('tabContent');
    const payConfirmModal = document.getElementById('payConfirmModal');
    const payConfirmMessage = document.getElementById('payConfirmMessage');
    const notificationModal = document.getElementById('notificationModal');
    const notificationMessage = document.getElementById('notificationMessage');

    let currentPayOperator = null;
    let currentTab = 'projects';

    // ==================== توابع کمکی ====================
    function formatMoney(amount) {
        return amount.toLocaleString('fa-IR') + ' تومان';
    }

    function showNotification(text) {
        notificationMessage.textContent = text;
        notificationModal.classList.add('active');
    }

    function hideNotification() {
        notificationModal.classList.remove('active');
    }

    function showPayConfirm(operatorName, amount) {
        currentPayOperator = operatorName;
        payConfirmMessage.textContent = `پرداخت ${formatMoney(amount)} به «${operatorName}»؟\nپس از پرداخت، حساب این فرد صفر می‌شود.`;
        payConfirmModal.classList.add('active');
    }

    function hidePayConfirm() {
        payConfirmModal.classList.remove('active');
        currentPayOperator = null;
    }

    // ==================== محاسبات ====================
    function getOperatorEarnings() {
        const earnings = {};

        projectsData.forEach(project => {
            if (project.status === 'done' && project.operator) {
                if (!earnings[project.operator]) {
                    earnings[project.operator] = {
                        totalEarned: 0,
                        commission: 0,
                        netPayable: 0,
                        jobCount: 0,
                        isOwner: SITE_OWNERS.includes(project.operator),
                        paid: operatorPayments[project.operator] || false
                    };
                }

                const commission = Math.floor(project.price * COMMISSION_RATE);
                const netAmount = project.price - commission;

                earnings[project.operator].totalEarned += project.price;
                earnings[project.operator].commission += commission;
                earnings[project.operator].netPayable += netAmount;
                earnings[project.operator].jobCount += 1;
            }
        });

        return earnings;
    }

    function getTotalCommission() {
        return projectsData
            .filter(p => p.status === 'done' && p.operator)
            .reduce((sum, p) => sum + Math.floor(p.price * COMMISSION_RATE), 0);
    }

    function getOwnerShares() {
        const totalCommission = getTotalCommission();
        const ownerJobs = projectsData.filter(p =>
            p.status === 'done' && SITE_OWNERS.includes(p.operator)
        );

        // کمیسیون کارهای صاحبان (خودشان انجام داده‌اند = بدون کمیسیون)
        const ownerJobPrices = ownerJobs.reduce((sum, p) => sum + p.price, 0);
        const ownerCommissionExempt = Math.floor(ownerJobPrices * COMMISSION_RATE);

        // کمیسیون واقعی (فقط از کارهای غیر صاحبان)
        const actualCommission = totalCommission - ownerCommissionExempt;

        // تقسیم بین ۳ صاحب سایت
        const sharePerOwner = Math.floor(actualCommission / 3);

        return {
            totalCommission,
            ownerCommissionExempt,
            actualCommission,
            sharePerOwner,
            owners: SITE_OWNERS.map(name => ({
                name,
                share: sharePerOwner
            }))
        };
    }

    function getMonthlyRevenue() {
        // شبیه‌سازی: فرض می‌کنیم همه پروژه‌ها در ماه جاری هستند
        const doneProjects = projectsData.filter(p => p.status === 'done');
        return doneProjects.reduce((sum, p) => sum + p.price, 0);
    }

    function getYearlyRevenue() {
        // شبیه‌سازی: ۱۲ برابر درآمد ماهانه
        return getMonthlyRevenue() * 12;
    }

    function updateStats() {
        document.getElementById('totalProjects').textContent = projectsData.length.toLocaleString('fa-IR');
        document.getElementById('activeProjects').textContent = projectsData.filter(p => p.status === 'progress').length.toLocaleString('fa-IR');
        document.getElementById('doneProjects').textContent = projectsData.filter(p => p.status === 'done').length.toLocaleString('fa-IR');

        const earnings = getOperatorEarnings();
        document.getElementById('totalOperators').textContent = Object.keys(earnings).length.toLocaleString('fa-IR');
    }

    // ==================== رندر ====================
    function renderAllProjects() {
        if (projectsData.length === 0) {
            tabContent.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>هیچ پروژه‌ای وجود ندارد</p></div>`;
            return;
        }

        tabContent.innerHTML = projectsData.map(p => {
            const statusMap = {
                'pending': {text: '⏳ در انتظار', class: 'status-pending'},
                'progress': {text: '⚙️ در حال انجام', class: 'status-progress'},
                'done': {text: '✅ تکمیل شده', class: 'status-done'}
            };
            const status = statusMap[p.status];
            const commission = Math.floor(p.price * COMMISSION_RATE);
            const isOwner = p.operator && SITE_OWNERS.includes(p.operator);

            return `
            <div class="project-card">
              <div class="project-header">
                <div class="project-icon">${p.icon}</div>
                <div class="project-info">
                  <div class="project-title">${p.title} ${isOwner ? '<span class="owner-tag">مالک</span>' : ''}</div>
                  <div class="project-desc">${p.desc}</div>
                </div>
                <span class="project-status ${status.class}">${status.text}</span>
              </div>

              <div class="project-detail-row">
                <span class="project-detail-label">👤 مشتری:</span>
                <span>${p.customer}</span>
              </div>

              <div class="project-detail-row">
                <span class="project-detail-label">🧑‍💻 اپراتور:</span>
                <span>${p.operator || '❌ تعیین نشده'}</span>
                ${isOwner ? '<span class="owner-tag">صاحب سایت</span>' : ''}
              </div>

              <div class="project-detail-row">
                <span class="project-detail-label">💰 قیمت:</span>
                <span class="project-price">${formatMoney(p.price)}</span>
                <span class="commission-badge">🏛️ کمیسیون: ${formatMoney(commission)}</span>
                ${p.operator && !isOwner ? `<span class="commission-badge">💵 قابل پرداخت: ${formatMoney(p.price - commission)}</span>` : ''}
                ${isOwner ? '<span class="commission-badge" style="background:rgba(251,191,36,0.2);color:#fbbf24;">👑 بدون کمیسیون</span>' : ''}
              </div>
            </div>
          `;
        }).join('');
    }

    function renderOperators() {
        const earnings = getOperatorEarnings();
        const operatorNames = Object.keys(earnings);

        if (operatorNames.length === 0) {
            tabContent.innerHTML = `<div class="empty-state"><div class="empty-icon">👥</div><p>هیچ اپراتوری یافت نشد</p></div>`;
            return;
        }

        // مرتب‌سازی: صاحبان اول
        operatorNames.sort((a, b) => {
            const aOwner = SITE_OWNERS.includes(a) ? 0 : 1;
            const bOwner = SITE_OWNERS.includes(b) ? 0 : 1;
            return aOwner - bOwner;
        });

        tabContent.innerHTML = operatorNames.map(name => {
            const data = earnings[name];
            const isOwner = data.isOwner;
            const paid = data.paid;

            return `
            <div class="operator-salary-card ${isOwner ? 'owner' : ''}">
              <div class="op-avatar ${isOwner ? 'owner-avatar' : 'normal-avatar'}">
                ${isOwner ? '👑' : '🧑‍💻'}
              </div>
              <div class="op-details">
                <div class="op-name ${isOwner ? 'owner-name' : ''}">
                  ${name}
                  ${isOwner ? '<span class="owner-tag">صاحب سایت</span>' : ''}
                </div>
                <div class="op-stats">
                  📋 ${data.jobCount} کار انجام شده
                  ${!isOwner ? `| 🏛️ کمیسیون: ${formatMoney(data.commission)}` : '| 👑 معاف از کمیسیون'}
                </div>
              </div>
              <div class="op-earnings">
                ${formatMoney(data.netPayable)}
                <div class="op-commission">
                  ${paid ? '✅ پرداخت شده' : '📌 در انتظار پرداخت'}
                </div>
              </div>
              <button
                class="pay-btn ${paid ? 'paid' : ''}"
                onclick="${paid ? '' : `window.payOperator('${name}', ${data.netPayable})`}"
                ${paid ? 'disabled' : ''}
              >
                ${paid ? '✅ تسویه شد' : '💳 پرداخت'}
              </button>
            </div>
          `;
        }).join('');
    }

    function renderRevenue() {
        const monthlyRevenue = getMonthlyRevenue();
        const yearlyRevenue = getYearlyRevenue();
        const totalCommission = getTotalCommission();
        const ownerShares = getOwnerShares();
        const earnings = getOperatorEarnings();

        // محاسبه کمیسیون واقعی (فقط از غیر صاحبان)
        const nonOwnerProjects = projectsData.filter(p =>
            p.status === 'done' && p.operator && !SITE_OWNERS.includes(p.operator)
        );
        const actualCommission = nonOwnerProjects.reduce((sum, p) => sum + Math.floor(p.price * COMMISSION_RATE), 0);

        tabContent.innerHTML = `
          <div class="revenue-section">
            <div class="revenue-title">💰 درآمد کل سایت</div>
            <div class="revenue-grid">
              <div class="revenue-card">
                <div class="revenue-value">${formatMoney(monthlyRevenue)}</div>
                <div class="revenue-label">📅 درآمد ماهانه</div>
              </div>
              <div class="revenue-card">
                <div class="revenue-value gold">${formatMoney(yearlyRevenue)}</div>
                <div class="revenue-label">📆 درآمد سالانه (تخمینی)</div>
              </div>
              <div class="revenue-card">
                <div class="revenue-value gold">${formatMoney(totalCommission)}</div>
                <div class="revenue-label">🏛️ کل کمیسیون (۲۰٪)</div>
              </div>
              <div class="revenue-card">
                <div class="revenue-value">${formatMoney(actualCommission)}</div>
                <div class="revenue-label">💵 کمیسیون قابل تقسیم</div>
              </div>
            </div>
          </div>

          <div class="revenue-section" style="margin-top:1rem;">
            <div class="revenue-title">👑 سهم صاحبان سایت (از کمیسیون ۲۰٪)</div>
            <p style="text-align:center;color:#b9c2e6;font-size:0.8rem;margin-bottom:1rem;">
              📌 کارهای انجام شده توسط صاحبان سایت شامل کمیسیون نمی‌شوند.<br>
              💰 کمیسیون کارهای بقیه اپراتورها بین سه صاحب سایت تقسیم می‌شود.
            </p>

            <div class="revenue-grid">
              ${ownerShares.owners.map(owner => {
            // اضافه کردن درآمد کارهای خود صاحب
            const ownerJobs = projectsData.filter(p =>
                p.status === 'done' && p.operator === owner.name
            );
            const ownerOwnEarnings = ownerJobs.reduce((sum, p) => sum + p.price, 0);
            const totalOwnerIncome = owner.share + ownerOwnEarnings;

            return `
                  <div class="revenue-card" style="border-color:rgba(251,191,36,0.3);">
                    <div style="font-size:1.2rem;font-weight:700;color:#fbbf24;">👑 ${owner.name}</div>
                    <div class="revenue-value" style="font-size:1.2rem;">${formatMoney(owner.share)}</div>
                    <div class="revenue-label">سهم از کمیسیون</div>
                    <div style="font-size:0.8rem;color:#4ade80;margin-top:0.4rem;">💼 درآمد کارهای خود: ${formatMoney(ownerOwnEarnings)}</div>
                    <div style="font-size:0.9rem;font-weight:700;color:#fbbf24;margin-top:0.2rem;">👑 کل: ${formatMoney(totalOwnerIncome)}</div>
                  </div>
                `;
        }).join('')}
            </div>

            <div style="text-align:center;margin-top:1rem;padding:1rem;background:rgba(0,0,0,0.3);border-radius:1.5rem;">
              <span style="color:#fbbf24;font-weight:700;">🏛️ کل کمیسیون تقسیمی: ${formatMoney(actualCommission)}</span>
              <br>
              <span style="color:#b9c2e6;font-size:0.75rem;">(بین ۳ نفر: ${formatMoney(ownerShares.sharePerOwner)} هر نفر)</span>
            </div>
          </div>

          <div class="revenue-section" style="margin-top:1rem;">
            <div class="revenue-title">📊 خلاصه پرداختی به اپراتورها</div>
            ${Object.keys(earnings).length === 0 ? '<p style="text-align:center;color:#b9c2e6;">هیچ اپراتوری وجود ندارد</p>' : ''}
            ${Object.keys(earnings).map(name => {
            const data = earnings[name];
            return `
                <div class="operator-salary-card ${data.isOwner ? 'owner' : ''}" style="margin-bottom:0.5rem;">
                  <div class="op-avatar ${data.isOwner ? 'owner-avatar' : 'normal-avatar'}">
                    ${data.isOwner ? '👑' : '🧑‍💻'}
                  </div>
                  <div class="op-details">
                    <div class="op-name ${data.isOwner ? 'owner-name' : ''}">${name}</div>
                    <div class="op-stats">📋 ${data.jobCount} کار | 🏛️ کمیسیون: ${formatMoney(data.commission)}</div>
                  </div>
                  <div class="op-earnings">${formatMoney(data.netPayable)}</div>
                </div>
              `;
        }).join('')}
          </div>
        `;
    }

    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        switch (tab) {
            case 'projects':
                renderAllProjects();
                break;
            case 'operators':
                renderOperators();
                break;
            case 'revenue':
                renderRevenue();
                break;
        }
    }

    // ==================== توابع گلوبال ====================
    window.payOperator = function (operatorName, amount) {
        showPayConfirm(operatorName, amount);
    };

    // ==================== ایونت‌ها ====================
    document.getElementById('payConfirmYes').addEventListener('click', () => {
        if (currentPayOperator) {
            operatorPayments[currentPayOperator] = true;
            showNotification(`✅ پرداخت به «${currentPayOperator}» با موفقیت انجام شد. حساب ایشان صفر شد.`);
            hidePayConfirm();
            if (currentTab === 'operators') renderOperators();
        }
    });

    document.getElementById('payConfirmNo').addEventListener('click', hidePayConfirm);
    payConfirmModal.addEventListener('click', (e) => {
        if (e.target === payConfirmModal) hidePayConfirm();
    });

    document.getElementById('closeNotificationBtn').addEventListener('click', hideNotification);
    notificationModal.addEventListener('click', (e) => {
        if (e.target === notificationModal) hideNotification();
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            switchTab(this.dataset.tab);
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hidePayConfirm();
            hideNotification();
        }
    });

    // لود اولیه
    updateStats();
    switchTab('projects');

})();


