// static/js/admin_panel.js
(function () {
    // ==================== تنظیمات ====================
    const SITE_OWNERS = ['مهران سبزی', 'دانیال وفادارنژاد', 'ابوالفضل رحمانی'];
    const COMMISSION_RATE = 0.40;  // 👈 ۴۰ درصد
    const MIN_WALLET = 200000;     // 👈 حداقل موجودی
    
    // ==================== CSRF Token ====================
    function getCsrfToken() {
        // روش ۱: از cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        // روش ۲: از hidden input
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }
    
    const csrfToken = getCsrfToken();
    console.log('CSRF Token:', csrfToken ? '✅ موجود' : '❌ ناموجود');

    // ==================== داده‌ها ====================
    let projectsData = [];
    let operatorsData = [];
    let currentTab = 'projects';

    // ==================== المنت‌ها ====================
    const tabContent = document.getElementById('tabContent');
    const payConfirmModal = document.getElementById('payConfirmModal');
    const payConfirmMessage = document.getElementById('payConfirmMessage');
    const notificationModal = document.getElementById('notificationModal');
    const notificationMessage = document.getElementById('notificationMessage');

    let currentPayOperatorId = null;
    let currentPayOperatorName = null;
    let currentPayAmount = null;

    // ==================== توابع کمکی ====================
    function formatMoney(amount) {
        return Number(amount || 0).toLocaleString('fa-IR') + ' تومان';
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function showNotification(text, duration = 3000) {
        notificationMessage.textContent = text;
        notificationModal.classList.add('active');
        if (duration > 0) {
            setTimeout(hideNotification, duration);
        }
    }

    function hideNotification() {
        notificationModal.classList.remove('active');
    }

    function showPayConfirm(operatorId, operatorName, amount) {
        currentPayOperatorId = operatorId;
        currentPayOperatorName = operatorName;
        currentPayAmount = amount;
        payConfirmMessage.textContent = 
            `پرداخت ${formatMoney(amount)} به «${operatorName}»؟\n` +
            `${formatMoney(MIN_WALLET)} در کیف پول باقی می‌ماند.`;
        payConfirmModal.classList.add('active');
    }

    function hidePayConfirm() {
        payConfirmModal.classList.remove('active');
        currentPayOperatorId = null;
    }

    function showLoading() {
        tabContent.innerHTML = '<div style="text-align:center;padding:2rem;color:#b9c2e6;">⏳ در حال بارگذاری...</div>';
    }

    // ==================== API Calls ====================
    async function apiCall(url, options = {}) {
        const token = getCsrfToken();
        
        const response = await fetch(url, {
            ...options,
            headers: {
                'X-CSRFToken': token,
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...(options.headers || {})
            },
            credentials: 'same-origin'
        });
        
        // اگر CSRF خطا داد
        if (response.status === 403) {
            console.error('CSRF Error - reloading page...');
            location.reload();
            throw new Error('CSRF token expired');
        }
        
        return await response.json();
    }

    async function loadProjects() {
        try {
            const data = await apiCall('/api/admin/projects/');
            projectsData = data.projects || [];
            return projectsData;
        } catch (e) {
            console.error('Error:', e);
            showNotification('❌ خطا در بارگذاری پروژه‌ها');
            return [];
        }
    }

    async function loadOperators() {
        try {
            const data = await apiCall('/api/admin/operators/');
            operatorsData = data.operators || [];
            return operatorsData;
        } catch (e) {
            console.error('Error:', e);
            return [];
        }
    }

    async function loadRevenue() {
        try {
            return await apiCall('/api/admin/revenue/');
        } catch (e) {
            return {};
        }
    }

    async function loadOperatorsList() {
        try {
            const data = await apiCall('/api/admin/operators/list/');
            return data.operators || [];
        } catch (e) {
            return [];
        }
    }

    // ==================== عملیات‌ها ====================
    async function deleteProject(projectId, title) {
        if (!confirm(`آیا از حذف پروژه "${title}" مطمئن هستید؟\nاین عملیات قابل بازگشت نیست.`)) return;

        try {
            const result = await apiCall(`/api/admin/projects/${projectId}/delete/`, {
                method: 'POST',
                body: JSON.stringify({})
            });

            if (result.success) {
                showNotification('✅ ' + result.message, 2000);
                await loadProjects();
                updateStats();
                renderAllProjects();
            } else {
                showNotification('❌ ' + (result.error || 'خطا'));
            }
        } catch (e) {
            showNotification('❌ خطا در حذف پروژه');
        }
    }

    async function updateProjectStatus(projectId, newStatus) {
        try {
            const result = await apiCall(`/api/admin/projects/${projectId}/status/`, {
                method: 'POST',
                body: JSON.stringify({ status: newStatus })
            });

            if (result.success) {
                showNotification('✅ ' + result.message, 1500);
                await loadProjects();
                updateStats();
                renderAllProjects();
            } else {
                showNotification('❌ ' + (result.error || 'خطا'));
            }
        } catch (e) {
            showNotification('❌ خطا در تغییر وضعیت');
        }
    }

    async function assignOperator(projectId) {
        const operators = await loadOperatorsList();
        if (operators.length === 0) {
            showNotification('⚠️ هیچ اپراتوری یافت نشد');
            return;
        }

        let operatorList = operators.map((op, i) => 
            `${i + 1}. ${op.full_name} (${op.role})`
        ).join('\n');

        const choice = prompt(
            `لیست اپراتورها:\n${operatorList}\n\n` +
            `شماره اپراتور را وارد کنید (یا 0 برای حذف اپراتور):`
        );

        if (choice === null) return;

        const index = parseInt(choice) - 1;
        
        let operatorId = null;
        if (choice !== '0' && index >= 0 && index < operators.length) {
            operatorId = operators[index].id;
        }

        try {
            const result = await apiCall(`/api/admin/projects/${projectId}/assign/`, {
                method: 'POST',
                body: JSON.stringify({ operator_id: operatorId })
            });

            if (result.success) {
                showNotification('✅ ' + result.message, 1500);
                await loadProjects();
                updateStats();
                renderAllProjects();
            } else {
                showNotification('❌ ' + (result.error || 'خطا'));
            }
        } catch (e) {
            showNotification('❌ خطا در تخصیص اپراتور');
        }
    }

    async function editProject(projectId) {
        const project = projectsData.find(p => p.id === projectId);
        if (!project) return;

        const newTitle = prompt('عنوان جدید:', project.title);
        if (newTitle === null) return;

        const newPrice = prompt('قیمت جدید (تومان):', project.price);
        if (newPrice === null) return;

        try {
            const result = await apiCall(`/api/admin/projects/${projectId}/update/`, {
                method: 'POST',
                body: JSON.stringify({
                    title: newTitle.trim(),
                    price: parseInt(newPrice) || project.price
                })
            });

            if (result.success) {
                showNotification('✅ ' + result.message, 1500);
                await loadProjects();
                updateStats();
                renderAllProjects();
            } else {
                showNotification('❌ ' + (result.error || 'خطا'));
            }
        } catch (e) {
            showNotification('❌ خطا در ویرایش پروژه');
        }
    }

    async function payOperator(operatorId, operatorName, amount) {
        // بررسی حداقل موجودی
        if (amount <= MIN_WALLET) {
            showNotification(
                `⚠️ مبلغ قابل پرداخت (${formatMoney(amount)}) کمتر از حداقل موجودی (${formatMoney(MIN_WALLET)}) است`,
                4000
            );
            return;
        }
        
        showPayConfirm(operatorId, operatorName, amount - MIN_WALLET);
    }

    async function confirmPayOperator() {
        if (!currentPayOperatorId) return;

        try {
            const result = await apiCall(`/api/admin/operators/${currentPayOperatorId}/pay/`, {
                method: 'POST',
                body: JSON.stringify({})
            });

            if (result.success) {
                showNotification(
                    `✅ ${result.message}\n` +
                    `💰 پرداخت شده: ${formatMoney(result.paid_amount)}\n` +
                    `🏦 موجودی جدید: ${formatMoney(result.new_balance)}`,
                    5000
                );
                await loadOperators();
                renderOperators();
            } else {
                showNotification('❌ ' + (result.error || 'خطا'), 4000);
            }
            hidePayConfirm();
        } catch (e) {
            showNotification('❌ خطا در پرداخت');
            hidePayConfirm();
        }
    }

    // ==================== رندر ====================
    function updateStats() {
        document.getElementById('totalProjects').textContent = projectsData.length.toLocaleString('fa-IR');
        document.getElementById('activeProjects').textContent = projectsData.filter(p =>
            ['pending', 'accepted', 'in_progress'].includes(p.status)
        ).length.toLocaleString('fa-IR');
        document.getElementById('doneProjects').textContent = projectsData.filter(p =>
            ['completed', 'delivered'].includes(p.status)
        ).length.toLocaleString('fa-IR');
        document.getElementById('totalOperators').textContent = operatorsData.length.toLocaleString('fa-IR');
    }

    function getStatusSelect(project) {
        const statuses = [
            { value: 'pending', text: '⏳ در انتظار' },
            { value: 'accepted', text: '✅ پذیرفته شده' },
            { value: 'in_progress', text: '⚙️ در حال انجام' },
            { value: 'completed', text: '🎉 آماده تحویل' },
            { value: 'delivered', text: '📦 تحویل داده شده' },
            { value: 'cancelled', text: '❌ لغو شده' },
            { value: 'rejected', text: '🚫 رد شده' },
        ];

        return `
            <select onchange="updateStatus('${project.id}', this.value)" 
                    style="background:rgba(255,255,255,0.1);color:white;border:1px solid rgba(255,255,255,0.2);
                    border-radius:1rem;padding:0.3rem 0.8rem;font-size:0.75rem;cursor:pointer;">
                ${statuses.map(s => `
                    <option value="${s.value}" ${project.status === s.value ? 'selected' : ''}
                            style="background:#1a1c2e;color:white;">
                        ${s.text}
                    </option>
                `).join('')}
            </select>
        `;
    }

    function renderAllProjects() {
        if (projectsData.length === 0) {
            tabContent.innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div><p>هیچ پروژه‌ای وجود ندارد</p></div>';
            return;
        }

        tabContent.innerHTML = projectsData.map(p => {
            const commission = Math.floor(p.price * COMMISSION_RATE);
            const isOwner = p.operator_name && (SITE_OWNERS.includes(p.operator_name) || p.is_owner);
            const netPayable = p.price - commission;

            return `
            <div class="project-card">
              <div class="project-header">
                <div class="project-icon">📋</div>
                <div class="project-info">
                  <div class="project-title">
                    ${escapeHtml(p.title)} 
                    ${isOwner ? '<span class="owner-tag">مالک</span>' : ''}
                  </div>
                  <div class="project-desc">${escapeHtml(p.description || '')}</div>
                  <div style="font-size:0.7rem;color:#a78bfa;">کد: ${p.tracking_code}</div>
                </div>
                ${getStatusSelect(p)}
              </div>

              <div class="project-detail-row">
                <span class="project-detail-label">👤 مشتری:</span>
                <span>${escapeHtml(p.customer_name)}</span>
              </div>

              <div class="project-detail-row">
                <span class="project-detail-label">🧑‍💻 اپراتور:</span>
                <span>${p.operator_name || '❌ تعیین نشده'}</span>
                ${isOwner ? '<span class="owner-tag">صاحب سایت</span>' : ''}
                <button onclick="assignOp('${p.id}')" 
                        style="background:#6366f1;color:white;border:none;padding:0.2rem 0.8rem;
                        border-radius:1rem;font-size:0.7rem;cursor:pointer;margin-right:0.5rem;">
                  ✏️ تغییر
                </button>
              </div>

              <div class="project-detail-row">
                <span class="project-detail-label">💰 قیمت:</span>
                <span class="project-price">${formatMoney(p.price)}</span>
                <span class="commission-badge">🏛️ کمیسیون ${COMMISSION_RATE * 100}٪: ${formatMoney(commission)}</span>
                ${p.operator_name && !isOwner ? `<span class="commission-badge">💵 قابل پرداخت: ${formatMoney(netPayable)}</span>` : ''}
                ${isOwner ? '<span class="commission-badge" style="background:rgba(251,191,36,0.2);color:#fbbf24;">👑 بدون کمیسیون</span>' : ''}
              </div>

              <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:0.5rem;">
                <button onclick="editProj('${p.id}')" 
                        style="background:#6366f1;color:white;border:none;padding:0.4rem 1rem;
                        border-radius:1.5rem;font-size:0.75rem;cursor:pointer;">
                  ✏️ ویرایش
                </button>
                <button onclick="deleteProj('${p.id}', '${escapeHtml(p.title).replace(/'/g, "\\'")}')" 
                        style="background:#ef4444;color:white;border:none;padding:0.4rem 1rem;
                        border-radius:1.5rem;font-size:0.75rem;cursor:pointer;">
                  🗑️ حذف
                </button>
              </div>
            </div>
          `;
        }).join('');
    }

    function renderOperators() {
        if (operatorsData.length === 0) {
            tabContent.innerHTML = '<div class="empty-state"><div class="empty-icon">👥</div><p>هیچ اپراتوری یافت نشد</p></div>';
            return;
        }

        const sorted = [...operatorsData].sort((a, b) => {
            if (a.is_owner && !b.is_owner) return -1;
            if (!a.is_owner && b.is_owner) return 1;
            return b.net_payable - a.net_payable;
        });

        tabContent.innerHTML = sorted.map(op => {
            const canPay = op.can_pay && op.net_payable > MIN_WALLET;
            
            return `
            <div class="operator-salary-card ${op.is_owner ? 'owner' : ''}">
              <div class="op-avatar ${op.is_owner ? 'owner-avatar' : 'normal-avatar'}">
                ${op.is_owner ? '👑' : '🧑‍💻'}
              </div>
              <div class="op-details">
                <div class="op-name ${op.is_owner ? 'owner-name' : ''}">
                  ${escapeHtml(op.name)}
                  ${op.is_owner ? '<span class="owner-tag">صاحب سایت</span>' : ''}
                </div>
                <div class="op-stats">
                  📋 ${op.completed_jobs} کار | 
                  💰 درآمد کل: ${formatMoney(op.total_earned)} |
                  🏛️ کمیسیون (${COMMISSION_RATE * 100}٪): ${formatMoney(op.commission)}
                </div>
                <div class="op-stats" style="color:#4ade80;">
                  💵 خالص پرداختی: ${formatMoney(op.net_payable)} |
                  🏦 موجودی کیف پول: ${formatMoney(op.wallet_balance)}
                </div>
              </div>
              <div class="op-earnings">
                ${formatMoney(op.net_payable)}
                <div class="op-commission" style="font-size:0.7rem;">
                  ${op.net_payable > MIN_WALLET ? 
                    `📤 قابل برداشت: ${formatMoney(op.net_payable - MIN_WALLET)}` : 
                    `⚠️ کمتر از حداقل (${formatMoney(MIN_WALLET)})`}
                </div>
              </div>
              <button
                class="pay-btn ${!canPay ? 'paid' : ''}"
                onclick="${canPay ? `payOp('${op.id}', '${escapeHtml(op.name).replace(/'/g, "\\'")}', ${op.net_payable})` : ''}"
                ${!canPay ? 'disabled' : ''}
              >
                ${op.is_paid ? '✅ تسویه شد' : 
                  op.net_payable <= MIN_WALLET ? `🔒 زیر ${formatMoney(MIN_WALLET)}` : 
                  '💳 پرداخت'}
              </button>
            </div>
          `;
        }).join('');
    }

    async function renderRevenue() {
        const revenue = await loadRevenue();

        tabContent.innerHTML = `
          <div class="revenue-section">
            <div class="revenue-title">💰 درآمد کل سایت (کمیسیون ${revenue.commission_rate || 40}٪)</div>
            <div class="revenue-grid">
              <div class="revenue-card">
                <div class="revenue-value">${formatMoney(revenue.monthly_revenue || 0)}</div>
                <div class="revenue-label">📅 درآمد ماهانه</div>
              </div>
              <div class="revenue-card">
                <div class="revenue-value gold">${formatMoney(revenue.yearly_revenue || 0)}</div>
                <div class="revenue-label">📆 درآمد سالانه (تخمینی)</div>
              </div>
              <div class="revenue-card">
                <div class="revenue-value gold">${formatMoney(revenue.total_commission || 0)}</div>
                <div class="revenue-label">🏛️ کل کمیسیون</div>
              </div>
              <div class="revenue-card">
                <div class="revenue-value">${formatMoney(revenue.actual_commission || 0)}</div>
                <div class="revenue-label">💵 کمیسیون قابل تقسیم</div>
              </div>
            </div>
          </div>

          <div class="revenue-section" style="margin-top:1rem;">
            <div class="revenue-title">👑 سهم صاحبان سایت</div>
            <div class="revenue-grid">
              ${(revenue.owners || []).map(owner => `
                <div class="revenue-card" style="border-color:rgba(251,191,36,0.3);">
                  <div style="font-size:1.2rem;font-weight:700;color:#fbbf24;">👑 ${escapeHtml(owner.name)}</div>
                  <div class="revenue-value" style="font-size:1.2rem;">${formatMoney(owner.share)}</div>
                  <div class="revenue-label">سهم از کمیسیون</div>
                  <div style="font-size:0.8rem;color:#4ade80;margin-top:0.4rem;">💼 درآمد کارهای خود: ${formatMoney(owner.own_revenue)}</div>
                  <div style="font-size:0.9rem;font-weight:700;color:#fbbf24;margin-top:0.2rem;">👑 کل: ${formatMoney(owner.total)}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
    }

    // ==================== توابع گلوبال ====================
    window.deleteProj = deleteProject;
    window.updateStatus = updateProjectStatus;
    window.assignOp = assignOperator;
    window.editProj = editProject;
    window.payOp = payOperator;

    // ==================== ایونت‌ها ====================
    document.getElementById('payConfirmYes').addEventListener('click', confirmPayOperator);
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

    // ==================== تب‌ها ====================
    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        showLoading();
        
        switch (tab) {
            case 'projects': renderAllProjects(); break;
            case 'operators': renderOperators(); break;
            case 'revenue': renderRevenue(); break;
        }
    }
    window.switchTab = switchTab;

    // ==================== لود اولیه ====================
    async function init() {
        console.log('🚀 Admin Panel Loading...');
        console.log('CSRF Token:', csrfToken ? '✅' : '❌');
        
        await Promise.all([loadProjects(), loadOperators()]);
        updateStats();
        renderAllProjects();
        console.log('✅ Admin Panel Ready');
    }

    init();

})();