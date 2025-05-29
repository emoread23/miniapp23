from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import LEVELS, UPGRADES

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура"""
    keyboard = [
        ['👑 Моя Империя', '💎 Инвестировать'],
        ['💰 Вывести прибыль', '👥 Друзья'],
        ['🏪 Магазин', '🏆 Топ игроков']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура администратора"""
    keyboard = [
        ['📊 Статистика', '💼 Транзакции'],
        ['👥 Пользователи', '⚙️ Настройки']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_level_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня"""
    keyboard = []
    for level, data in LEVELS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{level} - {data['minDeposit']} USDT",
                callback_data=f"level_{level}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Отменить", callback_data="confirm_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_shop_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура магазина"""
    keyboard = []
    for upgrade in UPGRADES:
        keyboard.append([
            InlineKeyboardButton(
                f"{upgrade['name']} - {upgrade['base_price']} USDT",
                callback_data=f"shop_{upgrade['id']}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой назад"""
    keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back")]]
    return InlineKeyboardMarkup(keyboard)

def get_referral_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура реферальной программы"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Статистика", callback_data="referral_stats"),
            InlineKeyboardButton("👥 Рефералы", callback_data="referral_list")
        ],
        [
            InlineKeyboardButton("💰 Бонусы", callback_data="referral_bonuses"),
            InlineKeyboardButton("📱 Пригласить", callback_data="referral_invite")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_achievements_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура достижений"""
    keyboard = [
        [
            InlineKeyboardButton("🏆 Мои достижения", callback_data="achievements_my"),
            InlineKeyboardButton("📈 Прогресс", callback_data="achievements_progress")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_top_players_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура топа игроков"""
    keyboard = [
        [
            InlineKeyboardButton("💰 По балансу", callback_data="top_balance"),
            InlineKeyboardButton("👥 По рефералам", callback_data="top_referrals")
        ],
        [
            InlineKeyboardButton("🔄 Обновить", callback_data="top_refresh"),
            InlineKeyboardButton("📊 Моя позиция", callback_data="top_my_position")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_transaction_keyboard(transaction_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для транзакции"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"transaction_confirm_{transaction_id}"),
            InlineKeyboardButton("❌ Отменить", callback_data=f"transaction_cancel_{transaction_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    keyboard = [
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notifications"),
            InlineKeyboardButton("🌐 Язык", callback_data="settings_language")
        ],
        [
            InlineKeyboardButton("💳 Кошелек", callback_data="settings_wallet"),
            InlineKeyboardButton("🔒 Безопасность", callback_data="settings_security")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_miniapp_keyboard(web_app_url, user_id: int):
    """Создает инлайн-клавиатуру с кнопкой для открытия миниаппа."""
    url_with_user_id = f"{web_app_url}?user_id={user_id}"
    
    keyboard = [
        [InlineKeyboardButton("🎮 Моя Империя", web_app=WebAppInfo(url=url_with_user_id))]
        # Вы можете добавить сюда другие кнопки, если нужно
    ]
    return InlineKeyboardMarkup(keyboard) 