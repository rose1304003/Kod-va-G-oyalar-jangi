"""
Multi-language translations for ITCom Hackathons Bot
Supports: Uzbek (uz), Russian (ru), English (en)
"""

LANGUAGES = ['uz', 'ru', 'en']

TRANSLATIONS = {
    # Menu items
    'hackathons': {
        'uz': 'Xakatonlar',
        'ru': 'Хакатоны',
        'en': 'Hackathons'
    },
    'my_hackathons': {
        'uz': 'Mening xakatonlarim',
        'ru': 'Мои хакатоны',
        'en': 'My hackathons'
    },
    'settings': {
        'uz': 'Sozlamalar',
        'ru': 'Настройки',
        'en': 'Settings'
    },
    'help': {
        'uz': 'Yordam',
        'ru': 'Помощь',
        'en': 'Help'
    },
    
    # Welcome messages
    'welcome_back': {
        'uz': 'Xush kelibsiz!',
        'ru': 'С возвращением!',
        'en': 'Welcome back!'
    },
    'welcome_message': {
        'uz': '''Bot nima qila oladi?

👋 Kod va G'oyalar Hackathons Botiga xush kelibsiz!

Ushbu bot sizga xakatonlarimizda samarali ishtirok etishga yordam beradi 💡

Bu yerda siz:
• Kelgusi xakatonlarga ro'yxatdan o'tishingiz 📝
• Vazifalarni qabul qilish va topshirishingiz ⚙️
• O'z yutuqlaringiz va natijalaringizni kuzatishingiz 📊
• E'lonlardan xabardor bo'lishingiz mumkin 📬



Omad tilaymiz va xakatonlarimizda ajoyib narsalar yarating 💚''',
        'ru': '''Что умеет этот бот?

👋 Добро пожаловать в Kod va G'oyalar Hackathons Bot!

Этот бот поможет вам эффективно участвовать в наших хакатонах 💡

Здесь вы можете:
• Регистрироваться на предстоящие хакатоны 📝
• Получать и отправлять задания ⚙️
• Отслеживать свой прогресс и результаты 📊
• Быть в курсе объявлений 📬



Удачи и создавайте что-то удивительное на наших хакатонах 💚''',
        'en': '''What can this bot do?

👋 Welcome to the Kod va G'oyalar Hackathons Bot!

This bot helps you participate in our hackathons effectively 💡

Here you can:
• Register for upcoming hackathons 📝
• Receive and submit tasks ⚙️
• Track your progress and results 📊
• Stay updated with announcements 📬


Good luck and build something amazing with our hackathons 💚'''
    },
    
    # Registration
    'enter_first_name': {
        'uz': 'Ismingizni kiriting (masalan: Robiya)',
        'ru': 'Введите ваше имя (например: Робия)',
        'en': 'Enter your first name (e.g. Robiya)'
    },
    'enter_last_name': {
        'uz': 'Familiyangizni kiriting (masalan: Obidjonova)',
        'ru': 'Введите вашу фамилию (например: Обиджонова)',
        'en': 'Enter your last name (e.g. Obidjonova)'
    },
    'enter_birth_date': {
        'uz': 'Tug\'ilgan sanangizni kiriting (masalan: 23.10.2007)',
        'ru': 'Введите дату рождения (например: 23.10.2007)',
        'en': 'Enter your birth date (e.g. 23.10.2007)'
    },
    'send_phone': {
        'uz': 'Telefon raqamingizni yuboring (📱 tugma orqali)',
        'ru': 'Отправьте ваш номер телефона (📱 через кнопку)',
        'en': 'Send your phone number (📱 via button)'
    },
    'share_phone_button': {
        'uz': '📱 Telefon raqamni yuborish',
        'ru': '📱 Отправить номер телефона',
        'en': '📱 Send phone number'
    },
    'enter_pinfl': {
        'uz': '''Shaxsiy identifikatsiya raqamingizni (JSHSHIR) kiriting - 14 raqam.

Nima uchun JSHSHIR kerak:
- yoshingizni tasdiqlash uchun
- final tadbirda ishtirokingizni tashkil qilish uchun (turar joy va chipta)''',
        'ru': '''Введите ваш персональный идентификационный номер (ПИНФЛ) - 14 цифр.

Зачем нужен ПИНФЛ:
- для подтверждения вашего возраста
- для организации вашего участия в финале (проживание и билеты)''',
        'en': '''Please enter your Personal Identification Number (PINFL) - 14 digits.

Why we require your PINFL:
- to verify your age
- to organize your participation in the final event if needed (booking accommodation and purchasing tickets)'''
    },
    'invalid_date': {
        'uz': '❌ Noto\'g\'ri sana formati. KK.OO.YYYY formatida kiriting (masalan: 23.10.2007)',
        'ru': '❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ (например: 23.10.2007)',
        'en': '❌ Invalid date format. Please use DD.MM.YYYY format (e.g. 23.10.2007)'
    },
    'invalid_pinfl': {
        'uz': '❌ JSHSHIR aynan 14 ta raqamdan iborat bo\'lishi kerak. Qaytadan kiriting.',
        'ru': '❌ ПИНФЛ должен содержать ровно 14 цифр. Попробуйте снова.',
        'en': '❌ PINFL must be exactly 14 digits. Please try again.'
    },
    'registration_almost_done': {
        'uz': '''Deyarli tayyor 🔄

Ishtirokingizni tasdiqlash uchun hackathonni tanlang:
Menu → 🚀 Xakatonlar → AI500! → Ro'yxatdan o'tish ✅

⚠️ Hackathon tanlamasdan ro'yxatdan o'tish haqiqiy emas''',
        'ru': '''Почти готово 🔄

Для подтверждения участия выберите хакатон:
Меню → 🚀 Хакатоны → AI500! → Регистрация ✅

⚠️ Регистрация без выбора хакатона недействительна''',
        'en': '''You're almost done 🔄

To confirm your participation, please choose your hackathon:
Menu → 🚀 Hackathons → AI500! → Register ✅

⚠️ Registration without selecting a hackathon is not valid'''
    },
    
    # Hackathon related
    'no_hackathons': {
        'uz': 'Xakatonlar mavjud emas',
        'ru': 'Нет доступных хакатонов',
        'en': 'No hackathons available'
    },
    'available_hackathons': {
        'uz': 'Mavjud xakatonlar',
        'ru': 'Доступные хакатоны',
        'en': 'Available hackathons'
    },
    'your_hackathons': {
        'uz': 'Sizning xakatonlaringiz',
        'ru': 'Ваши хакатоны',
        'en': 'Your hackathons'
    },
    'register': {
        'uz': 'Ro\'yxatdan o\'tish',
        'ru': 'Зарегистрироваться',
        'en': 'Register'
    },
    'registered': {
        'uz': 'Ro\'yxatdan o\'tdingiz',
        'ru': 'Вы зарегистрированы',
        'en': 'You are registered'
    },
    'see_details': {
        'uz': 'Batafsil ko\'rish',
        'ru': 'Подробнее',
        'en': 'See details'
    },
    'prize_pool': {
        'uz': 'Sovrin jamg\'armasi',
        'ru': 'Призовой фонд',
        'en': 'Prize pool'
    },
    'registered_teams': {
        'uz': 'Ro\'yxatdan o\'tgan jamoalar',
        'ru': 'Зарегистрированных команд',
        'en': 'Registered teams'
    },
    
    # Team related
    'create_team': {
        'uz': 'Jamoa yaratish',
        'ru': 'Создать команду',
        'en': 'Create team'
    },
    'join_team': {
        'uz': 'Jamoaga qo\'shilish',
        'ru': 'Присоединиться к команде',
        'en': 'Join team'
    },
    'create_new_team': {
        'uz': '🆕 Yangi jamoa yaratish',
        'ru': '🆕 Создать новую команду',
        'en': '🆕 Create new team'
    },
    'join_existing_team': {
        'uz': '🔗 Mavjud jamoaga qo\'shilish',
        'ru': '🔗 Присоединиться к команде',
        'en': '🔗 Join existing team'
    },
    'enter_team_name': {
        'uz': '📝 Jamoa nomini kiriting:',
        'ru': '📝 Введите название команды:',
        'en': '📝 Enter your team name:'
    },
    'enter_team_code': {
        'uz': '🔑 Jamoa kodini kiriting:',
        'ru': '🔑 Введите код команды:',
        'en': '🔑 Enter the team code:'
    },
    'team_created': {
        'uz': '''✅ Jamoa yaratildi!

📁 Nomi: {name}
🔑 Kod: {code}

Bu kodni jamoadoshlaringiz bilan ulashing, ular ham qo'shilishi uchun.

ℹ️ Yaqinda hackathonning keyingi bosqichlari haqida xabar olasiz.
Iltimos, botni bloklamang!''',
        'ru': '''✅ Команда создана!

📁 Название: {name}
🔑 Код: {code}

Поделитесь этим кодом с вашими товарищами по команде, чтобы они могли присоединиться.

ℹ️ Скоро вы получите обновления о следующих этапах хакатона.
Пожалуйста, не блокируйте бота!''',
        'en': '''✅ Team created!

📁 Name: {name}
🔑 Code: {code}

Share this code with your teammates so they can join the team.

ℹ️ Soon you will receive updates about the next stages of this hackathon.
Please do not block the bot!'''
    },
    'team_joined': {
        'uz': '✅ Siz \'{name}\' jamoasiga qo\'shildingiz!',
        'ru': '✅ Вы присоединились к команде \'{name}\'!',
        'en': '✅ You have joined team \'{name}\'!'
    },
    'invalid_team_code': {
        'uz': '❌ Noto\'g\'ri jamoa kodi. Tekshirib, qayta urinib ko\'ring.',
        'ru': '❌ Неверный код команды. Проверьте и попробуйте снова.',
        'en': '❌ Invalid team code. Please check and try again.'
    },
    'team_name': {
        'uz': 'Jamoa nomi',
        'ru': 'Название команды',
        'en': 'Team name'
    },
    'team_code': {
        'uz': 'Jamoa kodi',
        'ru': 'Код команды',
        'en': 'Team code'
    },
    'team_members': {
        'uz': 'Jamoa a\'zolari',
        'ru': 'Участники команды',
        'en': 'Team members'
    },
    'leave_team': {
        'uz': 'Jamoani tark etish',
        'ru': 'Покинуть команду',
        'en': 'Leave team'
    },
    'remove_member': {
        'uz': 'A\'zoni o\'chirish',
        'ru': 'Удалить участника',
        'en': 'Remove member'
    },
    'how_to_participate': {
        'uz': 'Qanday ishtirok etmoqchisiz?',
        'ru': 'Как вы хотите участвовать?',
        'en': 'How would you like to participate?'
    },
    
    # Stages
    'stage': {
        'uz': 'Bosqich',
        'ru': 'Этап',
        'en': 'Stage'
    },
    'stages': {
        'uz': 'Bosqichlar',
        'ru': 'Этапы',
        'en': 'Stages'
    },
    'deadline': {
        'uz': 'Muddat',
        'ru': 'Дедлайн',
        'en': 'Deadline'
    },
    'submit': {
        'uz': 'Topshirish',
        'ru': 'Отправить',
        'en': 'Submit'
    },
    'submission_received': {
        'uz': '✅ Topshiriq qabul qilindi!\n\nOmad! 🍀',
        'ru': '✅ Работа принята!\n\nУдачи! 🍀',
        'en': '✅ Submission received!\n\nGood luck! 🍀'
    },
    'deadline_passed': {
        'uz': '⏰ Bosqich muddati tugagan :(',
        'ru': '⏰ Срок этапа уже истёк :(',
        'en': '⏰ Stage deadline has already passed :('
    },
    'submit_your_work': {
        'uz': '''📤 Ishingizni topshiring

Demo veb-sayt havolasini yuboring yoki fayl yuklang (PDF, rasm, video va boshqalar):''',
        'ru': '''📤 Отправьте вашу работу

Отправьте ссылку на демо-сайт или загрузите файл (PDF, изображение, видео и т.д.):''',
        'en': '''📤 Submit your work

Send the link to your live demo website or upload a file (PDF, image, video, etc.):'''
    },
    
    # Settings / Profile
    'choose_language': {
        'uz': 'Tilni tanlang',
        'ru': 'Выберите язык',
        'en': 'Choose your language'
    },
    'your_data': {
        'uz': 'Sizning ma\'lumotlaringiz',
        'ru': 'Ваши данные',
        'en': 'Your data'
    },
    'first_name': {
        'uz': 'Ism',
        'ru': 'Имя',
        'en': 'First name'
    },
    'last_name': {
        'uz': 'Familiya',
        'ru': 'Фамилия',
        'en': 'Last name'
    },
    'birth_date': {
        'uz': 'Tug\'ilgan sana',
        'ru': 'Дата рождения',
        'en': 'Birth date'
    },
    'gender': {
        'uz': 'Jins',
        'ru': 'Пол',
        'en': 'Gender'
    },
    'male': {
        'uz': 'Erkak',
        'ru': 'Мужской',
        'en': 'Male'
    },
    'female': {
        'uz': 'Ayol',
        'ru': 'Женский',
        'en': 'Female'
    },
    'location': {
        'uz': 'Joylashuv',
        'ru': 'Местоположение',
        'en': 'Location'
    },
    'change_first_name': {
        'uz': 'Ismni o\'zgartirish',
        'ru': 'Изменить имя',
        'en': 'Change first name'
    },
    'change_last_name': {
        'uz': 'Familiyani o\'zgartirish',
        'ru': 'Изменить фамилию',
        'en': 'Change last name'
    },
    'not_set': {
        'uz': 'Belgilanmagan',
        'ru': 'Не указано',
        'en': 'Not set'
    },
    
    # Help
    'need_help': {
        'uz': 'Yordam kerakmi yoki xato topdingizmi?',
        'ru': 'Нужна помощь или нашли ошибку?',
        'en': 'Need help or found a bug?'
    },
    'help_text': {
        'uz': '''Agar sizda savollar bo'lsa, botdan foydalanishda yordam kerak bo'lsa yoki takomillashtirish bo'yicha takliflaringiz bo'lsa, biz bilan bog'laning:''',
        'ru': '''Если у вас есть вопросы, нужна помощь с ботом или есть предложения по улучшению, свяжитесь с нами:''',
        'en': '''If you have questions, need assistance using the bot or have suggestions for improvement, please contact us at:'''
    },
    'describe_problem': {
        'uz': 'Muammoni batafsil tasvirlab, iloji bo\'lsa skrinshot ham qo\'shing.\nTez orada javob beramiz',
        'ru': 'Опишите проблему подробно и приложите скриншоты, если возможно.\nМы скоро ответим',
        'en': 'Describe the problem in detail and attach screenshots if possible.\nWe will get back to you soon'
    },
    
    # Navigation
    'back': {
        'uz': 'Orqaga',
        'ru': 'Назад',
        'en': 'Back'
    },
    'main_menu': {
        'uz': 'Asosiy menyu',
        'ru': 'Главное меню',
        'en': 'Main menu'
    },
    'cancel': {
        'uz': 'Bekor qilish',
        'ru': 'Отмена',
        'en': 'Cancel'
    },
    'operation_cancelled': {
        'uz': 'Operatsiya bekor qilindi.',
        'ru': 'Операция отменена.',
        'en': 'Operation cancelled.'
    },
    
    # Notifications
    'days_left_3': {
        'uz': '⏳ Birinchi vazifagacha 3 kun qoldi!\n\nBirinchi vazifa yaqinlashmoqda, shuning uchun loyiha g\'oyasini belgilash uchun hozir eng yaxshi vaqt.',
        'ru': '⏳ До первого задания осталось 3 дня!\n\nПервое задание уже скоро, так что сейчас самое время определиться с идеей проекта.',
        'en': '⏳ 3 days left until the first task!\n\nYour first task is coming up soon, so now is a good time to settle on your project idea.'
    },
    'days_left_2': {
        'uz': '🕐 2 kun ichida birinchi vazifangizni olasiz!',
        'ru': '🕐 Через 2 дня вы получите первое задание!',
        'en': '🕐 In just two days you will receive your first task!'
    },
    'deadline_approaching': {
        'uz': '⏳ Bosqich muddati yaqinlashmoqda!\n\nBugun 23:59 gacha — javoblaringizni topshirishning oxirgi imkoniyati.',
        'ru': '⏳ Дедлайн этапа приближается!\n\nСегодня до 23:59 — последний шанс отправить ваши ответы.',
        'en': '⏳ Stage deadline approaching!\n\nToday until 23:59 — the final chance to submit your answers.'
    },
    'congratulations_stage': {
        'uz': '🎉 {stage} bosqichiga o\'tganingiz bilan tabriklaymiz!',
        'ru': '🎉 Поздравляем с прохождением в {stage} этап!',
        'en': '🎉 Congratulations on making it to {stage}!'
    },
    
    # Admin
    'admin_panel': {
        'uz': '🔐 Admin paneli',
        'ru': '🔐 Панель администратора',
        'en': '🔐 Admin Panel'
    },
    'create_hackathon': {
        'uz': 'Hackathon yaratish',
        'ru': 'Создать хакатон',
        'en': 'Create Hackathon'
    },
    'manage_hackathons': {
        'uz': 'Hackathonlarni boshqarish',
        'ru': 'Управление хакатонами',
        'en': 'Manage Hackathons'
    },
    'broadcast_message': {
        'uz': 'Xabar yuborish',
        'ru': 'Рассылка сообщений',
        'en': 'Broadcast Message'
    },
    'statistics': {
        'uz': 'Statistika',
        'ru': 'Статистика',
        'en': 'Statistics'
    },
    'manage_stages': {
        'uz': 'Bosqichlarni boshqarish',
        'ru': 'Управление этапами',
        'en': 'Manage Stages'
    },
    'export_submissions': {
        'uz': 'Topshiriqlarni eksport qilish',
        'ru': 'Экспорт работ',
        'en': 'Export Submissions'
    },
    'access_denied': {
        'uz': '⛔ Kirish taqiqlangan',
        'ru': '⛔ Доступ запрещён',
        'en': '⛔ Access denied'
    },
    
    # File upload
    'file_received': {
        'uz': '📁 Fayl qabul qilindi: {filename}',
        'ru': '📁 Файл получен: {filename}',
        'en': '📁 File received: {filename}'
    },
    'link_received': {
        'uz': '🔗 Havola qabul qilindi',
        'ru': '🔗 Ссылка получена',
        'en': '🔗 Link received'
    },
}


def get_text(key: str, lang: str = 'en', **kwargs) -> str:
    """Get translated text by key and language"""
    if key not in TRANSLATIONS:
        return key
    
    text = TRANSLATIONS[key].get(lang, TRANSLATIONS[key].get('en', key))
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    
    return text
