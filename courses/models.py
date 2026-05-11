from django.db import models
from django.utils import timezone
from users.models import User
import uuid


class Category(models.Model):
    """Категория курсов"""
    name = models.CharField(max_length=100, verbose_name='Название')
    slug = models.SlugField(unique=True, verbose_name='Слаг')

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Course(models.Model):
    """Курс"""
    title = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name='Преподаватель'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name='Категория'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Цена (тенге)'
    )
    image = models.ImageField(
        upload_to='courses/',
        blank=True,
        null=True,
        verbose_name='Обложка'
    )
    category_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name='Название категории (кастомное)',
        help_text='Используется когда учитель выбирает "Другое" и пишет свою категорию'
    )
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    # Настройки сертификата
    enable_certificate = models.BooleanField(default=False, verbose_name='Выдавать сертификат')
    certificate_title = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Текст сертификата',
        help_text='Например: "Успешно завершил курс по Python"'
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
    def rating(self):
        reviews = self.reviews.all()
        if reviews:
            return round(sum(r.rating for r in reviews) / len(reviews), 1)
        return 0


class Payment(models.Model):
    """Платёж за курс"""
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Ожидает оплаты'),
        (STATUS_PAID, 'Оплачен'),
        (STATUS_FAILED, 'Отклонён'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Курс'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student.name} — {self.course.title} — {self.status}'


class Enrollment(models.Model):
    """Запись на курс"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Курс'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата записи')

    class Meta:
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'
        unique_together = ['student', 'course']

    def __str__(self):
        return f'{self.student.name} - {self.course.title}'


class Review(models.Model):
    """Отзыв о курсе"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Курс'
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Студент'
    )
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        verbose_name='Оценка'
    )
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        unique_together = ['course', 'student']

    def __str__(self):
        return f'{self.student.name} - {self.course.title} ({self.rating})'


# ============================================================
# МОДУЛИ И УРОКИ
# ============================================================

class Module(models.Model):
    """Модуль курса"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='modules',
        verbose_name='Курс'
    )
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
        return f'{self.course.title} - {self.title}'

    @property
    def lessons_count(self):
        return self.lessons.count()


class Lesson(models.Model):
    """Урок"""
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Модуль'
    )
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
        return f'{self.module.title} - {self.title}'


class LessonMaterial(models.Model):
    """Материал урока (PDF, документы и т.д.)"""
    MATERIAL_TYPES = [
        ('pdf', 'PDF документ'),
        ('doc', 'Word документ'),
        ('image', 'Изображение'),
        ('other', 'Другое'),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Урок'
    )
    title = models.CharField(max_length=200, verbose_name='Название')
    file = models.FileField(upload_to='materials/', verbose_name='Файл')
    file_type = models.CharField(
        max_length=20,
        choices=MATERIAL_TYPES,
        default='other',
        verbose_name='Тип файла'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')

    class Meta:
        verbose_name = 'Материал урока'
        verbose_name_plural = 'Материалы уроков'

    def __str__(self):
        return f'{self.lesson.title} - {self.title}'


# ============================================================
# ТЕСТЫ
# ============================================================

class Test(models.Model):
    """Тест для модуля"""
    module = models.OneToOneField(
        Module,
        on_delete=models.CASCADE,
        related_name='test',
        verbose_name='Модуль'
    )
    title = models.CharField(max_length=200, verbose_name='Название теста')
    description = models.TextField(blank=True, verbose_name='Описание')
    passing_score = models.PositiveIntegerField(
        default=70,
        verbose_name='Проходной балл (%)',
        help_text='Минимальный процент правильных ответов для прохождения'
    )
    time_limit_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name='Лимит времени (мин)',
        help_text='0 = без ограничения времени'
    )
    attempts_allowed = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество попыток',
        help_text='0 = неограниченно'
    )
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return f'{self.module.title} - {self.title}'

    @property
    def questions_count(self):
        return self.questions.count()


class Question(models.Model):
    """Вопрос теста"""
    QUESTION_TYPES = [
        ('single', 'Один правильный ответ'),
        ('multiple', 'Несколько правильных ответов'),
    ]

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Тест'
    )
    text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        default='single',
        verbose_name='Тип вопроса'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    points = models.PositiveIntegerField(default=1, verbose_name='Баллы')

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering = ['order']

    def __str__(self):
        return f'{self.test.title} - Вопрос {self.order}'


class Answer(models.Model):
    """Вариант ответа"""
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Вопрос'
    )
    text = models.CharField(max_length=500, verbose_name='Текст ответа')
    is_correct = models.BooleanField(default=False, verbose_name='Правильный ответ')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Вариант ответа'
        verbose_name_plural = 'Варианты ответов'
        ordering = ['order']

    def __str__(self):
        return f'{self.text[:50]}...' if len(self.text) > 50 else self.text


# ============================================================
# ПРОГРЕСС СТУДЕНТА
# ============================================================

class LessonProgress(models.Model):
    """Прогресс студента по уроку"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        verbose_name='Студент'
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name='Урок'
    )
    is_completed = models.BooleanField(default=False, verbose_name='Завершён')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата завершения')
    watch_time_seconds = models.PositiveIntegerField(default=0, verbose_name='Время просмотра (сек)')

    class Meta:
        verbose_name = 'Прогресс по уроку'
        verbose_name_plural = 'Прогресс по урокам'
        unique_together = ['student', 'lesson']

    def __str__(self):
        status = '✓' if self.is_completed else '○'
        return f'{status} {self.student.name} - {self.lesson.title}'

    def mark_completed(self):
        if not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
            self.save()


class TestAttempt(models.Model):
    """Попытка прохождения теста"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name='Студент'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Тест'
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
        status = '✓' if self.is_passed else '✗'
        return f'{status} {self.student.name} - {self.test.title} ({self.score}%)'

    def calculate_score(self):
        """Подсчитать результат теста"""
        answers = self.answers.all()
        if not answers:
            return 0

        total_points = sum(a.question.points for a in answers)
        earned_points = sum(a.question.points for a in answers if a.is_correct)

        if total_points == 0:
            return 0

        self.score = round((earned_points / total_points) * 100)
        self.is_passed = self.score >= self.test.passing_score
        self.finished_at = timezone.now()
        self.save()
        return self.score


class TestAnswer(models.Model):
    """Ответ студента на вопрос теста"""
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Попытка'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='student_answers',
        verbose_name='Вопрос'
    )
    selected_answers = models.ManyToManyField(
        Answer,
        related_name='selections',
        verbose_name='Выбранные ответы'
    )
    is_correct = models.BooleanField(default=False, verbose_name='Правильно')

    class Meta:
        verbose_name = 'Ответ студента'
        verbose_name_plural = 'Ответы студентов'
        unique_together = ['attempt', 'question']

    def __str__(self):
        status = '✓' if self.is_correct else '✗'
        return f'{status} {self.attempt.student.name} - Вопрос {self.question.order}'

    def check_answer(self):
        """Проверить правильность ответа"""
        correct_answers = set(self.question.answers.filter(is_correct=True).values_list('id', flat=True))
        selected = set(self.selected_answers.values_list('id', flat=True))
        self.is_correct = correct_answers == selected
        self.save()
        return self.is_correct


# ============================================================
# СЕРТИФИКАТЫ
# ============================================================

class Certificate(models.Model):
    """Сертификат о прохождении курса"""
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Студент'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='certificates',
        verbose_name='Курс'
    )
    certificate_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Номер сертификата'
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата выдачи')
    pdf_file = models.FileField(
        upload_to='certificates/',
        blank=True,
        null=True,
        verbose_name='PDF файл'
    )

    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'
        unique_together = ['student', 'course']

    def __str__(self):
        return f'{self.certificate_number} - {self.student.name}'

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            # Генерируем уникальный номер: EP-2026-XXXXXXXX
            self.certificate_number = f'EP-{timezone.now().year}-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)
