// Инициализация Telegram WebApp
const tg = window.Telegram.WebApp;
tg.expand();

// Константы
const LEVELS = {
    'Новичок': { minDeposit: 50, income: 10, requiredReferrals: 3 },
    'Трейдер': { minDeposit: 100, income: 15, requiredReferrals: 6 },
    'Инвестор': { minDeposit: 200, income: 20, requiredReferrals: 9 },
    'Магнат': { minDeposit: 500, income: 25, requiredReferrals: 12 },
    'Император': { minDeposit: 1000, income: 30, requiredReferrals: 15 }
};

// Состояние приложения
let appState = {
    userLevel: 'Новичок',
    balance: 0,
    referrals: 0,
    referralEarnings: 0,
    monthlyIncome: 0,
    nextIncomeTime: null
};

// DOM элементы
const elements = {
    userLevel: document.getElementById('userLevel'),
    userBalance: document.getElementById('userBalance'),
    levelProgress: document.getElementById('levelProgress'),
    nextLevelProgress: document.getElementById('nextLevelProgress'),
    monthlyIncome: document.getElementById('monthlyIncome'),
    nextIncomeTime: document.getElementById('nextIncomeTime'),
    totalReferrals: document.getElementById('totalReferrals'),
    referralEarnings: document.getElementById('referralEarnings')
};

// Функции навигации
function showScreen(screenName) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    document.querySelector(`.${screenName}-screen`).classList.add('active');
}

// Обработчики событий
document.querySelectorAll('.menu-item').forEach(item => {
    item.addEventListener('click', () => {
        const screen = item.dataset.screen;
        showScreen(screen);
    });
});

document.querySelectorAll('.back-button').forEach(button => {
    button.addEventListener('click', () => {
        showScreen('main');
    });
});

// Функции обновления UI
function updateUserInfo() {
    elements.userLevel.textContent = appState.userLevel;
    elements.userBalance.textContent = appState.balance.toFixed(2);
    
    const currentLevel = LEVELS[appState.userLevel];
    const progress = (appState.referrals / currentLevel.requiredReferrals) * 100;
    elements.levelProgress.style.width = `${Math.min(progress, 100)}%`;
    elements.nextLevelProgress.textContent = `${appState.referrals}/${currentLevel.requiredReferrals}`;
    
    elements.monthlyIncome.textContent = appState.monthlyIncome.toFixed(2);
    elements.totalReferrals.textContent = appState.referrals;
    elements.referralEarnings.textContent = appState.referralEarnings.toFixed(2);
}

function updateNextIncomeTime() {
    if (!appState.nextIncomeTime) return;
    
    const now = new Date();
    const timeLeft = appState.nextIncomeTime - now;
    
    if (timeLeft <= 0) {
        elements.nextIncomeTime.textContent = 'Сейчас';
        return;
    }
    
    const hours = Math.floor(timeLeft / (1000 * 60 * 60));
    const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
    
    elements.nextIncomeTime.textContent = 
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Анимации
function animateValue(element, start, end, duration) {
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const animate = () => {
        current += increment;
        element.textContent = current.toFixed(2);
        
        if ((increment > 0 && current < end) || (increment < 0 && current > end)) {
            requestAnimationFrame(animate);
        } else {
            element.textContent = end.toFixed(2);
        }
    };
    
    animate();
}

// Инициализация
async function initApp() {
    try {
        // Здесь будет запрос к API для получения данных пользователя
        const userData = await fetchUserData();
        appState = { ...appState, ...userData };
        updateUserInfo();
        
        // Запуск таймера обновления времени до следующей выплаты
        setInterval(updateNextIncomeTime, 1000);
        
        // Анимация появления элементов
        document.querySelectorAll('.menu-item').forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateY(0)';
            }, index * 100);
        });
    } catch (error) {
        console.error('Ошибка инициализации приложения:', error);
        tg.showAlert('Произошла ошибка при загрузке данных');
    }
}

// Заглушка для получения данных пользователя
async function fetchUserData() {
    // Здесь будет реальный запрос к API
    return {
        userLevel: 'Новичок',
        balance: 50,
        referrals: 1,
        referralEarnings: 5,
        monthlyIncome: 5,
        nextIncomeTime: new Date(Date.now() + 24 * 60 * 60 * 1000)
    };
}

// Запуск приложения
initApp(); 