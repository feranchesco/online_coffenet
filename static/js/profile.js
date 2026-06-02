// script 2
(function () {
    // ==================== دیتای سفارشات ====================
    const ordersData = [
        {
            id: 1,
            icon: "🖨️",
            title: "پرینت و اسکن",
            desc: "پرینت ۵۰ برگ رنگی A4",
            status: "progress",
            statusText: "در حال انجام",
            statusClass: "status-progress",
            operator: "رضا احمدی",
            operatorRole: "اپراتور چاپ",
            price: "۵۰,۰۰۰ تومان",
            isPaid: true,
            chat: [
                {type: "operator", text: "سلام، فایل‌ها رو دریافت کردم"},
                {type: "user", text: "ممنون، تا کی آماده میشه؟"},
                {type: "operator", text: "تا ۲ ساعت دیگه تحویل میدم"}
            ],
            hasFile: false
        },
        {
            id: 2,
            icon: "🎓",
            title: "خدمات دانشجویی",
            desc: "تایپ پایان‌نامه ۸۰ صفحه",
            status: "progress",
            statusText: "در حال انجام",
            statusClass: "status-progress",
            operator: "مریم حسینی",
            operatorRole: "تایپیست",
            price: "۱۲۰,۰۰۰ تومان",
            isPaid: false,
            chat: [
                {type: "operator", text: "سلام، کار رو شروع کردم"},
                {type: "user", text: "عالیه، فرمت خاصی نیاز داره؟"}
            ],
            hasFile: false
        },
        {
            id: 3,
            icon: "✍️",
            title: "تایپ و طراحی",
            desc: "طراحی رزومه حرفه‌ای",
            status: "done",
            statusText: "آماده تحویل",
            statusClass: "status-done",
            operator: "سارا رضایی",
            operatorRole: "طراح گرافیک",
            price: "۸۰,۰۰۰ تومان",
            isPaid: true,
            chat: [
                {type: "operator", text: "رزومه آماده است"},
                {type: "user", text: "ممنون، دانلود میکنم"}
            ],
            hasFile: true
        },
        {
            id: 4,
            icon: "📦",
            title: "پیگیری سفارشات",
            desc: "رهگیری مرسوله پستی",
            status: "pending",
            statusText: "در انتظار",
            statusClass: "status-pending",
            operator: "در انتظار پذیرش",
            operatorRole: "",
            price: "۱۰,۰۰۰ تومان",
            isPaid: false,
            chat: [],
            hasFile: false
        }
    ];

    const historyOrders = [
        {icon: "🖨️", title: "پرینت جزوه", date: "۱۴۰۲/۰۸/۱۵", price: "۳۵,۰۰۰ تومان"},
        {icon: "🌐", title: "ثبت نام کنکور", date: "۱۴۰۲/۰۸/۱۰", price: "۲۵,۰۰۰ تومان"},
        {icon: "🏛️", title: "استعلام مدرک", date: "۱۴۰۲/۰۸/۰۵", price: "۱۵,۰۰۰ تومان"},
        {icon: "🎓", title: "صحافی پایان‌نامه", date: "۱۴۰۲/۰۷/۲۸", price: "۹۰,۰۰۰ تومان"}
    ];

    // ==================== المنت‌ها ====================
    const tabContent = document.getElementById('tabContent');
    const modalOverlay = document.getElementById('modalOverlay');
    const modalMessage = document.getElementById('modalMessage');
    const modalIcon = document.getElementById('modalIcon');
    const paymentModal = document.getElementById('paymentModal');
    const paymentMessage = document.getElementById('paymentMessage');

    let currentPaymentOrderId = null;
    let currentTab = 'active';

    // ==================== توابع ====================
    function showModal(text, icon = '✨') {
        modalMessage.textContent = text;
        modalIcon.textContent = icon;
        modalOverlay.classList.add('active');
    }

    function hideModal() {
        modalOverlay.classList.remove('active');
    }

    function showPaymentModal(orderId, price) {
        currentPaymentOrderId = orderId;
        paymentMessage.textContent = `پرداخت مبلغ ${price} برای این سفارش؟`;
        paymentModal.classList.add('active');
    }

    function hidePaymentModal() {
        paymentModal.classList.remove('active');
        currentPaymentOrderId = null;
    }

    // ==================== رندر محتوا ====================
    function renderActiveOrders() {
        const activeOrders = ordersData.filter(o => o.status !== 'done');
        if (activeOrders.length === 0) {
            tabContent.innerHTML = `
            <div style="text-align:center; padding:2rem; color:#b9c2e6;">
              <div style="font-size:3rem;">📭</div>
              <p>هیچ سفارش فعالی ندارید</p>
            </div>
          `;
            return;
        }

        tabContent.innerHTML = activeOrders.map(order => `
          <div class="order-card" style="margin-bottom:1rem;">
            <div class="order-header">
              <div class="order-icon">${order.icon}</div>
              <div class="order-info">
                <div class="order-title">${order.title}</div>
                <div class="order-desc">${order.desc}</div>
              </div>
              <span class="order-status ${order.statusClass}">${order.statusText}</span>
            </div>

            <div class="operator-info">
              <div class="operator-avatar">${order.operator !== 'در انتظار پذیرش' ? '🧑‍💻' : '⏳'}</div>
              <div>
                <div class="operator-name">${order.operator}</div>
                ${order.operatorRole ? `<div class="operator-role">${order.operatorRole}</div>` : ''}
              </div>
            </div>

            ${order.chat.length > 0 ? `
              <div class="chat-section" id="chat-${order.id}">
                ${order.chat.map(msg => `
                  <div class="chat-msg ${msg.type === 'user' ? 'chat-user' : 'chat-operator'}">
                    ${msg.text}
                  </div>
                `).join('')}
              </div>
              <div class="chat-input-row">
                <input type="text" class="chat-input" id="chatInput-${order.id}" placeholder="پیام خود را بنویسید...">
                <button class="chat-send-btn" onclick="window.sendChat(${order.id})">ارسال</button>
              </div>
            ` : `
              <div style="text-align:center; color:#b9c2e6; font-size:0.8rem; padding:0.5rem;">
                چت پس از پذیرش سفارش فعال می‌شود
              </div>
            `}

            <div class="order-actions">
              <span class="price-tag">💲 ${order.price}</span>
              ${order.isPaid ? `
                <button class="pay-btn paid">✅ پرداخت شده</button>
              ` : `
                <button class="pay-btn" onclick="window.showPayment(${order.id}, '${order.price}')">💳 پرداخت</button>
              `}
              ${order.hasFile && order.isPaid ? `
                <button class="download-btn" onclick="window.downloadFile(${order.id})">📥 دانلود نتیجه</button>
              ` : order.hasFile && !order.isPaid ? `
                <button class="download-btn" disabled>🔒 ابتدا پرداخت کنید</button>
              ` : `
                <button class="download-btn" disabled>📥 فایل آماده نیست</button>
              `}
            </div>
          </div>
        `).join('');
    }

    function renderCompletedOrders() {
        const completedOrders = ordersData.filter(o => o.status === 'done');
        if (completedOrders.length === 0) {
            tabContent.innerHTML = `
            <div style="text-align:center; padding:2rem; color:#b9c2e6;">
              <div style="font-size:3rem;">📭</div>
              <p>سفارش تکمیل شده‌ای ندارید</p>
            </div>
          `;
            return;
        }

        tabContent.innerHTML = completedOrders.map(order => `
          <div class="order-card" style="margin-bottom:1rem;">
            <div class="order-header">
              <div class="order-icon">${order.icon}</div>
              <div class="order-info">
                <div class="order-title">${order.title}</div>
                <div class="order-desc">${order.desc}</div>
              </div>
              <span class="order-status ${order.statusClass}">${order.statusText}</span>
            </div>

            <div class="operator-info">
              <div class="operator-avatar">🧑‍💻</div>
              <div>
                <div class="operator-name">${order.operator}</div>
                ${order.operatorRole ? `<div class="operator-role">${order.operatorRole}</div>` : ''}
              </div>
            </div>

            <div class="order-actions">
              <span class="price-tag">💲 ${order.price}</span>
              ${order.isPaid ? `
                <button class="pay-btn paid">✅ پرداخت شده</button>
                ${order.hasFile ? `
                  <button class="download-btn" onclick="window.downloadFile(${order.id})">📥 دانلود نتیجه</button>
                ` : ''}
              ` : `
                <button class="pay-btn" onclick="window.showPayment(${order.id}, '${order.price}')">💳 پرداخت</button>
                <button class="download-btn" disabled>🔒 ابتدا پرداخت کنید</button>
              `}
            </div>
          </div>
        `).join('');
    }

    function renderHistory() {
        tabContent.innerHTML = historyOrders.map(h => `
          <div class="history-card" style="margin-bottom:0.8rem;">
            <div class="history-icon">${h.icon}</div>
            <div class="history-details">
              <div class="history-title">${h.title}</div>
              <div class="history-date">📅 ${h.date}</div>
            </div>
            <div class="history-price">${h.price}</div>
          </div>
        `).join('');
    }

    function switchTab(tab) {
        currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        switch (tab) {
            case 'active':
                renderActiveOrders();
                break;
            case 'completed':
                renderCompletedOrders();
                break;
            case 'history':
                renderHistory();
                break;
        }
    }

    // ==================== توابع گلوبال ====================
    window.sendChat = function (orderId) {
        const input = document.getElementById(`chatInput-${orderId}`);
        const chatBox = document.getElementById(`chat-${orderId}`);
        const text = input.value.trim();
        if (!text) return;

        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-msg chat-user';
        msgDiv.textContent = text;
        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        input.value = '';

        // شبیه‌سازی پاسخ اپراتور
        setTimeout(() => {
            const replyDiv = document.createElement('div');
            replyDiv.className = 'chat-msg chat-operator';
            replyDiv.textContent = '✅ پیام شما دریافت شد، به زودی پاسخ می‌دم';
            chatBox.appendChild(replyDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }, 1500);
    };

    window.showPayment = function (orderId, price) {
        showPaymentModal(orderId, price);
    };

    window.downloadFile = function (orderId) {
        const order = ordersData.find(o => o.id === orderId);
        if (order && order.isPaid && order.hasFile) {
            showModal(`📥 دانلود فایل سفارش "${order.title}" شروع شد!\n(حالت دمو: فایل شبیه‌سازی شده)`, '✅');
        }
    };

    // ==================== ایونت‌ها ====================
    document.getElementById('closeModalBtn').addEventListener('click', hideModal);
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) hideModal();
    });

    document.getElementById('cancelPaymentBtn').addEventListener('click', hidePaymentModal);
    paymentModal.addEventListener('click', (e) => {
        if (e.target === paymentModal) hidePaymentModal();
    });

    document.getElementById('confirmPaymentBtn').addEventListener('click', () => {
        if (currentPaymentOrderId) {
            const order = ordersData.find(o => o.id === currentPaymentOrderId);
            if (order) {
                order.isPaid = true;
                showModal(`✅ پرداخت با موفقیت انجام شد!\nمبلغ: ${order.price}`, '💳');
                hidePaymentModal();
                switchTab(currentTab);
            }
        }
    });

    // تب‌ها
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function () {
            switchTab(this.dataset.tab);
        });
    });

    // Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModal();
            hidePaymentModal();
        }
    });

    // لود اولیه
    renderActiveOrders();

})();