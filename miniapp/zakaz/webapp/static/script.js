// Константы для уровней
const LEVELS = {
    'Новичок': { min_invest: 50, income_percent: 10, referrals_needed: 3 },
    'Трейдер': { min_invest: 100, income_percent: 15, referrals_needed: 6 },
    'Инвестор': { min_invest: 200, income_percent: 20, referrals_needed: 9 },
    'Магнат': { min_invest: 500, income_percent: 25, referrals_needed: 12 },
    'Император': { min_invest: 1000, income_percent: 30, referrals_needed: 15 }
};

// Глобальные переменные
let currentUser = null;
let currentLevel = null;
let upgrades = [];
let achievements = [];
let tg = null;
let telegramId = null;

// Инициализация приложения
document.addEventListener('DOMContentLoaded', () => {
    // Получаем telegram_id из URL
    const urlParams = new URLSearchParams(window.location.search);
    telegramId = urlParams.get('telegram_id');
    
    if (!telegramId) {
        showError('Не удалось получить ID пользователя');
        return;
    }
    
    // Загружаем данные пользователя
    loadUserData();
    
    // Настраиваем обработчики событий
    setupEventListeners();
    
    // Инициализация Telegram WebApp
    tg = window.Telegram.WebApp;
    tg.expand();
    
    // Проверка авторизации
    checkAuth();
    
    // Настройка навигации
    setupNavigation();
    
    // Настройка модальных окон
    setupModals();
    
    // Настройка кнопки выхода
    setupLogout();
});

// Загрузка данных пользователя
async function loadUserData() {
    try {
        const response = await fetch(`/api/user/${telegramId}`);
        if (!response.ok) {
            throw new Error('Ошибка загрузки данных пользователя');
        }
        
        currentUser = await response.json();
        updateUI();
    } catch (error) {
        showError(error.message);
    }
}

// Обновление интерфейса
function updateUI() {
    if (!currentUser) return;
    
    // Обновляем информацию о пользователе
    document.getElementById('username').textContent = currentUser.username;
    document.getElementById('user-level').textContent = `Уровень: ${currentUser.level}`;
    
    // Обновляем статистику
    document.getElementById('balance').textContent = `${currentUser.balance} USDT`;
    document.getElementById('invested').textContent = `${currentUser.invested_amount} USDT`;
    document.getElementById('referral-count').textContent = currentUser.referral_count;
    document.getElementById('income-percent').textContent = `${LEVELS[currentUser.level].income_percent}%`;
    
    // Обновляем прогресс уровня
    const progressBar = document.querySelector('.progress-bar');
    progressBar.style.width = `${currentUser.progress}%`;
    
    // Обновляем информацию о следующем уровне
    const nextLevelInfo = document.getElementById('next-level-info');
    if (currentUser.next_level) {
        nextLevelInfo.textContent = `Следующий уровень: ${currentUser.next_level} (нужно еще ${LEVELS[currentUser.next_level].referrals_needed - currentUser.referral_count} рефералов)`;
    } else {
        nextLevelInfo.textContent = 'Вы достигли максимального уровня!';
    }
    
    // Обновляем реферальную ссылку
    const referralLink = document.getElementById('referral-link');
    referralLink.value = `https://t.me/your_bot?start=${currentUser.referral_code}`;
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Навигация по меню
    document.querySelectorAll('.menu li').forEach(item => {
        item.addEventListener('click', () => {
            // Убираем активный класс у всех пунктов меню
            document.querySelectorAll('.menu li').forEach(i => i.classList.remove('active'));
            // Добавляем активный класс выбранному пункту
            item.classList.add('active');
            
            // Скрываем все страницы
            document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
            // Показываем выбранную страницу
            const pageId = `${item.dataset.page}-page`;
            document.getElementById(pageId).classList.add('active');
        });
    });
    
    // Копирование реферальной ссылки
    document.getElementById('copy-link').addEventListener('click', () => {
        const referralLink = document.getElementById('referral-link');
        referralLink.select();
        document.execCommand('copy');
        showSuccess('Реферальная ссылка скопирована!');
    });
    
    // Инвестирование
    document.getElementById('invest-button').addEventListener('click', handleInvest);
    
    // Вывод средств
    document.getElementById('withdraw-button').addEventListener('click', handleWithdraw);
}

// Обработка инвестирования
async function handleInvest() {
    const amount = parseFloat(document.getElementById('invest-amount').value);
    
    if (!amount || amount < LEVELS['Новичок'].min_invest) {
        showError(`Минимальная сумма инвестиции: ${LEVELS['Новичок'].min_invest} USDT`);
        return;
    }
    
    try {
        const response = await fetch('/api/invest', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                amount: amount
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка при создании инвестиции');
        }
        
        showSuccess('Инвестиция успешно создана!');
        loadUserData(); // Обновляем данные пользователя
    } catch (error) {
        showError(error.message);
    }
}

// Обработка вывода средств
async function handleWithdraw() {
    const amount = parseFloat(document.getElementById('withdraw-amount').value);
    
    if (!amount || amount < 1) {
        showError('Минимальная сумма вывода: 1 USDT');
        return;
    }
    
    try {
        const response = await fetch('/api/withdraw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                telegram_id: telegramId,
                amount: amount
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка при создании заявки на вывод');
        }
        
        showSuccess('Заявка на вывод успешно создана!');
        loadUserData(); // Обновляем данные пользователя
    } catch (error) {
        showError(error.message);
    }
}

// Показ сообщения об успехе
function showSuccess(message) {
    const modal = new bootstrap.Modal(document.getElementById('successModal'));
    document.getElementById('success-message').textContent = message;
    modal.show();
}

// Показ сообщения об ошибке
function showError(message) {
    const modal = new bootstrap.Modal(document.getElementById('errorModal'));
    document.getElementById('error-message').textContent = message;
    modal.show();
}

// Загрузка списка рефералов
async function loadReferrals() {
    try {
        const response = await fetch(`/api/referrals/${telegramId}`);
        if (!response.ok) {
            throw new Error('Ошибка загрузки списка рефералов');
        }
        
        const referrals = await response.json();
        const container = document.getElementById('referrals-container');
        container.innerHTML = '';
        
        if (referrals.length === 0) {
            container.innerHTML = '<p>У вас пока нет рефералов</p>';
            return;
        }
        
        referrals.forEach(ref => {
            const div = document.createElement('div');
            div.className = 'referral-item';
            div.innerHTML = `
                <div class="referral-info">
                    <h4>${ref.username}</h4>
                    <p>Уровень: ${ref.level}</p>
                    <p>Инвестировано: ${ref.invested_amount} USDT</p>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        showError(error.message);
    }
}

// Загрузка топа игроков
async function loadTopPlayers() {
    try {
        const response = await fetch('/api/top');
        if (!response.ok) {
            throw new Error('Ошибка загрузки топа игроков');
        }
        
        const players = await response.json();
        const container = document.getElementById('top-players');
        container.innerHTML = '';
        
        players.forEach((player, index) => {
            const div = document.createElement('div');
            div.className = 'player-item';
            div.innerHTML = `
                <div class="player-rank">#${index + 1}</div>
                <div class="player-info">
                    <h4>${player.username}</h4>
                    <p>Уровень: ${player.level}</p>
                </div>
                <div class="player-stats">
                    <p>${player.invested_amount} USDT</p>
                    <p>${player.referral_count} рефералов</p>
                </div>
            `;
            container.appendChild(div);
        });
    } catch (error) {
        showError(error.message);
    }
}

// Проверка авторизации
async function checkAuth() {
    try {
        const response = await fetch('/api/user/me');
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                currentUser = data.data;
                updateUserInterface();
                loadLevels();
                loadUpgrades();
                loadAchievements();
                document.getElementById('auth-modal').style.display = 'none';
            } else {
                showAuthModal();
            }
        } else {
            showAuthModal();
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showAuthModal();
    }
}

// Показ модального окна авторизации
function showAuthModal() {
    document.getElementById('auth-modal').style.display = 'block';
}

// Авторизация через Telegram
function initTelegramAuth() {
    const telegramLoginBtn = document.getElementById('telegram-login-btn');
    telegramLoginBtn.addEventListener('click', async () => {
        try {
            const userData = tg.initDataUnsafe.user;
            if (!userData) {
                showError('Ошибка получения данных пользователя');
                return;
            }

            const response = await fetch('/api/auth/telegram', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            const data = await response.json();
            if (data.success) {
                currentUser = data.data;
                updateUserInterface();
                loadLevels();
                loadUpgrades();
                loadAchievements();
                document.getElementById('auth-modal').style.display = 'none';
                showSuccess('Успешная авторизация');
            } else {
                showError(data.error);
            }
        } catch (error) {
            console.error('Ошибка:', error);
            showError('Ошибка при авторизации');
        }
    });
}

// Выход из системы
async function logout() {
    try {
        const response = await fetch('/api/logout');
        if (response.ok) {
            currentUser = null;
            showAuthModal();
            showSuccess('Успешный выход из системы');
        } else {
            showError('Ошибка при выходе из системы');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка при выходе из системы');
    }
}

// Настройка кнопки выхода
function setupLogout() {
    const logoutBtn = document.getElementById('logout-btn');
    logoutBtn.addEventListener('click', logout);
}

// Обновление интерфейса
function updateUserInterface() {
    if (!currentUser) return;

    // Обновление информации о пользователе
    document.getElementById('username').textContent = currentUser.username;
    document.getElementById('user-level').textContent = `Уровень: ${currentUser.level}`;
    document.getElementById('user-balance').textContent = `${currentUser.balance} USDT`;
    document.getElementById('total-deposit').textContent = `${currentUser.total_deposit} USDT`;
    document.getElementById('total-withdraw').textContent = `${currentUser.total_withdraw} USDT`;
    document.getElementById('referral-count').textContent = currentUser.referral_count;
    document.getElementById('referral-earnings').textContent = `${currentUser.referral_earnings} USDT`;
    document.getElementById('referral-code').textContent = currentUser.referral_code;
    document.getElementById('referral-link').value = `${window.location.origin}/ref/${currentUser.referral_code}`;
}

// Загрузка уровней
async function loadLevels() {
    try {
        const response = await fetch('/api/levels');
        const data = await response.json();
        
        if (data.success) {
            currentLevel = data.data[currentUser.level];
            updateLevelProgress();
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// Обновление прогресса уровня
function updateLevelProgress() {
    if (!currentLevel) return;

    const progress = (currentUser.total_deposit / currentLevel.minDeposit) * 100;
    document.getElementById('level-progress').style.width = `${Math.min(progress, 100)}%`;
    document.getElementById('level-progress-text').textContent = 
        `${currentUser.total_deposit}/${currentLevel.minDeposit} USDT`;
}

// Загрузка апгрейдов
async function loadUpgrades() {
    try {
        const response = await fetch('/api/upgrades');
        const data = await response.json();
        
        if (data.success) {
            upgrades = data.data;
            renderUpgrades();
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// Отрисовка апгрейдов
function renderUpgrades() {
    const container = document.getElementById('upgrades-list');
    container.innerHTML = '';

    upgrades.forEach(upgrade => {
        const card = document.createElement('div');
        card.className = 'card';
        card.innerHTML = `
            <h3>${upgrade.name}</h3>
            <p>${upgrade.description}</p>
            <div class="upgrade-stats">
                <div class="stat">
                    <span class="label">Бонус:</span>
                    <span>${upgrade.bonus}%</span>
                </div>
                <div class="stat">
                    <span class="label">Цена:</span>
                    <span>${upgrade.price} USDT</span>
                </div>
            </div>
            <button class="primary-btn" onclick="purchaseUpgrade('${upgrade.id}')" 
                    ${currentUser.balance < upgrade.price ? 'disabled' : ''}>
                <i class="fas fa-shopping-cart"></i>
                Купить
            </button>
        `;
        container.appendChild(card);
    });
}

// Покупка апгрейда
async function purchaseUpgrade(upgradeId) {
    try {
        const response = await fetch('/api/upgrade', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                upgrade_id: upgradeId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('Апгрейд успешно куплен');
            loadUserData(); // Перезагрузка данных пользователя
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showError('Ошибка при покупке апгрейда');
    }
}

// Загрузка достижений
async function loadAchievements() {
    try {
        const response = await fetch('/api/achievements');
        const data = await response.json();
        
        if (data.success) {
            achievements = data.data;
            renderAchievements();
        }
    } catch (error) {
        console.error('Ошибка:', error);
    }
}

// Отрисовка достижений
function renderAchievements() {
    const container = document.getElementById('achievements-list');
    container.innerHTML = '';

    achievements.forEach(achievement => {
        const card = document.createElement('div');
        card.className = 'achievement-item';
        card.innerHTML = `
            <i class="fas ${achievement.icon}"></i>
            <h4>${achievement.name}</h4>
            <p>${achievement.description}</p>
            <div class="achievement-progress">
                <div class="progress-bar">
                    <div class="progress" style="width: ${achievement.progress}%"></div>
                </div>
                <span>${achievement.progress}%</span>
            </div>
        `;
        container.appendChild(card);
    });
}

// Настройка навигации
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-links li');
    const sections = document.querySelectorAll('.section');

    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const targetSection = link.getAttribute('data-section');
            
            // Обновление активного пункта меню
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Показ нужной секции
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === targetSection) {
                    section.classList.add('active');
                }
            });
        });
    });
}

// Настройка модальных окон
function setupModals() {
    const modals = document.querySelectorAll('.modal');
    const closeBtns = document.querySelectorAll('.close');

    closeBtns.forEach(btn => {
        btn.onclick = () => {
            btn.closest('.modal').style.display = 'none';
        };
    });

    window.onclick = (event) => {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    };
} 