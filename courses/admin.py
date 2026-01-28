from django.contrib import admin
from .models import (
    Category, Course, Enrollment, Review,
    Module, Lesson, LessonMaterial,
    Test, Question, Answer,
    LessonProgress, TestAttempt, TestAnswer,
    Certificate
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


# ============================================================
# КУРСЫ
# ============================================================

class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    fields = ['title', 'order', 'is_published']
    ordering = ['order']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'category', 'price', 'is_published', 'enable_certificate', 'created_at']
    list_filter = ['is_published', 'enable_certificate', 'category', 'created_at']
    search_fields = ['title', 'description', 'teacher__name']
    list_editable = ['is_published']
    raw_id_fields = ['teacher']
    inlines = [ModuleInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'teacher', 'category', 'price', 'image')
        }),
        ('Публикация', {
            'fields': ('is_published',)
        }),
        ('Сертификат', {
            'fields': ('enable_certificate', 'certificate_title'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrolled_at']
    list_filter = ['enrolled_at']
    raw_id_fields = ['student', 'course']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'student', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    raw_id_fields = ['student', 'course']


# ============================================================
# МОДУЛИ И УРОКИ
# ============================================================

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ['title', 'order', 'duration_minutes', 'is_published']
    ordering = ['order']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'lessons_count', 'is_published']
    list_filter = ['is_published', 'course']
    search_fields = ['title', 'course__title']
    list_editable = ['order', 'is_published']
    raw_id_fields = ['course']
    inlines = [LessonInline]

    def lessons_count(self, obj):
        return obj.lessons.count()
    lessons_count.short_description = 'Уроков'


class LessonMaterialInline(admin.TabularInline):
    model = LessonMaterial
    extra = 0
    fields = ['title', 'file', 'file_type']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'order', 'duration_minutes', 'is_published']
    list_filter = ['is_published', 'module__course']
    search_fields = ['title', 'module__title', 'module__course__title']
    list_editable = ['order', 'is_published']
    raw_id_fields = ['module']
    inlines = [LessonMaterialInline]


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'file_type', 'uploaded_at']
    list_filter = ['file_type', 'uploaded_at']
    search_fields = ['title', 'lesson__title']
    raw_id_fields = ['lesson']


# ============================================================
# ТЕСТЫ
# ============================================================

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ['text', 'is_correct', 'order']


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['text', 'question_type', 'order', 'points']
    ordering = ['order']


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'passing_score', 'questions_count', 'is_published']
    list_filter = ['is_published', 'module__course']
    search_fields = ['title', 'module__title']
    list_editable = ['is_published']
    raw_id_fields = ['module']
    inlines = [QuestionInline]

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Вопросов'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text_short', 'test', 'question_type', 'order', 'points']
    list_filter = ['question_type', 'test__module__course']
    search_fields = ['text', 'test__title']
    list_editable = ['order', 'points']
    raw_id_fields = ['test']
    inlines = [AnswerInline]

    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Вопрос'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text_short', 'question', 'is_correct', 'order']
    list_filter = ['is_correct']
    search_fields = ['text', 'question__text']
    list_editable = ['is_correct', 'order']
    raw_id_fields = ['question']

    def text_short(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_short.short_description = 'Ответ'


# ============================================================
# ПРОГРЕСС
# ============================================================

@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'is_completed', 'completed_at']
    list_filter = ['is_completed', 'completed_at']
    search_fields = ['student__name', 'lesson__title']
    raw_id_fields = ['student', 'lesson']


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'test', 'score', 'is_passed', 'started_at', 'finished_at']
    list_filter = ['is_passed', 'started_at']
    search_fields = ['student__name', 'test__title']
    raw_id_fields = ['student', 'test']


@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'is_correct']
    list_filter = ['is_correct']
    raw_id_fields = ['attempt', 'question']


# ============================================================
# СЕРТИФИКАТЫ
# ============================================================

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'student', 'course', 'issued_at']
    list_filter = ['issued_at', 'course']
    search_fields = ['certificate_number', 'student__name', 'course__title']
    raw_id_fields = ['student', 'course']
    readonly_fields = ['certificate_number', 'issued_at']
