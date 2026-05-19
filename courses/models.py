import uuid
from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Course(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Преподаватель',
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='courses', verbose_name='Категория',
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Цена (тенге)')
    image = models.ImageField(upload_to='courses/', null=True, blank=True, verbose_name='Обложка')
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    certificate_title = models.CharField(
        max_length=500, blank=True,
        help_text='Например: "Успешно завершил курс по Python"',
        verbose_name='Текст сертификата',
    )
    enable_certificate = models.BooleanField(default=False, verbose_name='Выдавать сертификат')
    category_name = models.CharField(
        max_length=200, null=True, blank=True,
        help_text='Используется когда учитель выбирает "Другое" и пишет свою категорию',
        verbose_name='Название категории (кастомное)',
    )

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def students_count(self):
        return self.enrollments.count()

    @property
    def teacher_name(self):
        return self.teacher.name

    @property
    def rating(self):
        avg = self.reviews.aggregate(r=models.Avg('rating'))['r']
        return round(avg, 1) if avg else None


class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Студент',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Курс')
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')

    class Meta:
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'
        unique_together = [('student', 'course')]

    def __str__(self):
        return f'{self.student.email} — {self.course.title}'


class Review(models.Model):
    RATING_CHOICES = [(i, i) for i in range(1, 6)]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Студент',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews', verbose_name='Курс')
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name='Оценка')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = [('course', 'student')]

    def __str__(self):
        return f'{self.student.email} — {self.course.title} ({self.rating})'


class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name='Курс')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Модуль'
        verbose_name_plural = 'Модули'
        ordering = ['order']

    def __str__(self):
        return f'{self.course.title} — {self.title}'

    @property
    def lessons_count(self):
        return self.lessons.count()

    @property
    def has_test(self):
        return hasattr(self, 'test')


class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name='Модуль')
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    video_url = models.URLField(blank=True, verbose_name='Ссылка на видео')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name='Длительность (мин)')
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ['order']

    def __str__(self):
        return f'{self.module.title} — {self.title}'

    @property
    def materials_count(self):
        return self.materials.count()


class LessonMaterial(models.Model):
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF документ'),
        ('doc', 'Word документ'),
        ('image', 'Изображение'),
        ('other', 'Другое'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='materials', verbose_name='Урок')
    title = models.CharField(max_length=200, verbose_name='Название')
    file = models.FileField(upload_to='materials/', verbose_name='Файл')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other', verbose_name='Тип файла')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Материал урока'
        verbose_name_plural = 'Материалы уроков'

    def __str__(self):
        return f'{self.lesson.title} — {self.title}'


class Test(models.Model):
    module = models.OneToOneField(Module, on_delete=models.CASCADE, related_name='test', verbose_name='Модуль')
    title = models.CharField(max_length=200, verbose_name='Название теста')
    description = models.TextField(blank=True, verbose_name='Описание')
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text='Минимальный процент правильных ответов для прохождения',
        verbose_name='Проходной балл (%)',
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=0,
        help_text='0 = без ограничения времени',
        verbose_name='Лимит времени (мин)',
    )
    attempts_allowed = models.PositiveIntegerField(
        default=0,
        help_text='0 = неограниченно',
        verbose_name='Количество попыток',
    )
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return f'Тест: {self.title}'

    @property
    def questions_count(self):
        return self.questions.count()


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('single', 'Один правильный ответ'),
        ('multiple', 'Несколько правильных ответов'),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', verbose_name='Тест')
    text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(
        max_length=20, choices=QUESTION_TYPE_CHOICES, default='single', verbose_name='Тип вопроса',
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    points = models.PositiveIntegerField(default=1, verbose_name='Баллы')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order']

    def __str__(self):
        return f'{self.test.title} — {self.text[:50]}'


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers', verbose_name='Вопрос')
    text = models.CharField(max_length=500, verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['order']

    def __str__(self):
        return f'{self.question.text[:30]} — {self.text}'


class TestAttempt(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts', verbose_name='Тест')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name='Студент',
    )
    score = models.PositiveIntegerField(default=0, verbose_name='Набранный балл (%)')
    is_passed = models.BooleanField(default=False, verbose_name='Сдан')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Начат')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершён')

    class Meta:
        verbose_name = 'Попытка теста'
        verbose_name_plural = 'Попытки тестов'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.student.email} — {self.test.title} ({self.score}%)'


class TestAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='answers', verbose_name='Попытка')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='student_answers', verbose_name='Вопрос')
    selected_answers = models.ManyToManyField(Answer, related_name='selections', verbose_name='Выбранные ответы')
    is_correct = models.BooleanField(default=False, verbose_name='Правильно')

    class Meta:
        verbose_name = 'Ответ студента'
        verbose_name_plural = 'Ответы студентов'
        unique_together = [('attempt', 'question')]

    def __str__(self):
        return f'{self.attempt} — {self.question.text[:30]}'


class Certificate(models.Model):
    certificate_number = models.CharField(max_length=50, unique=True, verbose_name='Номер сертификата')
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Студент',
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='certificates', verbose_name='Курс',
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')
    pdf_file = models.FileField(upload_to='certificates/', null=True, blank=True, verbose_name='PDF файл')

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        unique_together = [('student', 'course')]

    def __str__(self):
        return f'{self.certificate_number} — {self.student.email}'

    @staticmethod
    def generate_number():
        return str(uuid.uuid4()).replace('-', '').upper()[:16]


class LessonProgress(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='Студент',
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress', verbose_name='Урок')
    is_completed = models.BooleanField(default=False, verbose_name='Завершён')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')
    watch_time_seconds = models.PositiveIntegerField(default=0, verbose_name='Время просмотра (сек)')

    class Meta:
        verbose_name = 'Прогресс по уроку'
        verbose_name_plural = 'Прогресс по урокам'
        unique_together = [('student', 'lesson')]

    def __str__(self):
        return f'{self.student.email} — {self.lesson.title}'


class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачен'),
        ('failed', 'Отклонён'),
    ]

    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Студент',
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments', verbose_name='Курс')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.id} — {self.student.email} — {self.status}'
