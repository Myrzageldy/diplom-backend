"""
Management command to seed the database with 35 demo courses.
Usage: python manage.py seed_courses
Usage (with teacher email): python manage.py seed_courses --teacher teacher@example.com
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from courses.models import Category, Course, Module, Lesson, Test, Question, Answer

User = get_user_model()

# Keyword -> YouTube video ID mapping (real educational videos)
# Keywords matched against lesson title (case-insensitive)
VIDEO_MAP = [
    # ── HTML / CSS ──
    (["html", "тег", "семантик", "форм"],             "qz0aGYrrlhU"),  # freeCodeCamp HTML
    (["css", "селектор", "специфичн", "цвет"],         "1Rs2ND1ryYc"),  # Traversy CSS
    (["flexbox", "flex"],                              "JJSoEo8JSnc"),  # Traversy Flexbox
    (["grid"],                                         "jV8B24rSN5o"),  # Traversy CSS Grid
    (["media", "адаптив", "responsive", "mobile"],     "yfoY53QXEnI"),  # Responsive Design
    (["box model", "margin", "padding", "border"],     "rIO5326XgOM"),  # Box Model
    # ── JavaScript ──
    (["javascript", "js", "переменн", "тип данных", "оператор", "условие", "цикл"],
                                                       "PkZNo7MFNFg"),  # freeCodeCamp JS full
    (["стрелочн", "arrow", "функц", "lambda", "def",
      "замыкание", "closure"],                         "h33Srr5J9nY"),  # Arrow functions
    (["dom", "документ", "элемент", "браузер"],        "5fb2aPlgoys"),  # DOM traversal
    (["событи", "event", "обработчик", "handler"],     "XF1_MlZ5l6M"),  # Events
    (["async", "await", "асинхронн"],                  "V_Kr9OSfDeU"),  # Async/Await
    (["promise", "промис"],                            "DHvZLI7Db8E"),  # Promises
    (["fetch", "rest", "запрос", "api", "http"],       "cuEtnrL9-H0"),  # Fetch API
    # ── React ──
    (["react", "jsx", "компонент", "virtual dom"],     "w7ejDZ8SWv8"),  # React Crash Course
    (["usestate", "useeffect", "хук", "hook"],         "O6P86uwfdR0"),  # React Hooks
    (["usecontext", "context", "provider"],            "5LrDIWkK_Bc"),  # Context API
    (["redux", "store", "action", "reducer"],          "poQXNp9ItL4"),  # Redux Toolkit
    (["usecallback", "usememo", "usereducer"],         "MFj_S0Nof-Y"),  # Advanced hooks
    # ── TypeScript ──
    (["typescript", "тип", "interface", "generic",
      "enum", "декоратор", "модификатор"],             "BwuLxPii8Ms"),  # TypeScript Tutorial
    # ── Node / Express ──
    (["node", "npm", "модул", "require", "import",
      "установк", "package"],                         "fBNz5xF-Kx4"),  # Node.js Crash
    (["express", "middleware", "маршрут", "route",
      "crud", "api route", "rest api"],               "L72fhGm1tfE"),  # Express.js
    (["jwt", "token", "авторизац", "аутентификац",
      "аутентиф", "oauth", "session"],                "7Q17ubqLfaM"),  # JWT Auth
    # ── Python ──
    (["python", "переменн", "тип данных", "синтаксис",
      "установк python", "первая программ"],           "rfscVS0vtbw"),  # freeCodeCamp Python
    (["список", "массив", "словарь", "кортеж",
      "множество", "set", "list comprehension"],       "W8KRpuf-ge8"),  # Python data structures
    (["класс", "объект", "ооп", "oop", "наследован",
      "self", "__init__"],                             "JeznW_7DlB0"),  # Python OOP
    (["django", "orm", "model", "migration", "view",
      "template", "url", "wsgi", "mtv"],              "F5mRW0jo-U4"),  # Django Crash
    (["fastapi", "pydantic", "uvicorn", "starlette"],  "0sOvCWFmrtA"),  # FastAPI Tutorial
    (["requests", "beautifulsoup", "парсинг",
      "scraping", "html парс"],                       "XVv6mJpFOb0"),  # BeautifulSoup
    (["selenium", "браузер автомат"],                  "Xjv1sY630Uc"),  # Selenium
    (["scrapy"],                                       "mBoX_JCKZTE"),  # Scrapy
    (["openpyxl", "excel", "pdf", "pillow", "pil",
      "schedule", "файл", "автоматизац"],              "s3lIa3E8KPQ"),  # Python automation
    # ── Data Science / ML ──
    (["numpy", "массив числ"],                         "QUT1VHiLmmI"),  # NumPy Tutorial
    (["pandas", "dataframe", "csv", "данных",
      "очистк", "группировк"],                        "vmEHCJofvqE"),  # Pandas Tutorial
    (["matplotlib", "график", "визуализац"],           "3Xc3CA655Y4"),  # Matplotlib
    (["seaborn"],                                      "6GUZXRvalAU"),  # Seaborn
    (["plotly", "dash", "интерактивн"],                "GGL6PJCE3WA"),  # Plotly
    (["sklearn", "scikit", "регресси", "классифик",
      "дерев", "random forest", "метрик", "knn",
      "svm", "gradient", "бустинг", "cross"],         "0B5eIE_1vpU"),  # sklearn Tutorial
    (["нейронн", "neural", "deep learning", "keras",
      "tensorflow", "cnn", "rnn", "lstm",
      "перцептрон"],                                   "aircAruvnKk"),  # Neural Networks
    (["машинн обучени", "machine learning", "ml",
      "признак", "feature", "overfitting",
      "обучени", "train"],                             "i_LwzRVP7bg"),  # ML Tutorial
    # ── SQL / Databases ──
    (["sql", "select", "insert", "update", "delete",
      "ddl", "dml", "where", "group by", "order"],    "HXV3zeQKqGY"),  # SQL Tutorial
    (["join", "inner", "left", "right", "full",
      "подзапрос", "cte", "оконн"],                   "9yeOJ0ZMUYw"),  # SQL Joins
    (["нормал", "нормальн форм", "erd", "индекс",
      "проектиров", "postgresql", "mysql"],            "7S_tz1z_5bA"),  # DB Design
    (["mongodb", "nosql", "bson", "коллекц",
      "документ", "mongoose", "aggregate"],           "ofme2o29ngU"),  # MongoDB
    (["redis", "кеш", "ttl", "очередь задач",
      "celery"],                                       "jgpVkeyfRe8"),  # Redis Tutorial
    # ── Git / GitHub ──
    (["git", "коммит", "commit", "ветк", "branch",
      "merge", "история", "репозитори",
      ".gitignore"],                                   "RGOj5yH7evk"),  # Git freeCodeCamp
    (["github", "pull request", "fork", "code review",
      "actions", "ci/cd", "защит"],                   "nhNq2kIvi9s"),  # GitHub Tutorial
    # ── Docker ──
    (["docker", "контейнер", "image", "образ",
      "dockerfile", "registry", "hub"],               "fqMOX6JJhGo"),  # Docker freeCodeCamp
    (["docker compose", "compose", "volume", "сет",
      "продакш"],                                      "HG6yIjZapSA"),  # Docker Compose
    # ── Linux / Bash ──
    (["linux", "команд", "навигац", "файлов",
      "chmod", "права", "окружени"],                  "ROjZy1WbCIA"),  # Linux Tutorial
    (["bash", "скрипт", "цикл", "условие bash",
      "переменн bash", "shebang"],                    "oxuRxtrO2Ag"),  # Bash Scripting
    (["cron", "планировщик", "schedule"],              "QZJ1drMQz1E"),  # Cron Jobs
    # ── Kubernetes ──
    (["kubernetes", "k8s", "pod", "deployment",
      "service", "kubectl", "namespace",
      "replicaset"],                                   "X48VuDVv0do"),  # K8s Tutorial
    # ── Vue.js ──
    (["vue", "composition api", "options api",
      "ref(", "reactive", "v-for", "pinia"],          "qZXt1Aom3Cs"),  # Vue.js Crash
    # ── Next.js ──
    (["next.js", "nextjs", "app router", "server component",
      "server action", "ssr", "ssg", "nextauth",
      "prisma", "vercel"],                             "mTz0GXj8NN0"),  # Next.js Tutorial
    # ── React Native ──
    (["react native", "expo", "core component",
      "asyncstorage", "push уведомл"],                "0-S5a0eXPoc"),  # RN Tutorial
    # ── Flutter ──
    (["flutter", "dart", "widget", "stateful",
      "stateless", "setstate"],                        "VPvVD8t02U8"),  # Flutter Tutorial
    # ── GraphQL ──
    (["graphql", "query", "mutation", "subscription",
      "apollo", "resolver", "schema"],                "ed8SaKjLAPY"),  # GraphQL Tutorial
    # ── Security ──
    (["xss", "cross-site", "инъекци", "sql injection",
      "owasp", "угроз", "фишинг", "malware"],         "EoaDgUgS6QA"),  # Web Security
    (["шифрован", "encrypt", "tls", "ssl", "https",
      "hsts", "симметричн", "асимметричн",
      "хеш", "hash", "salt", "соль"],                 "hExRDVZHhig"),  # Cryptography
    (["csp", "cors", "заголовок", "rate limit",
      "csrf", "защит", "безопасн"],                   "F5KJVuii0Yw"),  # Web App Security
    # ── UI/UX ──
    (["figma", "компонент figma", "auto layout",
      "prototype", "прототип figma"],                 "FTFaQWZBqQ8"),  # Figma Tutorial
    (["ux", "wireframe", "исследован", "юзабилити",
      "тестирован", "persona"],                       "_lyzy-vChh4"),  # UX Design
    (["дизайн-систем", "токен", "handoff",
      "ui kit", "типографик", "цветов"],              "EK-rQYeJQIA"),  # Design Systems
    # ── Алгоритмы ──
    (["big o", "сложност", "нотац"],                   "v4cd1O4zkGw"),  # Big O Notation
    (["сортировк", "sort", "bubble", "quick",
      "merge", "heap"],                               "kPRA0W1kECg"),  # Sorting Algorithms
    (["бинарн", "binary search", "поиск"],             "P3YID7pr0pA"),  # Binary Search
    (["рекурс", "recursion", "стек вызов"],            "IJDJ0kBx2LM"),  # Recursion
    (["связн список", "linked list"],                   "FSsriWQ0qYE"),  # Linked List
    (["стек", "stack", "очередь", "queue"],            "wjI1WNcIntg"),  # Stack & Queue
    (["дерево", "tree", "bst"],                        "fAAZixBzIAI"),  # Trees
    (["хеш-таблиц", "hash table"],                     "jalSiaIi8j4"),  # Hash Tables
    # ── Английский ──
    (["документац", "readme", "it терминolog",
      "английск", "english", "lgtm",
      "деловая", "email", "переписк"],                "cVwmSL7bKa8"),  # English for Devs
]

DEFAULT_VIDEO = "https://www.youtube.com/watch?v=rfscVS0vtbw"  # fallback


def get_video_url(lesson_title: str) -> str:
    """Find a relevant YouTube video URL based on lesson title keywords."""
    title_lower = lesson_title.lower()
    for keywords, video_id in VIDEO_MAP:
        for kw in keywords:
            if kw in title_lower:
                return f"https://www.youtube.com/watch?v={video_id}"
    return DEFAULT_VIDEO


CATEGORIES = [
    {"name": "Веб-разработка", "slug": "web-dev"},
    {"name": "Python", "slug": "python"},
    {"name": "Data Science", "slug": "data-science"},
    {"name": "Мобильная разработка", "slug": "mobile"},
    {"name": "DevOps", "slug": "devops"},
    {"name": "Кибербезопасность", "slug": "security"},
    {"name": "UI/UX Дизайн", "slug": "uiux"},
    {"name": "Базы данных", "slug": "databases"},
]

# Unsplash cover images for each course (stored as URL strings in ImageField)
# getMediaUrl() on the frontend returns http URLs as-is, so this works without file upload
COURSE_IMAGES = {
    "HTML и CSS с нуля":                        "https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&h=450&fit=crop&auto=format",
    "JavaScript для начинающих":                "https://images.unsplash.com/photo-1555066931-4138f20af03c?w=800&h=450&fit=crop&auto=format",
    "React.js: полный курс":                    "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&h=450&fit=crop&auto=format",
    "TypeScript с нуля":                        "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=450&fit=crop&auto=format",
    "Node.js и Express":                        "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=450&fit=crop&auto=format",
    "GraphQL API":                              "https://images.unsplash.com/photo-1633356122102-3fe601e05bd2?w=800&h=450&fit=crop&auto=format",
    "Vue.js 3":                                 "https://images.unsplash.com/photo-1547082299-de196ea013d6?w=800&h=450&fit=crop&auto=format",
    "Next.js: Full-Stack React":                "https://images.unsplash.com/photo-1561736778-92e52a7769ef?w=800&h=450&fit=crop&auto=format",
    "Python для начинающих":                    "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=800&h=450&fit=crop&auto=format",
    "Django: веб-фреймворк":                   "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=450&fit=crop&auto=format",
    "FastAPI: современный Python API":          "https://images.unsplash.com/photo-1516116216624-53e697fedbea?w=800&h=450&fit=crop&auto=format",
    "Автоматизация с Python":                   "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&h=450&fit=crop&auto=format",
    "Data Science с Python":                    "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&h=450&fit=crop&auto=format",
    "Машинное обучение":                        "https://images.unsplash.com/photo-1507146153580-3dec1b756403?w=800&h=450&fit=crop&auto=format",
    "SQL и базы данных":                        "https://images.unsplash.com/photo-1544383835-bda2bc66a2e2?w=800&h=450&fit=crop&auto=format",
    "Redis: кеширование и очереди":             "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=800&h=450&fit=crop&auto=format",
    "MongoDB: NoSQL базы данных":               "https://images.unsplash.com/photo-1544383835-bda2bc66a2e2?w=800&h=450&fit=crop&auto=format",
    "Docker с нуля":                            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=450&fit=crop&auto=format",
    "Linux для разработчиков":                  "https://images.unsplash.com/photo-1555066931-4138f20af03c?w=800&h=450&fit=crop&auto=format",
    "Git и GitHub":                             "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=800&h=450&fit=crop&auto=format",
    "Kubernetes для разработчиков":             "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&h=450&fit=crop&auto=format",
    "Основы кибербезопасности":                 "https://images.unsplash.com/photo-1555949963-ff9fe0c870ca?w=800&h=450&fit=crop&auto=format",
    "React Native: мобильные приложения":       "https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?w=800&h=450&fit=crop&auto=format",
    "Flutter: кроссплатформенная разработка":   "https://images.unsplash.com/photo-1606868306217-dbf5046868d2?w=800&h=450&fit=crop&auto=format",
    "UI/UX дизайн с нуля":                      "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800&h=450&fit=crop&auto=format",
    "Алгоритмы и структуры данных":             "https://images.unsplash.com/photo-1509228468518-180dd4864904?w=800&h=450&fit=crop&auto=format",
    "Английский для IT":                        "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=800&h=450&fit=crop&auto=format",
}

# YouTube video IDs (real educational videos)
YOUTUBE_VIDEOS = [
    "https://www.youtube.com/watch?v=qz0aGYrrlhU",
    "https://www.youtube.com/watch?v=W6NZfCO5SIk",
    "https://www.youtube.com/watch?v=rfscVS0vtbw",
    "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
    "https://www.youtube.com/watch?v=8JJ101D3knE",
    "https://www.youtube.com/watch?v=ok-plXXHlWw",
    "https://www.youtube.com/watch?v=pTB0EiLXUC8",
    "https://www.youtube.com/watch?v=PlbupGCBV6w",
    "https://www.youtube.com/watch?v=HXV3zeQKqGY",
    "https://www.youtube.com/watch?v=7S_tz1z_5bA",
    "https://www.youtube.com/watch?v=ZxKM3DCV2kE",
    "https://www.youtube.com/watch?v=mU6anWqZJcc",
    "https://www.youtube.com/watch?v=fqMOX6JJhGo",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=UB1O30fR-EE",
    "https://www.youtube.com/watch?v=Ke90Tje7VS0",
    "https://www.youtube.com/watch?v=yfoY53QXEnI",
    "https://www.youtube.com/watch?v=4UZrsTqkcW4",
    "https://www.youtube.com/watch?v=ysEN5RaKOlA",
    "https://www.youtube.com/watch?v=nu_pCVPKzTk",
]

COURSES_DATA = [
    # ── Веб-разработка ──
    {
        "title": "HTML и CSS с нуля",
        "description": "Полный курс по HTML5 и CSS3 для начинающих. Научитесь создавать современные веб-страницы с нуля, изучите семантическую вёрстку, flexbox, grid и адаптивный дизайн.",
        "category": "web-dev",
        "price": 0,
        "modules": [
            {
                "title": "Основы HTML",
                "lessons": ["Что такое HTML и как работает браузер", "Теги, атрибуты и структура документа", "Семантические теги HTML5", "Формы и элементы ввода"],
                "test": {
                    "title": "Тест: Основы HTML",
                    "questions": [
                        {"text": "Какой тег используется для создания заголовка первого уровня?", "answers": ["<h1>", "<header>", "<title>", "<heading>"], "correct": 0},
                        {"text": "Что означает аббревиатура HTML?", "answers": ["HyperText Markup Language", "High Tech Modern Language", "HyperTransfer Markup Links", "Home Tool Markup Language"], "correct": 0},
                        {"text": "Какой атрибут задаёт адрес ссылки?", "answers": ["src", "href", "link", "url"], "correct": 1},
                        {"text": "Какой тег создаёт маркированный список?", "answers": ["<ol>", "<dl>", "<ul>", "<li>"], "correct": 2},
                        {"text": "Для чего используется тег <meta>?", "answers": ["Для создания таблиц", "Для метаданных страницы", "Для мультимедиа", "Для ссылок"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Основы CSS",
                "lessons": ["Селекторы и специфичность", "Box model: margin, padding, border", "Flexbox layout", "CSS Grid"],
                "test": {
                    "title": "Тест: Основы CSS",
                    "questions": [
                        {"text": "Какое свойство меняет цвет текста?", "answers": ["background-color", "font-color", "color", "text-color"], "correct": 2},
                        {"text": "Как выровнять элементы по центру во Flexbox?", "answers": ["align: center", "justify-content: center", "text-align: center", "center: flex"], "correct": 1},
                        {"text": "Какое значение display создаёт flex-контейнер?", "answers": ["block", "inline", "flex", "grid"], "correct": 2},
                        {"text": "Какое свойство задаёт отступ внутри элемента?", "answers": ["margin", "padding", "border", "spacing"], "correct": 1},
                        {"text": "Чему равна специфичность id-селектора?", "answers": ["0,0,1", "0,1,0", "1,0,0", "0,0,0"], "correct": 2},
                    ]
                }
            },
            {
                "title": "Адаптивный дизайн",
                "lessons": ["Media queries", "Mobile-first подход", "Адаптивные изображения", "Финальный проект: лендинг"],
                "test": {
                    "title": "Тест: Адаптивный дизайн",
                    "questions": [
                        {"text": "Что такое media query?", "answers": ["Тип базы данных", "Правило CSS для разных устройств", "JavaScript функция", "HTML тег"], "correct": 1},
                        {"text": "Какой viewport мета-тег обязателен для адаптивности?", "answers": ["<meta name='viewport' content='width=device-width'>", "<meta name='mobile'>", "<meta name='responsive'>", "<meta name='screen'>"], "correct": 0},
                        {"text": "Что означает mobile-first?", "answers": ["Разработка только для мобильных", "Начинать стили с мобильных устройств", "Запрет десктопной версии", "Использование мобильных фреймворков"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "JavaScript для начинающих",
        "description": "Изучите JavaScript с нуля — от переменных и функций до асинхронного программирования. Практические задания и проекты на каждом этапе.",
        "category": "web-dev",
        "price": 4900,
        "modules": [
            {
                "title": "Основы JavaScript",
                "lessons": ["Переменные: var, let, const", "Типы данных и операторы", "Условия и циклы", "Функции и стрелочные функции"],
                "test": {
                    "title": "Тест: Основы JS",
                    "questions": [
                        {"text": "Какой оператор строгого равенства в JS?", "answers": ["==", "===", "=", "!="], "correct": 1},
                        {"text": "Что выведет: typeof null?", "answers": ["null", "undefined", "object", "string"], "correct": 2},
                        {"text": "Как объявить стрелочную функцию?", "answers": ["function() {}", "() => {}", "func() {}", "arrow() {}"], "correct": 1},
                        {"text": "Что делает метод console.log()?", "answers": ["Создаёт переменную", "Выводит в консоль", "Удаляет элемент", "Отправляет запрос"], "correct": 1},
                        {"text": "Какой метод добавляет элемент в конец массива?", "answers": ["push()", "pop()", "shift()", "unshift()"], "correct": 0},
                    ]
                }
            },
            {
                "title": "DOM и события",
                "lessons": ["DOM: структура и методы", "Поиск элементов", "Обработчики событий", "Динамическое изменение страницы"],
                "test": {
                    "title": "Тест: DOM",
                    "questions": [
                        {"text": "Какой метод ищет элемент по id?", "answers": ["querySelector", "getElementById", "getElement", "findById"], "correct": 1},
                        {"text": "Как добавить обработчик события?", "answers": ["element.on('click')", "element.addEventListener('click', fn)", "element.click(fn)", "element.event('click')"], "correct": 1},
                        {"text": "Что такое DOM?", "answers": ["Язык программирования", "Объектная модель документа", "База данных", "Протокол передачи данных"], "correct": 1},
                        {"text": "Какое свойство меняет HTML-содержимое элемента?", "answers": ["textContent", "innerHTML", "value", "src"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Асинхронный JS",
                "lessons": ["Callbacks и callback hell", "Промисы (Promise)", "Async/Await", "Fetch API и работа с REST"],
                "test": {
                    "title": "Тест: Async JS",
                    "questions": [
                        {"text": "Что возвращает async функция?", "answers": ["Число", "Promise", "String", "Array"], "correct": 1},
                        {"text": "Какой метод отлавливает ошибку в Promise?", "answers": [".then()", ".catch()", ".finally()", ".error()"], "correct": 1},
                        {"text": "Что делает await?", "answers": ["Создаёт промис", "Ожидает выполнения промиса", "Отменяет промис", "Клонирует промис"], "correct": 1},
                        {"text": "Какой API используется для HTTP-запросов?", "answers": ["XMLHttpRequest", "fetch()", "request()", "http()"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "React.js: полный курс",
        "description": "Изучите React с основ до продвинутых концепций. Хуки, контекст, Redux, React Router и создание полноценных SPA-приложений.",
        "category": "web-dev",
        "price": 9900,
        "modules": [
            {
                "title": "Основы React",
                "lessons": ["Что такое React и Virtual DOM", "JSX и компоненты", "Props и State", "Lifecycle методы"],
                "test": {
                    "title": "Тест: Основы React",
                    "questions": [
                        {"text": "Что такое JSX?", "answers": ["Java Syntax Extension", "JavaScript XML", "JSON Extension", "Java Script XML"], "correct": 1},
                        {"text": "Для чего нужен useState?", "answers": ["Создать компонент", "Управлять локальным состоянием", "Делать HTTP запросы", "Работать с DOM"], "correct": 1},
                        {"text": "Что такое props?", "answers": ["Состояние компонента", "Данные, передаваемые в компонент", "Хуки React", "CSS стили"], "correct": 1},
                        {"text": "Какой хук используется для побочных эффектов?", "answers": ["useState", "useEffect", "useContext", "useRef"], "correct": 1},
                        {"text": "Как называется виртуальная DOM в React?", "answers": ["Real DOM", "Shadow DOM", "Virtual DOM", "Fake DOM"], "correct": 2},
                    ]
                }
            },
            {
                "title": "React Hooks",
                "lessons": ["useState и useReducer", "useEffect и зависимости", "useContext и Provider", "Кастомные хуки"],
                "test": {
                    "title": "Тест: React Hooks",
                    "questions": [
                        {"text": "Правило хуков: хуки можно вызывать...", "answers": ["Внутри условий", "Внутри циклов", "На верхнем уровне компонента", "Внутри вложенных функций"], "correct": 2},
                        {"text": "Какой хук заменяет this.setState?", "answers": ["useEffect", "useState", "useRef", "useMemo"], "correct": 1},
                        {"text": "Для чего нужен useCallback?", "answers": ["Мемоизация функций", "Работа с API", "Роутинг", "Работа с DOM"], "correct": 0},
                    ]
                }
            },
            {
                "title": "Управление состоянием",
                "lessons": ["Context API", "Redux Toolkit основы", "Async actions с createAsyncThunk", "Финальный проект: Todo App"],
                "test": {
                    "title": "Тест: State Management",
                    "questions": [
                        {"text": "Что такое Redux store?", "answers": ["Хранилище состояния", "База данных", "Роутер", "HTTP клиент"], "correct": 0},
                        {"text": "Что такое action в Redux?", "answers": ["Компонент", "Объект с типом и данными", "Функция рендера", "Асинхронный запрос"], "correct": 1},
                        {"text": "Для чего нужен reducer?", "answers": ["Изменять состояние на основе action", "Делать запросы к API", "Рендерить компоненты", "Создавать маршруты"], "correct": 0},
                    ]
                }
            },
        ]
    },
    {
        "title": "TypeScript с нуля",
        "description": "Полный курс по TypeScript. Статическая типизация, интерфейсы, дженерики, декораторы и интеграция с React и Node.js.",
        "category": "web-dev",
        "price": 7900,
        "modules": [
            {
                "title": "Типы и интерфейсы",
                "lessons": ["Базовые типы TypeScript", "Интерфейсы и type aliases", "Union и Intersection типы", "Generics"],
                "test": {
                    "title": "Тест: Типы TypeScript",
                    "questions": [
                        {"text": "Какой тип принимает любое значение?", "answers": ["unknown", "any", "void", "never"], "correct": 1},
                        {"text": "Как объявить интерфейс?", "answers": ["type Name = {}", "interface Name {}", "class Name {}", "struct Name {}"], "correct": 1},
                        {"text": "Что такое generic?", "answers": ["Тип для чисел", "Параметризованный тип", "Тип для строк", "Тип для объектов"], "correct": 1},
                        {"text": "Какое ключевое слово создаёт алиас типа?", "answers": ["interface", "type", "alias", "typedef"], "correct": 1},
                        {"text": "Что означает тип void?", "answers": ["Отсутствие значения", "Любое значение", "Нулевое значение", "Неопределённое значение"], "correct": 0},
                    ]
                }
            },
            {
                "title": "TypeScript и ООП",
                "lessons": ["Классы и наследование", "Модификаторы доступа", "Abstract классы", "Декораторы"],
                "test": {
                    "title": "Тест: ООП в TypeScript",
                    "questions": [
                        {"text": "Какой модификатор доступа скрывает поле от внешнего кода?", "answers": ["public", "protected", "private", "readonly"], "correct": 2},
                        {"text": "Ключевое слово для наследования класса?", "answers": ["implements", "extends", "inherits", "from"], "correct": 1},
                        {"text": "Что такое abstract класс?", "answers": ["Класс без методов", "Класс, который нельзя инстанцировать напрямую", "Статический класс", "Финальный класс"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Node.js и Express",
        "description": "Создавайте серверные приложения на Node.js. REST API, Express.js, middleware, аутентификация JWT, работа с базами данных.",
        "category": "web-dev",
        "price": 8900,
        "modules": [
            {
                "title": "Основы Node.js",
                "lessons": ["Установка и npm", "Модули и require/import", "File System и Path", "HTTP модуль"],
                "test": {
                    "title": "Тест: Node.js основы",
                    "questions": [
                        {"text": "Что такое npm?", "answers": ["Node Package Manager", "Network Protocol Manager", "Node Process Module", "New Programming Method"], "correct": 0},
                        {"text": "Какой метод читает файл асинхронно?", "answers": ["fs.readFile()", "fs.read()", "file.read()", "fs.open()"], "correct": 0},
                        {"text": "Как запустить Node.js скрипт?", "answers": ["node script.js", "run script.js", "start script.js", "exec script.js"], "correct": 0},
                        {"text": "Что такое event loop в Node.js?", "answers": ["База данных", "Механизм обработки асинхронных событий", "Цикл for", "HTTP сервер"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Express.js REST API",
                "lessons": ["Express сервер и роуты", "Middleware", "CRUD операции", "Обработка ошибок"],
                "test": {
                    "title": "Тест: Express.js",
                    "questions": [
                        {"text": "Что такое middleware в Express?", "answers": ["База данных", "Функция между запросом и ответом", "HTML шаблон", "CSS файл"], "correct": 1},
                        {"text": "Какой метод Express обрабатывает GET запросы?", "answers": ["app.post()", "app.get()", "app.put()", "app.fetch()"], "correct": 1},
                        {"text": "Как передать данные в теле запроса?", "answers": ["req.params", "req.query", "req.body", "req.headers"], "correct": 2},
                    ]
                }
            },
        ]
    },

    # ── Python ──
    {
        "title": "Python для начинающих",
        "description": "Научитесь программировать на Python с нуля. Синтаксис, структуры данных, функции, ООП и работа с файлами.",
        "category": "python",
        "price": 0,
        "modules": [
            {
                "title": "Синтаксис Python",
                "lessons": ["Установка Python и первая программа", "Переменные и типы данных", "Операторы и условия", "Циклы for и while"],
                "test": {
                    "title": "Тест: Синтаксис Python",
                    "questions": [
                        {"text": "Как вывести текст в Python?", "answers": ["echo()", "print()", "console.log()", "write()"], "correct": 1},
                        {"text": "Какой тип данных для целых чисел?", "answers": ["float", "int", "str", "bool"], "correct": 1},
                        {"text": "Как начать комментарий в Python?", "answers": ["//", "/*", "#", "--"], "correct": 2},
                        {"text": "Что делает range(5)?", "answers": ["Создаёт список [0,1,2,3,4]", "Генерирует числа от 1 до 5", "Возвращает 5", "Создаёт кортеж"], "correct": 0},
                        {"text": "Оператор целочисленного деления в Python?", "answers": ["/", "//", "%", "**"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Структуры данных",
                "lessons": ["Списки и методы list", "Словари и множества", "Кортежи", "List comprehension"],
                "test": {
                    "title": "Тест: Структуры данных Python",
                    "questions": [
                        {"text": "Какая структура данных неизменяема?", "answers": ["list", "dict", "tuple", "set"], "correct": 2},
                        {"text": "Как добавить элемент в список?", "answers": ["list.add()", "list.append()", "list.insert(0)", "list.push()"], "correct": 1},
                        {"text": "Как получить значение из словаря по ключу?", "answers": ["dict[key]", "dict.get(key)", "dict->key", "dict.key"], "correct": 0},
                        {"text": "Что такое set?", "answers": ["Список с дублями", "Коллекция уникальных элементов", "Словарь", "Кортеж"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Функции и ООП",
                "lessons": ["Функции и параметры", "Lambda функции", "Классы и объекты", "Наследование в Python"],
                "test": {
                    "title": "Тест: Функции и ООП",
                    "questions": [
                        {"text": "Ключевое слово для создания функции?", "answers": ["function", "def", "func", "fn"], "correct": 1},
                        {"text": "Что такое self в методе класса?", "answers": ["Статический метод", "Ссылка на экземпляр класса", "Глобальная переменная", "Конструктор"], "correct": 1},
                        {"text": "Как создать класс в Python?", "answers": ["class MyClass:", "def MyClass:", "struct MyClass:", "object MyClass:"], "correct": 0},
                        {"text": "Что делает __init__?", "answers": ["Удаляет объект", "Инициализирует объект", "Создаёт статический метод", "Вызывает родительский класс"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Django: веб-фреймворк",
        "description": "Создавайте веб-приложения с Django. ORM, views, templates, REST API с Django REST Framework и аутентификация.",
        "category": "python",
        "price": 11900,
        "modules": [
            {
                "title": "Основы Django",
                "lessons": ["Установка и структура проекта", "Models и ORM", "Views и URL routing", "Templates и статика"],
                "test": {
                    "title": "Тест: Основы Django",
                    "questions": [
                        {"text": "Что такое ORM?", "answers": ["Object Relational Mapping", "Online Request Module", "Output Rendering Method", "Object Resource Manager"], "correct": 0},
                        {"text": "Как применить миграции?", "answers": ["python manage.py migrate", "django migrate", "python migrate.py", "manage migrate"], "correct": 0},
                        {"text": "Что хранит файл models.py?", "answers": ["URL маршруты", "Модели базы данных", "HTML шаблоны", "Настройки проекта"], "correct": 1},
                        {"text": "Как запустить Django сервер?", "answers": ["python manage.py runserver", "django start", "python server.py", "run django"], "correct": 0},
                        {"text": "Что такое MTV в Django?", "answers": ["Model-Template-View", "Module-Type-Variable", "Management-Tool-Version", "Method-Type-View"], "correct": 0},
                    ]
                }
            },
            {
                "title": "Django REST Framework",
                "lessons": ["Serializers", "ViewSets и Routers", "Permissions и Authentication", "JWT токены"],
                "test": {
                    "title": "Тест: DRF",
                    "questions": [
                        {"text": "Для чего нужны Serializers?", "answers": ["Для создания URL", "Для сериализации данных (Python <-> JSON)", "Для миграций", "Для статических файлов"], "correct": 1},
                        {"text": "Что такое ViewSet?", "answers": ["HTML шаблон", "Набор CRUD операций в одном классе", "URL конфигурация", "Модель данных"], "correct": 1},
                        {"text": "Какой permission требует аутентификации?", "answers": ["AllowAny", "IsAuthenticated", "IsAdminUser", "IsOwner"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "FastAPI: современный Python API",
        "description": "Изучите FastAPI — самый быстрый Python веб-фреймворк. Async/await, Pydantic, автодокументация, OAuth2 и развёртывание.",
        "category": "python",
        "price": 9900,
        "modules": [
            {
                "title": "Основы FastAPI",
                "lessons": ["Установка и первый эндпоинт", "Path и Query параметры", "Pydantic модели", "Async эндпоинты"],
                "test": {
                    "title": "Тест: FastAPI",
                    "questions": [
                        {"text": "Что автоматически генерирует FastAPI?", "answers": ["Базу данных", "Документацию API (Swagger)", "Frontend интерфейс", "Миграции"], "correct": 1},
                        {"text": "Какая библиотека используется для валидации в FastAPI?", "answers": ["Marshmallow", "Pydantic", "Cerberus", "Voluptuous"], "correct": 1},
                        {"text": "Для чего нужен декоратор @app.get()?", "answers": ["Создаёт GET эндпоинт", "Получает данные из БД", "Делает HTTP запрос", "Создаёт переменную"], "correct": 0},
                        {"text": "Что такое dependency injection в FastAPI?", "answers": ["Установка зависимостей pip", "Система передачи зависимостей в функции", "Тип базы данных", "Метод аутентификации"], "correct": 1},
                    ]
                }
            },
            {
                "title": "FastAPI и базы данных",
                "lessons": ["SQLAlchemy с FastAPI", "Alembic миграции", "Async SQLAlchemy", "Тестирование API"],
                "test": {
                    "title": "Тест: FastAPI + DB",
                    "questions": [
                        {"text": "Что такое SQLAlchemy?", "answers": ["ORM для Python", "Язык запросов", "База данных", "Frontend фреймворк"], "correct": 0},
                        {"text": "Для чего нужен Alembic?", "answers": ["Тестирование", "Управление миграциями БД", "Документация", "Аутентификация"], "correct": 1},
                        {"text": "Какой метод тестирует FastAPI приложение?", "answers": ["TestClient", "APIClient", "TestRunner", "MockClient"], "correct": 0},
                    ]
                }
            },
        ]
    },
    {
        "title": "Автоматизация с Python",
        "description": "Автоматизируйте рутинные задачи с Python: парсинг сайтов, работа с Excel/PDF, автоматизация браузера и планировщик задач.",
        "category": "python",
        "price": 5900,
        "modules": [
            {
                "title": "Парсинг веб-сайтов",
                "lessons": ["Библиотека requests", "BeautifulSoup4", "Selenium и автоматизация браузера", "Scrapy фреймворк"],
                "test": {
                    "title": "Тест: Парсинг",
                    "questions": [
                        {"text": "Какая библиотека делает HTTP запросы?", "answers": ["urllib", "requests", "fetch", "httplib"], "correct": 1},
                        {"text": "Что такое BeautifulSoup?", "answers": ["База данных", "Библиотека парсинга HTML/XML", "Web фреймворк", "ORM"], "correct": 1},
                        {"text": "Для чего нужен Selenium?", "answers": ["Парсинг статических страниц", "Автоматизация браузера", "Работа с API", "Создание веб-сервера"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Работа с файлами",
                "lessons": ["openpyxl: Excel автоматизация", "PyPDF2: работа с PDF", "Работа с изображениями Pillow", "Планировщик задач schedule"],
                "test": {
                    "title": "Тест: Автоматизация файлов",
                    "questions": [
                        {"text": "Какая библиотека работает с Excel?", "answers": ["pandas", "openpyxl", "xlrd", "Все перечисленные"], "correct": 3},
                        {"text": "Как открыть файл в Python?", "answers": ["file.open()", "open()", "File()", "read()"], "correct": 1},
                        {"text": "Что такое PIL/Pillow?", "answers": ["PDF библиотека", "Библиотека обработки изображений", "Excel библиотека", "Email библиотека"], "correct": 1},
                    ]
                }
            },
        ]
    },

    # ── Data Science ──
    {
        "title": "Data Science с Python",
        "description": "Полный курс по Data Science. NumPy, Pandas, Matplotlib, Seaborn, анализ данных и создание отчётов.",
        "category": "data-science",
        "price": 13900,
        "modules": [
            {
                "title": "NumPy и Pandas",
                "lessons": ["NumPy массивы и операции", "Pandas DataFrame", "Загрузка и очистка данных", "Группировка и агрегация"],
                "test": {
                    "title": "Тест: NumPy и Pandas",
                    "questions": [
                        {"text": "Что такое DataFrame в Pandas?", "answers": ["Массив чисел", "Двумерная таблица данных", "Тип переменной", "Функция"], "correct": 1},
                        {"text": "Как загрузить CSV файл в Pandas?", "answers": ["pd.load_csv()", "pd.read_csv()", "pd.open_csv()", "pd.import_csv()"], "correct": 1},
                        {"text": "Что делает df.dropna()?", "answers": ["Удаляет дублирующиеся строки", "Удаляет строки с NaN", "Заполняет пустые значения", "Сортирует данные"], "correct": 1},
                        {"text": "Функция NumPy для среднего значения?", "answers": ["np.mean()", "np.avg()", "np.average()", "np.median()"], "correct": 0},
                        {"text": "Как выбрать столбец в Pandas?", "answers": ["df.column", "df['column']", "df.get('column')", "df.select('column')"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Визуализация данных",
                "lessons": ["Matplotlib основы", "Seaborn статистические графики", "Plotly интерактивные графики", "Дашборды с Dash"],
                "test": {
                    "title": "Тест: Визуализация",
                    "questions": [
                        {"text": "Какая библиотека создаёт интерактивные графики?", "answers": ["Matplotlib", "Seaborn", "Plotly", "NumPy"], "correct": 2},
                        {"text": "Как создать гистограмму в Matplotlib?", "answers": ["plt.bar()", "plt.hist()", "plt.line()", "plt.scatter()"], "correct": 1},
                        {"text": "Для чего нужен Seaborn?", "answers": ["Машинное обучение", "Статистическая визуализация", "Обработка текста", "Веб-скрапинг"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Машинное обучение с sklearn",
                "lessons": ["Введение в ML", "Линейная регрессия", "Классификация и деревья решений", "Метрики качества модели"],
                "test": {
                    "title": "Тест: ML основы",
                    "questions": [
                        {"text": "Что такое обучение с учителем?", "answers": ["Обучение по видеоурокам", "Обучение на размеченных данных", "Обучение без данных", "Обучение на изображениях"], "correct": 1},
                        {"text": "Для чего нужен train_test_split?", "answers": ["Разделить данные на обучение и тест", "Создать модель", "Визуализировать данные", "Очистить данные"], "correct": 0},
                        {"text": "Что такое overfitting?", "answers": ["Недообучение модели", "Переобучение: хорошо на обучении, плохо на тесте", "Правильная модель", "Быстрая модель"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Машинное обучение",
        "description": "Глубокое погружение в ML. Алгоритмы от линейной регрессии до нейронных сетей. TensorFlow, Keras, scikit-learn.",
        "category": "data-science",
        "price": 19900,
        "modules": [
            {
                "title": "Классические алгоритмы ML",
                "lessons": ["KNN: k ближайших соседей", "SVM: метод опорных векторов", "Random Forest", "Градиентный бустинг"],
                "test": {
                    "title": "Тест: Алгоритмы ML",
                    "questions": [
                        {"text": "Что такое Random Forest?", "answers": ["Один граф решений", "Ансамбль деревьев решений", "Нейронная сеть", "Кластеризация"], "correct": 1},
                        {"text": "Метрика для задачи классификации?", "answers": ["MSE", "RMSE", "Accuracy (точность)", "MAE"], "correct": 2},
                        {"text": "Для чего нужна кросс-валидация?", "answers": ["Обучить модель быстрее", "Оценить обобщающую способность модели", "Визуализировать данные", "Очистить данные"], "correct": 1},
                        {"text": "Что такое признаки (features) в ML?", "answers": ["Метки классов", "Входные переменные для модели", "Результаты предсказания", "Параметры алгоритма"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Нейронные сети",
                "lessons": ["Перцептрон и многослойная сеть", "Keras и TensorFlow", "CNN для изображений", "RNN и LSTM"],
                "test": {
                    "title": "Тест: Нейронные сети",
                    "questions": [
                        {"text": "Что такое нейрон в нейросети?", "answers": ["Клетка мозга", "Математическая функция, обрабатывающая входы", "База данных", "Слой данных"], "correct": 1},
                        {"text": "Что делает функция активации?", "answers": ["Обучает сеть", "Вводит нелинейность", "Нормализует данные", "Создаёт слои"], "correct": 1},
                        {"text": "Для чего CNN?", "answers": ["Обработка текста", "Обработка изображений", "Временные ряды", "Табличные данные"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "SQL и базы данных",
        "description": "Изучите SQL от основ до продвинутого уровня. SELECT, JOIN, индексы, оптимизация запросов, PostgreSQL и проектирование баз данных.",
        "category": "databases",
        "price": 6900,
        "modules": [
            {
                "title": "Основы SQL",
                "lessons": ["DDL: CREATE TABLE, ALTER", "DML: SELECT, INSERT, UPDATE, DELETE", "WHERE, ORDER BY, GROUP BY", "Агрегатные функции"],
                "test": {
                    "title": "Тест: Основы SQL",
                    "questions": [
                        {"text": "Какой оператор выбирает данные?", "answers": ["INSERT", "SELECT", "UPDATE", "CREATE"], "correct": 1},
                        {"text": "Как удалить все строки таблицы без удаления структуры?", "answers": ["DROP TABLE", "DELETE FROM table", "TRUNCATE TABLE", "REMOVE FROM"], "correct": 2},
                        {"text": "Что делает GROUP BY?", "answers": ["Сортирует строки", "Группирует строки по значению", "Фильтрует строки", "Объединяет таблицы"], "correct": 1},
                        {"text": "Какая функция считает количество строк?", "answers": ["SUM()", "AVG()", "COUNT()", "MAX()"], "correct": 2},
                        {"text": "Что такое PRIMARY KEY?", "answers": ["Внешний ключ", "Уникальный идентификатор строки", "Индекс", "Тип данных"], "correct": 1},
                    ]
                }
            },
            {
                "title": "JOIN и подзапросы",
                "lessons": ["INNER JOIN", "LEFT, RIGHT, FULL JOIN", "Подзапросы и CTE", "Оконные функции"],
                "test": {
                    "title": "Тест: JOIN",
                    "questions": [
                        {"text": "Что возвращает INNER JOIN?", "answers": ["Все строки левой таблицы", "Только совпадающие строки из обеих таблиц", "Все строки", "Строки без совпадений"], "correct": 1},
                        {"text": "LEFT JOIN возвращает...", "answers": ["Только правую таблицу", "Все строки левой + совпадения правой", "Только совпадения", "Все строки обеих таблиц"], "correct": 1},
                        {"text": "Что такое CTE?", "answers": ["Common Table Expression — временный именованный результат запроса", "CREATE TABLE Extension", "Column Type Entity", "Composite Table Element"], "correct": 0},
                    ]
                }
            },
            {
                "title": "Проектирование баз данных",
                "lessons": ["Нормальные формы (1NF, 2NF, 3NF)", "ER-диаграммы", "Индексы и производительность", "PostgreSQL vs MySQL"],
                "test": {
                    "title": "Тест: Проектирование БД",
                    "questions": [
                        {"text": "Что такое нормализация?", "answers": ["Ускорение запросов", "Устранение избыточности данных", "Добавление индексов", "Создание резервных копий"], "correct": 1},
                        {"text": "Для чего нужен индекс?", "answers": ["Хранить данные", "Ускорить поиск по таблице", "Создавать связи", "Нормализовать данные"], "correct": 1},
                        {"text": "Что такое Foreign Key?", "answers": ["Главный ключ таблицы", "Ключ для шифрования", "Ссылка на первичный ключ другой таблицы", "Уникальное поле"], "correct": 2},
                    ]
                }
            },
        ]
    },

    # ── DevOps ──
    {
        "title": "Docker с нуля",
        "description": "Контейнеризация приложений с Docker. Dockerfile, Docker Compose, сети, тома и развёртывание в продакшн.",
        "category": "devops",
        "price": 8900,
        "modules": [
            {
                "title": "Основы Docker",
                "lessons": ["Что такое контейнеры и Docker", "Dockerfile и образы", "Запуск и управление контейнерами", "Docker Hub и реестры"],
                "test": {
                    "title": "Тест: Основы Docker",
                    "questions": [
                        {"text": "Что такое Docker Image?", "answers": ["Запущенный контейнер", "Шаблон для создания контейнера", "База данных", "Сервер"], "correct": 1},
                        {"text": "Команда для запуска контейнера?", "answers": ["docker start", "docker run", "docker exec", "docker create"], "correct": 1},
                        {"text": "Что хранит Dockerfile?", "answers": ["Конфигурацию сети", "Инструкции для сборки образа", "Данные БД", "Логи"], "correct": 1},
                        {"text": "Как посмотреть запущенные контейнеры?", "answers": ["docker images", "docker ps", "docker list", "docker show"], "correct": 1},
                        {"text": "Что такое Docker Hub?", "answers": ["Локальный реестр", "Облачный реестр Docker образов", "Docker сеть", "Инструмент мониторинга"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Docker Compose",
                "lessons": ["Файл docker-compose.yml", "Многоконтейнерные приложения", "Сети и volumes", "Продакшн конфигурация"],
                "test": {
                    "title": "Тест: Docker Compose",
                    "questions": [
                        {"text": "Для чего Docker Compose?", "answers": ["Создать один контейнер", "Управлять несколькими контейнерами", "Публиковать образы", "Мониторинг"], "correct": 1},
                        {"text": "Команда для запуска Compose?", "answers": ["docker compose run", "docker compose up", "docker compose start", "docker compose exec"], "correct": 1},
                        {"text": "Что такое volume в Docker?", "answers": ["Память контейнера", "Постоянное хранилище данных", "Сетевой интерфейс", "Переменная окружения"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Linux для разработчиков",
        "description": "Освойте командную строку Linux. Bash скрипты, управление процессами, сеть, пользователи и настройка серверов.",
        "category": "devops",
        "price": 5900,
        "modules": [
            {
                "title": "Командная строка Bash",
                "lessons": ["Навигация и файловая система", "Работа с файлами (cp, mv, rm)", "Права доступа chmod", "Переменные окружения"],
                "test": {
                    "title": "Тест: Bash",
                    "questions": [
                        {"text": "Команда для просмотра текущей директории?", "answers": ["ls", "pwd", "cd", "dir"], "correct": 1},
                        {"text": "Как сделать файл исполняемым?", "answers": ["chmod +x file", "exec file", "run file", "set file"], "correct": 0},
                        {"text": "Что делает команда grep?", "answers": ["Копирует файлы", "Ищет паттерн в файле", "Удаляет файлы", "Переименовывает файлы"], "correct": 1},
                        {"text": "Как перейти в домашнюю директорию?", "answers": ["cd /home", "cd ~", "cd /root", "cd home"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Bash скрипты",
                "lessons": ["Написание bash скриптов", "Переменные и условия", "Циклы в Bash", "Cron: планировщик задач"],
                "test": {
                    "title": "Тест: Bash скрипты",
                    "questions": [
                        {"text": "Первая строка bash скрипта (shebang)?", "answers": ["#!/bin/bash", "# bash", "//bin/bash", "#!/usr/bin/bash"], "correct": 0},
                        {"text": "Как передать аргумент в скрипт?", "answers": ["script.sh -arg", "script.sh arg", "Оба варианта верны", "Нельзя"], "correct": 2},
                        {"text": "Как задать cron задачу каждую минуту?", "answers": ["* * * * *", "0 * * * *", "* 0 * * *", "1 * * * *"], "correct": 0},
                    ]
                }
            },
        ]
    },
    {
        "title": "Git и GitHub",
        "description": "Система контроля версий Git. Ветвление, слияние, работа с удалёнными репозиториями, GitHub Flow и Code Review.",
        "category": "devops",
        "price": 0,
        "modules": [
            {
                "title": "Основы Git",
                "lessons": ["Установка и настройка Git", "Инициализация репозитория", "Коммиты и история", "Ветки и слияние"],
                "test": {
                    "title": "Тест: Основы Git",
                    "questions": [
                        {"text": "Команда для создания коммита?", "answers": ["git add", "git commit", "git push", "git save"], "correct": 1},
                        {"text": "Как создать новую ветку?", "answers": ["git branch name", "git checkout -b name", "Оба варианта", "git new name"], "correct": 2},
                        {"text": "Что делает git clone?", "answers": ["Создаёт ветку", "Копирует репозиторий", "Удаляет файлы", "Обновляет код"], "correct": 1},
                        {"text": "Что хранит .gitignore?", "answers": ["История коммитов", "Паттерны файлов, которые не отслеживаются", "Настройки репозитория", "Удалённые репозитории"], "correct": 1},
                        {"text": "Команда для отправки изменений на GitHub?", "answers": ["git pull", "git fetch", "git push", "git send"], "correct": 2},
                    ]
                }
            },
            {
                "title": "GitHub и командная работа",
                "lessons": ["Fork и Pull Request", "Code Review", "GitHub Actions CI/CD", "Защита веток"],
                "test": {
                    "title": "Тест: GitHub",
                    "questions": [
                        {"text": "Что такое Pull Request?", "answers": ["Запрос на получение данных", "Запрос на слияние изменений", "Создание нового репозитория", "Удаление ветки"], "correct": 1},
                        {"text": "Для чего нужен GitHub Actions?", "answers": ["Хранение файлов", "Автоматизация CI/CD процессов", "Code Review", "Управление доступом"], "correct": 1},
                        {"text": "Что такое fork репозитория?", "answers": ["Создание копии репозитория", "Удаление репозитория", "Переименование репозитория", "Архивирование репозитория"], "correct": 0},
                    ]
                }
            },
        ]
    },
    {
        "title": "Kubernetes для разработчиков",
        "description": "Оркестрация контейнеров с Kubernetes. Pods, Deployments, Services, ConfigMaps и развёртывание микросервисов.",
        "category": "devops",
        "price": 14900,
        "modules": [
            {
                "title": "Основы Kubernetes",
                "lessons": ["Архитектура Kubernetes", "Pods и контейнеры", "Deployments и ReplicaSets", "Services и сети"],
                "test": {
                    "title": "Тест: Kubernetes",
                    "questions": [
                        {"text": "Что такое Pod в Kubernetes?", "answers": ["Виртуальная машина", "Наименьшая единица развёртывания", "База данных", "Сеть"], "correct": 1},
                        {"text": "Для чего нужен Deployment?", "answers": ["Хранить данные", "Управлять репликами Pods", "Конфигурировать сеть", "Логировать"], "correct": 1},
                        {"text": "Команда для просмотра Pods?", "answers": ["kubectl list pods", "kubectl get pods", "kubectl show pods", "kubectl ps"], "correct": 1},
                        {"text": "Что такое namespace в K8s?", "answers": ["Имя сервиса", "Логическое разделение ресурсов", "Тип хранилища", "Конфигурация сети"], "correct": 1},
                    ]
                }
            },
        ]
    },

    # ── Кибербезопасность ──
    {
        "title": "Основы кибербезопасности",
        "description": "Введение в кибербезопасность. Типы атак, методы защиты, шифрование, безопасная аутентификация и OWASP Top 10.",
        "category": "security",
        "price": 9900,
        "modules": [
            {
                "title": "Типы угроз",
                "lessons": ["Социальная инженерия и фишинг", "Вредоносное ПО (malware)", "SQL инъекции", "XSS атаки"],
                "test": {
                    "title": "Тест: Типы угроз",
                    "questions": [
                        {"text": "Что такое фишинг?", "answers": ["Тип шифрования", "Обман пользователей для получения данных", "Вирус", "DoS атака"], "correct": 1},
                        {"text": "SQL инъекция — это...", "answers": ["Тип шифрования", "Атака через вредоносный SQL код в запросе", "Метод аутентификации", "Тип вируса"], "correct": 1},
                        {"text": "XSS (Cross-Site Scripting) — это...", "answers": ["Межсайтовое выполнение скриптов", "Шифрование данных", "DoS атака", "Метод хеширования"], "correct": 0},
                        {"text": "Что такое OWASP?", "answers": ["Стандарт шифрования", "Организация, публикующая топ уязвимостей веб-приложений", "Язык программирования", "Протокол"], "correct": 1},
                        {"text": "DoS атака направлена на...", "answers": ["Кражу данных", "Отказ в обслуживании (перегрузку сервиса)", "Получение паролей", "Изменение данных"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Шифрование и аутентификация",
                "lessons": ["Симметричное и асимметричное шифрование", "Хеш-функции (MD5, SHA)", "JWT и сессии", "Двухфакторная аутентификация"],
                "test": {
                    "title": "Тест: Шифрование",
                    "questions": [
                        {"text": "Разница между симметричным и асимметричным шифрованием?", "answers": ["Симметричное быстрее, один ключ; асимметричное медленнее, два ключа", "Они одинаковые", "Асимметричное быстрее", "Симметричное использует два ключа"], "correct": 0},
                        {"text": "Что такое соль (salt) при хешировании паролей?", "answers": ["Тип шифрования", "Случайные данные, добавляемые к паролю перед хешированием", "Ключ шифрования", "Алгоритм"], "correct": 1},
                        {"text": "JWT расшифровывается как...", "answers": ["Java Web Token", "JSON Web Token", "JavaScript Web Transfer", "Just Web Token"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Защита веб-приложений",
                "lessons": ["HTTPS и TLS/SSL", "CSP заголовки", "CORS политики", "Rate limiting и защита API"],
                "test": {
                    "title": "Тест: Защита веб-приложений",
                    "questions": [
                        {"text": "Для чего нужен заголовок HSTS?", "answers": ["Кеширование", "Принудительное HTTPS соединение", "Авторизация", "Сжатие"], "correct": 1},
                        {"text": "Content Security Policy (CSP) защищает от...", "answers": ["SQL инъекций", "XSS атак", "DoS атак", "MITM атак"], "correct": 1},
                        {"text": "Что такое CORS?", "answers": ["Тип атаки", "Cross-Origin Resource Sharing — политика доступа", "Алгоритм шифрования", "Протокол"], "correct": 1},
                    ]
                }
            },
        ]
    },

    # ── Мобильная разработка ──
    {
        "title": "React Native: мобильные приложения",
        "description": "Разработка мобильных приложений на React Native. iOS и Android из одной кодовой базы, навигация, Redux и публикация в сторы.",
        "category": "mobile",
        "price": 12900,
        "modules": [
            {
                "title": "Основы React Native",
                "lessons": ["Установка и Expo CLI", "Core Components", "Стили и StyleSheet", "Навигация с React Navigation"],
                "test": {
                    "title": "Тест: React Native основы",
                    "questions": [
                        {"text": "Чем React Native отличается от React?", "answers": ["Другой синтаксис", "Использует нативные компоненты вместо HTML", "Другой язык", "Только для iOS"], "correct": 1},
                        {"text": "Аналог <div> в React Native?", "answers": ["<div>", "<View>", "<Box>", "<Container>"], "correct": 1},
                        {"text": "Для чего Expo?", "answers": ["Хостинг приложений", "Упрощение разработки и тестирования RN", "База данных", "Авторизация"], "correct": 1},
                        {"text": "Как стилизовать компонент в RN?", "answers": ["CSS файлы", "StyleSheet.create()", "className", "style.css"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Работа с API и состоянием",
                "lessons": ["Fetch и Axios в React Native", "AsyncStorage", "Redux в мобильных приложениях", "Push уведомления"],
                "test": {
                    "title": "Тест: API и State в RN",
                    "questions": [
                        {"text": "Что такое AsyncStorage?", "answers": ["База данных", "Локальное хранилище ключ-значение", "Сетевой запрос", "Push уведомления"], "correct": 1},
                        {"text": "Для чего Axios в мобильных приложениях?", "answers": ["Навигация", "HTTP запросы к API", "Хранение данных", "Анимации"], "correct": 1},
                        {"text": "Как отправить push уведомление?", "answers": ["Только через FCM/APNs", "Только через Expo", "Через FCM, APNs или Expo", "Нельзя"], "correct": 2},
                    ]
                }
            },
        ]
    },
    {
        "title": "Flutter: кроссплатформенная разработка",
        "description": "Создавайте красивые мобильные приложения на Flutter и Dart. Виджеты, анимации, Firebase и публикация в Google Play и App Store.",
        "category": "mobile",
        "price": 11900,
        "modules": [
            {
                "title": "Основы Flutter и Dart",
                "lessons": ["Установка Flutter SDK", "Язык Dart: основы", "Виджеты и дерево виджетов", "StatefulWidget и setState"],
                "test": {
                    "title": "Тест: Flutter основы",
                    "questions": [
                        {"text": "На каком языке пишут Flutter приложения?", "answers": ["JavaScript", "Kotlin", "Dart", "Swift"], "correct": 2},
                        {"text": "Главный строительный блок Flutter?", "answers": ["Component", "Widget", "View", "Element"], "correct": 1},
                        {"text": "Разница StatelessWidget и StatefulWidget?", "answers": ["Нет разницы", "StatefulWidget имеет изменяемое состояние", "StatelessWidget быстрее", "StatefulWidget только для iOS"], "correct": 1},
                        {"text": "Команда для запуска Flutter приложения?", "answers": ["flutter start", "flutter run", "dart run", "flutter launch"], "correct": 1},
                    ]
                }
            },
        ]
    },

    # ── UI/UX ──
    {
        "title": "UI/UX дизайн с нуля",
        "description": "Научитесь проектировать удобные интерфейсы. Figma, принципы UX, прототипирование, дизайн-системы и подготовка к работе.",
        "category": "uiux",
        "price": 7900,
        "modules": [
            {
                "title": "Основы UX дизайна",
                "lessons": ["Что такое UX и почему это важно", "Пользовательские исследования", "Wireframes и прототипы", "Юзабилити-тестирование"],
                "test": {
                    "title": "Тест: UX основы",
                    "questions": [
                        {"text": "Что изучает UX дизайн?", "answers": ["Визуальное оформление", "Пользовательский опыт и удобство", "Программирование", "Маркетинг"], "correct": 1},
                        {"text": "Что такое wireframe?", "answers": ["Финальный дизайн", "Схематичный каркас интерфейса", "Код страницы", "База данных"], "correct": 1},
                        {"text": "Цель юзабилити-тестирования?", "answers": ["Оценить красоту дизайна", "Проверить удобство использования с реальными пользователями", "Проверить код", "Измерить скорость"], "correct": 1},
                        {"text": "Что такое user persona?", "answers": ["Реальный пользователь", "Собирательный образ целевого пользователя", "Аккаунт в системе", "Тест"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Figma: инструмент дизайнера",
                "lessons": ["Интерфейс Figma", "Компоненты и стили", "Прототипирование в Figma", "Auto Layout и адаптивные компоненты"],
                "test": {
                    "title": "Тест: Figma",
                    "questions": [
                        {"text": "Figma — это...", "answers": ["Язык программирования", "Веб-приложение для UI дизайна", "База данных", "CMS система"], "correct": 1},
                        {"text": "Для чего нужны компоненты в Figma?", "answers": ["Повторное использование элементов дизайна", "Написание кода", "Хранение изображений", "Аналитика"], "correct": 0},
                        {"text": "Auto Layout в Figma аналогичен...", "answers": ["CSS Grid", "CSS Flexbox", "CSS Position", "CSS Float"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Дизайн-системы",
                "lessons": ["Что такое дизайн-система", "Типографика и цветовые схемы", "Создание UI Kit", "Handoff разработчикам"],
                "test": {
                    "title": "Тест: Дизайн-системы",
                    "questions": [
                        {"text": "Что входит в дизайн-систему?", "answers": ["Только цвета", "Компоненты, стили, токены и документация", "Только код", "Только иконки"], "correct": 1},
                        {"text": "Что такое design token?", "answers": ["Пароль дизайнера", "Именованное значение дизайна (цвет, отступ и т.д.)", "Инструмент Figma", "Тип файла"], "correct": 1},
                        {"text": "Для чего нужен handoff?", "answers": ["Для хранения файлов", "Передача дизайна разработчикам с CSS параметрами", "Для тестирования", "Для презентации клиенту"], "correct": 1},
                    ]
                }
            },
        ]
    },

    # ── Дополнительные ──
    {
        "title": "GraphQL API",
        "description": "Современный подход к API с GraphQL. Queries, Mutations, Subscriptions, Apollo Server и Client, интеграция с React.",
        "category": "web-dev",
        "price": 8900,
        "modules": [
            {
                "title": "Основы GraphQL",
                "lessons": ["REST vs GraphQL", "Schema и типы", "Queries и Mutations", "Resolvers"],
                "test": {
                    "title": "Тест: GraphQL основы",
                    "questions": [
                        {"text": "Главное преимущество GraphQL перед REST?", "answers": ["Быстрее", "Клиент запрашивает ровно нужные поля", "Проще в реализации", "Безопаснее"], "correct": 1},
                        {"text": "Что такое Schema в GraphQL?", "answers": ["База данных", "Описание типов и операций API", "Конфигурация сервера", "Маршрут"], "correct": 1},
                        {"text": "Mutation в GraphQL используется для...", "answers": ["Чтения данных", "Изменения данных (create/update/delete)", "Подписки", "Аутентификации"], "correct": 1},
                        {"text": "Что такое resolver?", "answers": ["Функция, которая возвращает данные для поля", "Тип данных", "Клиентская библиотека", "Конфигурация"], "correct": 0},
                    ]
                }
            },
        ]
    },
    {
        "title": "Redis: кеширование и очереди",
        "description": "Работа с Redis. Структуры данных, кеширование, сессии, очереди задач с Celery и паттерны использования.",
        "category": "databases",
        "price": 6900,
        "modules": [
            {
                "title": "Основы Redis",
                "lessons": ["Установка и CLI Redis", "Строки, списки, множества", "Хеши и отсортированные множества", "TTL и истечение ключей"],
                "test": {
                    "title": "Тест: Redis",
                    "questions": [
                        {"text": "Redis — это...", "answers": ["Реляционная БД", "In-memory хранилище ключ-значение", "Документная БД", "Графовая БД"], "correct": 1},
                        {"text": "Команда для установки значения в Redis?", "answers": ["INSERT key value", "SET key value", "PUT key value", "ADD key value"], "correct": 1},
                        {"text": "Что такое TTL в Redis?", "answers": ["Тип данных", "Время жизни ключа", "Транзакция", "Тип соединения"], "correct": 1},
                        {"text": "Для чего Redis используется в веб-приложениях?", "answers": ["Только как основная БД", "Кеширование, сессии, очереди задач", "Только для файлов", "Только для логов"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "MongoDB: NoSQL базы данных",
        "description": "Документно-ориентированная БД MongoDB. CRUD операции, агрегации, индексы, схемы с Mongoose и использование в Node.js.",
        "category": "databases",
        "price": 7900,
        "modules": [
            {
                "title": "Основы MongoDB",
                "lessons": ["Документы и коллекции", "CRUD операции", "Операторы запросов", "Агрегационный конвейер"],
                "test": {
                    "title": "Тест: MongoDB",
                    "questions": [
                        {"text": "MongoDB хранит данные в формате...", "answers": ["Таблиц", "BSON документов", "CSV файлов", "XML"], "correct": 1},
                        {"text": "Аналог таблицы в MongoDB?", "answers": ["Document", "Database", "Collection", "Schema"], "correct": 2},
                        {"text": "Команда для вставки документа?", "answers": ["db.insert()", "db.collection.insertOne()", "db.add()", "db.create()"], "correct": 1},
                        {"text": "Что такое $match в агрегации?", "answers": ["Фильтрация документов", "Группировка", "Сортировка", "Проекция"], "correct": 0},
                    ]
                }
            },
        ]
    },
    {
        "title": "Vue.js 3",
        "description": "Прогрессивный JavaScript фреймворк Vue.js 3. Composition API, Vue Router, Pinia (Vuex) и создание полноценных SPA.",
        "category": "web-dev",
        "price": 8900,
        "modules": [
            {
                "title": "Основы Vue.js 3",
                "lessons": ["Установка и первое приложение", "Composition API vs Options API", "Реактивность: ref и reactive", "Computed и Watch"],
                "test": {
                    "title": "Тест: Vue.js 3",
                    "questions": [
                        {"text": "Для объявления реактивного примитива в Vue 3?", "answers": ["reactive()", "ref()", "useState()", "signal()"], "correct": 1},
                        {"text": "v-for используется для...", "answers": ["Условного рендера", "Рендера списков", "Обработки событий", "Привязки данных"], "correct": 1},
                        {"text": "Какой хук жизненного цикла аналогичен componentDidMount?", "answers": ["onBeforeMount", "onMounted", "onUpdated", "onCreated"], "correct": 1},
                        {"text": "Что такое Pinia?", "answers": ["Роутер для Vue", "Менеджер состояния для Vue 3", "UI библиотека", "HTTP клиент"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Next.js: Full-Stack React",
        "description": "Полноценная разработка с Next.js. SSR, SSG, App Router, Server Components, API Routes и деплой на Vercel.",
        "category": "web-dev",
        "price": 10900,
        "modules": [
            {
                "title": "Next.js App Router",
                "lessons": ["Структура App Router", "Server и Client Components", "Data Fetching: fetch и cache", "Loading и Error состояния"],
                "test": {
                    "title": "Тест: Next.js",
                    "questions": [
                        {"text": "Разница SSR и SSG?", "answers": ["SSR генерирует при каждом запросе, SSG — при сборке", "Они одинаковые", "SSG быстрее при каждом запросе", "SSR только для статики"], "correct": 0},
                        {"text": "Что такое Server Component в Next.js 13+?", "answers": ["Компонент только для сервера, без JS на клиенте", "Компонент с useState", "API route", "Middleware"], "correct": 0},
                        {"text": "'use client' директива означает...", "answers": ["Запрос к API", "Компонент рендерится на клиенте", "Серверный компонент", "Middleware"], "correct": 1},
                        {"text": "Для чего нужен файл layout.tsx?", "answers": ["Стили страницы", "Общий макет для группы страниц", "API route", "Конфигурация"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Next.js и базы данных",
                "lessons": ["Prisma ORM с Next.js", "Server Actions", "Аутентификация с NextAuth.js", "Деплой на Vercel"],
                "test": {
                    "title": "Тест: Next.js + DB",
                    "questions": [
                        {"text": "Что такое Server Action в Next.js?", "answers": ["API route", "Функция на сервере, вызываемая напрямую из компонента", "Middleware", "Хук"], "correct": 1},
                        {"text": "Prisma — это...", "answers": ["База данных", "ORM для TypeScript/JavaScript", "UI библиотека", "Роутер"], "correct": 1},
                        {"text": "Для чего NextAuth.js?", "answers": ["Стилизация", "Аутентификация (Google, GitHub, credentials)", "Хранение данных", "Анимации"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Алгоритмы и структуры данных",
        "description": "Фундаментальные алгоритмы и структуры данных. Сортировки, деревья, графы, динамическое программирование и подготовка к техническим интервью.",
        "category": "python",
        "price": 8900,
        "modules": [
            {
                "title": "Базовые алгоритмы",
                "lessons": ["Big O нотация", "Сортировки: bubble, quick, merge", "Бинарный поиск", "Рекурсия и стек вызовов"],
                "test": {
                    "title": "Тест: Алгоритмы",
                    "questions": [
                        {"text": "Сложность бинарного поиска?", "answers": ["O(n)", "O(n²)", "O(log n)", "O(1)"], "correct": 2},
                        {"text": "Худшая сложность сортировки пузырьком?", "answers": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"], "correct": 2},
                        {"text": "Что такое Big O нотация?", "answers": ["Число ошибок", "Описание роста времени/памяти алгоритма", "Тип данных", "Язык программирования"], "correct": 1},
                        {"text": "Рекурсия — это...", "answers": ["Цикл for", "Функция, вызывающая сама себя", "Тип данных", "Алгоритм сортировки"], "correct": 1},
                    ]
                }
            },
            {
                "title": "Структуры данных",
                "lessons": ["Связный список", "Стек и очередь", "Деревья и BST", "Хеш-таблицы"],
                "test": {
                    "title": "Тест: Структуры данных",
                    "questions": [
                        {"text": "Принцип работы стека?", "answers": ["FIFO", "LIFO", "Случайный доступ", "Двусторонний"], "correct": 1},
                        {"text": "BST расшифровывается как...", "answers": ["Binary Search Table", "Binary Search Tree", "Basic Sort Type", "Balanced Sorted Tree"], "correct": 1},
                        {"text": "Сложность поиска в хеш-таблице (в среднем)?", "answers": ["O(n)", "O(log n)", "O(1)", "O(n²)"], "correct": 2},
                        {"text": "Что такое очередь (Queue)?", "answers": ["LIFO структура", "FIFO структура", "Дерево", "Граф"], "correct": 1},
                    ]
                }
            },
        ]
    },
    {
        "title": "Английский для IT",
        "description": "Технический английский для разработчиков. Чтение документации, деловая переписка, техническое интервью и профессиональный словарный запас.",
        "category": "uiux",
        "price": 5900,
        "modules": [
            {
                "title": "Основы технического английского",
                "lessons": ["Чтение README и документации", "IT терминология", "Деловая переписка по email", "Участие в code review"],
                "test": {
                    "title": "Тест: IT English",
                    "questions": [
                        {"text": "Что означает 'deprecated'?", "answers": ["Новая функция", "Устаревшая/нерекомендованная функция", "Ошибка", "Тест"], "correct": 1},
                        {"text": "Перевод: 'the function returns a boolean value'", "answers": ["Функция принимает булево значение", "Функция возвращает булево значение", "Функция создаёт булево значение", "Функция удаляет булево значение"], "correct": 1},
                        {"text": "LGTM в code review означает...", "answers": ["Let's Get To Meeting", "Looks Good To Me", "Let's Get The Merge", "Large General Test Mode"], "correct": 1},
                        {"text": "Что значит 'merge conflict'?", "answers": ["Слияние завершено", "Конфликт при слиянии изменений", "Удаление ветки", "Создание PR"], "correct": 1},
                    ]
                }
            },
        ]
    },
]


class Command(BaseCommand):
    help = "Seed database with 35 demo courses including modules, lessons, and tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--teacher",
            type=str,
            default="teacher@edu.kz",
            help="Email of teacher user to assign courses to",
        )
        parser.add_argument(
            "--password",
            type=str,
            default="Teacher123!",
            help="Password for the teacher user (if creating new)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing seeded data before creating new",
        )

    def handle(self, *args, **options):
        teacher_email = options["teacher"]
        teacher_password = options["password"]

        if options["clear"]:
            self.stdout.write("Clearing existing courses...")
            Course.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared all courses and categories."))

        # Get or create teacher
        teacher, created = User.objects.get_or_create(
            email=teacher_email,
            defaults={
                "name": "Айгерим Сейткали",
                "role": "teacher",
                "is_active": True,
            },
        )
        if created:
            teacher.set_password(teacher_password)
            teacher.save()
            self.stdout.write(self.style.SUCCESS(f"Created teacher: {teacher_email} / {teacher_password}"))
        else:
            if teacher.role != "teacher":
                teacher.role = "teacher"
                teacher.save()
            self.stdout.write(f"Using existing teacher: {teacher_email}")

        # Create categories
        categories = {}
        for cat_data in CATEGORIES:
            cat, _ = Category.objects.get_or_create(
                slug=cat_data["slug"],
                defaults={"name": cat_data["name"]},
            )
            categories[cat_data["slug"]] = cat
            self.stdout.write(f"  Category: {cat.name}")

        # Create courses
        total_courses = 0
        total_modules = 0
        total_lessons = 0
        total_tests = 0
        total_questions = 0

        for course_data in COURSES_DATA:
            # Check if course already exists
            if Course.objects.filter(title=course_data["title"], teacher=teacher).exists():
                self.stdout.write(f"  Skipping existing: {course_data['title']}")
                continue

            course = Course.objects.create(
                title=course_data["title"],
                description=course_data["description"],
                teacher=teacher,
                category=categories.get(course_data["category"]),
                price=course_data["price"],
                image=COURSE_IMAGES.get(course_data["title"], ""),
                is_published=True,
                enable_certificate=True,
                certificate_title=f"Сертификат о прохождении курса «{course_data['title']}»",
            )
            total_courses += 1

            for module_idx, module_data in enumerate(course_data["modules"]):
                module = Module.objects.create(
                    course=course,
                    title=module_data["title"],
                    order=module_idx + 1,
                    is_published=True,
                )
                total_modules += 1

                for lesson_idx, lesson_title in enumerate(module_data["lessons"]):
                    Lesson.objects.create(
                        module=module,
                        title=lesson_title,
                        description=f"Подробное изучение темы: {lesson_title}. Теория, примеры и практические задания.",
                        video_url=get_video_url(lesson_title),
                        order=lesson_idx + 1,
                        duration_minutes=random.randint(10, 45),
                        is_published=True,
                    )
                    total_lessons += 1

                # Create test for the module
                test_data = module_data.get("test")
                if test_data:
                    test = Test.objects.create(
                        module=module,
                        title=test_data["title"],
                        description=f"Проверьте свои знания по теме «{module_data['title']}»",
                        passing_score=70,
                        time_limit_minutes=20,
                        attempts_allowed=3,
                        is_published=True,
                    )
                    total_tests += 1

                    for q_idx, q_data in enumerate(test_data["questions"]):
                        question = Question.objects.create(
                            test=test,
                            text=q_data["text"],
                            question_type="single",
                            order=q_idx + 1,
                            points=1,
                        )
                        total_questions += 1

                        for a_idx, answer_text in enumerate(q_data["answers"]):
                            Answer.objects.create(
                                question=question,
                                text=answer_text,
                                is_correct=(a_idx == q_data["correct"]),
                                order=a_idx + 1,
                            )

            self.stdout.write(
                f"  [OK] [{total_courses:02d}] {course.title} "
                f"({len(course_data['modules'])} moduley)"
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
        self.stdout.write(f"  Courses created : {total_courses}")
        self.stdout.write(f"  Modules created : {total_modules}")
        self.stdout.write(f"  Lessons created : {total_lessons}")
        self.stdout.write(f"  Tests created   : {total_tests}")
        self.stdout.write(f"  Questions created: {total_questions}")
        self.stdout.write(self.style.SUCCESS("=" * 50))
        self.stdout.write(f"  Teacher login: {teacher_email}")
        self.stdout.write(f"  Teacher pass : {teacher_password}")
