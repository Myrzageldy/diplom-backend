from rest_framework import serializers
from .models import (
    Category, Course, Module, Lesson, LessonMaterial, Enrollment,
    LessonProgress, Test, Question, Answer, TestAttempt, TestAnswer,
    Certificate, Payment, Review,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


# ── Answers ──────────────────────────────────────────────────────────────────

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct', 'order']


class AnswerPublicSerializer(serializers.ModelSerializer):
    """Without is_correct — for students during a test."""
    class Meta:
        model = Answer
        fields = ['id', 'text', 'order']


# ── Questions ─────────────────────────────────────────────────────────────────

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'points', 'answers']


class QuestionCreateSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'points', 'answers']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers', [])
        question = Question.objects.create(**validated_data)
        for ans in answers_data:
            Answer.objects.create(question=question, **ans)
        return question

    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if answers_data is not None:
            instance.answers.all().delete()
            for ans in answers_data:
                Answer.objects.create(question=instance, **ans)
        return instance


class QuestionPublicSerializer(serializers.ModelSerializer):
    answers = AnswerPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'order', 'points', 'answers']


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestSerializer(serializers.ModelSerializer):
    questions_count = serializers.ReadOnlyField()
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'passing_score', 'time_limit_minutes',
            'attempts_allowed', 'is_published', 'questions_count', 'questions', 'created_at',
        ]


class TestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['title', 'description', 'passing_score', 'time_limit_minutes', 'attempts_allowed', 'is_published']


class TestStudentSerializer(serializers.ModelSerializer):
    """Test for student — questions without correct answer flags."""
    questions_count = serializers.ReadOnlyField()
    questions = QuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = [
            'id', 'title', 'description', 'passing_score', 'time_limit_minutes',
            'attempts_allowed', 'questions_count', 'questions',
        ]


# ── LessonMaterial ────────────────────────────────────────────────────────────

class LessonMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonMaterial
        fields = ['id', 'title', 'file', 'file_type', 'uploaded_at']


# ── Lessons ───────────────────────────────────────────────────────────────────

class LessonSerializer(serializers.ModelSerializer):
    materials_count = serializers.ReadOnlyField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video_url', 'order',
            'duration_minutes', 'is_published', 'materials_count', 'created_at',
        ]


class LessonCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['title', 'description', 'video_url', 'order', 'duration_minutes', 'is_published']


class LessonDetailSerializer(serializers.ModelSerializer):
    materials_count = serializers.ReadOnlyField()
    materials = LessonMaterialSerializer(many=True, read_only=True)
    module_title = serializers.SerializerMethodField()
    course_id = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'description', 'video_url', 'order',
            'duration_minutes', 'is_published', 'materials_count', 'materials',
            'module_title', 'course_id', 'created_at',
        ]

    def get_module_title(self, obj):
        return obj.module.title

    def get_course_id(self, obj):
        return obj.module.course_id


# ── Modules ───────────────────────────────────────────────────────────────────

class ModuleSerializer(serializers.ModelSerializer):
    lessons_count = serializers.ReadOnlyField()
    has_test = serializers.ReadOnlyField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'is_published', 'lessons_count', 'has_test', 'created_at']


class ModuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['title', 'description', 'order', 'is_published']


class ModuleDetailSerializer(serializers.ModelSerializer):
    lessons_count = serializers.ReadOnlyField()
    has_test = serializers.ReadOnlyField()
    lessons = LessonDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'order', 'is_published',
            'lessons_count', 'has_test', 'lessons', 'created_at',
        ]


# ── Courses ───────────────────────────────────────────────────────────────────

class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField()
    students_count = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'teacher_name', 'category_name', 'students_count', 'rating',
            'is_published', 'created_at',
        ]


class TeacherCourseSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField()
    students_count = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'teacher_name', 'category_name', 'students_count', 'rating',
            'is_published', 'enable_certificate', 'certificate_title', 'created_at',
        ]


class CourseDetailSerializer(serializers.ModelSerializer):
    teacher_name = serializers.ReadOnlyField()
    students_count = serializers.ReadOnlyField()
    rating = serializers.ReadOnlyField()
    modules_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'image',
            'teacher_name', 'category_name', 'students_count', 'rating',
            'is_published', 'enable_certificate', 'modules_count', 'created_at',
        ]

    def get_modules_count(self, obj):
        return obj.modules.count()


class CourseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'title', 'description', 'price', 'category', 'category_name',
            'is_published', 'enable_certificate', 'certificate_title',
        ]


# ── Enrollments ───────────────────────────────────────────────────────────────

class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = ['id', 'course', 'enrolled_at']


# ── Progress ──────────────────────────────────────────────────────────────────

class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ['id', 'lesson', 'is_completed', 'completed_at', 'watch_time_seconds']


class CourseProgressSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    progress_percent = serializers.FloatField()
    modules = serializers.ListField()


# ── Test Attempts ─────────────────────────────────────────────────────────────

class TestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswer
        fields = ['id', 'question', 'selected_answers', 'is_correct']


class TestAttemptSerializer(serializers.ModelSerializer):
    test_title = serializers.SerializerMethodField()

    class Meta:
        model = TestAttempt
        fields = ['id', 'test', 'test_title', 'score', 'is_passed', 'started_at', 'finished_at']

    def get_test_title(self, obj):
        return obj.test.title


# ── Certificates ──────────────────────────────────────────────────────────────

class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ['id', 'certificate_number', 'student_name', 'course_title', 'issued_at', 'pdf_file']

    def get_student_name(self, obj):
        return obj.student.name

    def get_course_title(self, obj):
        return obj.course.title


class CertificateVerifySerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.SerializerMethodField()
    teacher_name = serializers.SerializerMethodField()

    class Meta:
        model = Certificate
        fields = ['certificate_number', 'student_name', 'course_title', 'teacher_name', 'issued_at']

    def get_student_name(self, obj):
        return obj.student.name

    def get_course_title(self, obj):
        return obj.course.title

    def get_teacher_name(self, obj):
        return obj.course.teacher.name
