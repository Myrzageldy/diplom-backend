from rest_framework import serializers
from .models import (
    Course, Category, Enrollment, Review,
    Module, Lesson, LessonMaterial,
    Test, Question, Answer,
    LessonProgress, TestAttempt, TestAnswer,
    Certificate
)
from users.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


# ============================================================
# КУРСЫ
# ============================================================

class CourseListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка курсов"""
    teacher_name = serializers.CharField(source='teacher.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    students_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'teacher_name', 'category_name', 'students_count', 'rating',
            'is_published', 'created_at'
        ]

    def get_students_count(self, obj):
        return obj.students_count  # Uses @property

    def get_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None


class CourseDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детальной информации о курсе"""
    teacher = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    students_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    modules_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'teacher', 'category', 'students_count', 'rating',
            'is_published', 'enable_certificate', 'modules_count',
            'created_at', 'updated_at'
        ]

    def get_students_count(self, obj):
        return obj.students_count

    def get_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None

    def get_modules_count(self, obj):
        return obj.modules.filter(is_published=True).count()


class TeacherCourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курсов преподавателя"""
    students_count = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    modules_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'is_published', 'students_count', 'rating', 'modules_count',
            'enable_certificate', 'created_at'
        ]

    def get_students_count(self, obj):
        return obj.students_count

    def get_rating(self, obj):
        from django.db.models import Avg
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None

    def get_modules_count(self, obj):
        return obj.modules.count()


class CourseCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования курса"""
    category_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'category_id', 'is_published', 'enable_certificate', 'certificate_title'
        ]

    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        course = Course.objects.create(**validated_data)
        if category_id:
            course.category_id = category_id
            course.save()
        return course

    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if category_id is not None:
            instance.category_id = category_id
        instance.save()
        return instance


class EnrollmentSerializer(serializers.ModelSerializer):
    """Сериализатор для записи на курс"""
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'enrolled_at']


# ============================================================
# МОДУЛИ
# ============================================================

class ModuleSerializer(serializers.ModelSerializer):
    """Сериализатор для модулей"""
    lessons_count = serializers.SerializerMethodField()
    has_test = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order',
            'is_published', 'lessons_count', 'has_test', 'created_at'
        ]

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_has_test(self, obj):
        return hasattr(obj, 'test')


class ModuleCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования модуля"""
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'is_published']


class ModuleDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор модуля с уроками"""
    lessons_count = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()
    has_test = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order',
            'is_published', 'lessons_count', 'lessons', 'has_test', 'created_at'
        ]

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_lessons(self, obj):
        lessons = obj.lessons.all().order_by('order')
        return LessonSerializer(lessons, many=True).data

    def get_has_test(self, obj):
        return hasattr(obj, 'test')


# ============================================================
# УРОКИ
# ============================================================

class LessonMaterialSerializer(serializers.ModelSerializer):
    """Сериализатор для материалов урока"""
    class Meta:
        model = LessonMaterial
        fields = ['id', 'title', 'file', 'file_type', 'uploaded_at']


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для уроков"""
    materials_count = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video_url', 'order',
            'duration_minutes', 'is_published', 'materials_count', 'created_at'
        ]

    def get_materials_count(self, obj):
        return obj.materials.count()


class LessonCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования урока"""
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video_url', 'order',
            'duration_minutes', 'is_published'
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    """Детальный сериализатор урока с материалами"""
    materials = LessonMaterialSerializer(many=True, read_only=True)
    module_title = serializers.CharField(source='module.title', read_only=True)
    course_id = serializers.IntegerField(source='module.course.id', read_only=True)

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video_url', 'order',
            'duration_minutes', 'is_published', 'materials',
            'module_title', 'course_id', 'created_at'
        ]


# ============================================================
# ТЕСТЫ
# ============================================================

class AnswerSerializer(serializers.ModelSerializer):
    """Сериализатор для вариантов ответа"""
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct', 'order']


class AnswerStudentSerializer(serializers.ModelSerializer):
    """Сериализатор для студента (без правильного ответа)"""
    class Meta:
        model = Answer
        fields = ['id', 'text', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    """Сериализатор для вопросов (для учителя)"""
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'points', 'answers']


class QuestionStudentSerializer(serializers.ModelSerializer):
    """Сериализатор вопросов для студента (без правильных ответов)"""
    answers = AnswerStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'points', 'answers']


class QuestionCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания вопроса"""
    answers = AnswerSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'points', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if answers_data is not None:
            # Удаляем старые ответы и создаём новые
            instance.answers.all().delete()
            for answer_data in answers_data:
                Answer.objects.create(question=instance, **answer_data)

        return instance


class TestSerializer(serializers.ModelSerializer):
    """Сериализатор для теста (для учителя)"""
    questions_count = serializers.IntegerField(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'passing_score',
            'time_limit_minutes', 'attempts_allowed', 'is_published',
            'questions_count', 'questions', 'created_at'
        ]


class TestCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/редактирования теста"""
    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'passing_score',
            'time_limit_minutes', 'attempts_allowed', 'is_published'
        ]


class TestStudentSerializer(serializers.ModelSerializer):
    """Сериализатор теста для студента"""
    questions_count = serializers.IntegerField(read_only=True)
    questions = QuestionStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'passing_score',
            'time_limit_minutes', 'attempts_allowed',
            'questions_count', 'questions'
        ]


# ============================================================
# ПРОГРЕСС
# ============================================================

class LessonProgressSerializer(serializers.ModelSerializer):
    """Сериализатор прогресса по уроку"""
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'lesson_title', 'is_completed', 'completed_at', 'watch_time_seconds']
        read_only_fields = ['completed_at']


class TestAttemptSerializer(serializers.ModelSerializer):
    """Сериализатор попытки теста"""
    test_title = serializers.CharField(source='test.title', read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            'id', 'test', 'test_title', 'score', 'is_passed',
            'started_at', 'finished_at'
        ]


class TestAnswerSerializer(serializers.ModelSerializer):
    """Сериализатор ответа студента"""
    class Meta:
        model = TestAnswer
        fields = ['id', 'question', 'selected_answers', 'is_correct']


class CourseProgressSerializer(serializers.Serializer):
    """Сериализатор общего прогресса по курсу"""
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    progress_percent = serializers.IntegerField()
    modules = serializers.ListField()


# ============================================================
# СЕРТИФИКАТЫ
# ============================================================

class CertificateSerializer(serializers.ModelSerializer):
    """Сериализатор сертификата"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'id', 'certificate_number', 'student_name', 'course_title',
            'issued_at', 'pdf_file'
        ]


class CertificateVerifySerializer(serializers.ModelSerializer):
    """Сериализатор для публичной проверки сертификата"""
    student_name = serializers.CharField(source='student.name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    teacher_name = serializers.CharField(source='course.teacher.name', read_only=True)

    class Meta:
        model = Certificate
        fields = [
            'certificate_number', 'student_name', 'course_title',
            'teacher_name', 'issued_at'
        ]
