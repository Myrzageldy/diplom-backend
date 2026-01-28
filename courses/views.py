from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404

from .models import (
    Course, Category, Enrollment, Review,
    Module, Lesson, LessonMaterial,
    Test, Question, Answer,
    LessonProgress, TestAttempt, TestAnswer,
    Certificate
)
from .serializers import (
    CourseListSerializer, CourseDetailSerializer,
    CategorySerializer, TeacherCourseSerializer, EnrollmentSerializer,
    CourseCreateSerializer,
    ModuleSerializer, ModuleCreateSerializer, ModuleDetailSerializer,
    LessonSerializer, LessonCreateSerializer, LessonDetailSerializer,
    LessonMaterialSerializer,
    TestSerializer, TestCreateSerializer, TestStudentSerializer,
    QuestionSerializer, QuestionCreateSerializer,
    AnswerSerializer,
    LessonProgressSerializer, TestAttemptSerializer, TestAnswerSerializer,
    CourseProgressSerializer,
    CertificateSerializer, CertificateVerifySerializer
)


# ============================================================
# КУРСЫ - ПУБЛИЧНЫЕ
# ============================================================

class CourseListView(APIView):
    """
    GET /api/courses/
    Список всех опубликованных курсов.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        courses = Course.objects.filter(is_published=True)

        # Поиск
        search = request.query_params.get('search', '')
        if search:
            courses = courses.filter(title__icontains=search) | \
                      courses.filter(description__icontains=search)

        # Фильтр по категории
        category = request.query_params.get('category', '')
        if category:
            courses = courses.filter(category__slug=category)

        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)


class CourseDetailView(APIView):
    """
    GET /api/courses/<id>/
    Детальная информация о курсе.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CourseDetailSerializer(course)
        data = serializer.data

        # Добавляем модули (публичные)
        modules = course.modules.filter(is_published=True).order_by('order')
        data['modules'] = ModuleSerializer(modules, many=True).data

        # Проверяем записан ли пользователь
        if request.user.is_authenticated:
            data['is_enrolled'] = Enrollment.objects.filter(
                student=request.user, course=course
            ).exists()
        else:
            data['is_enrolled'] = False

        return Response(data)


class CategoryListView(APIView):
    """
    GET /api/courses/categories/
    Список всех категорий.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


# ============================================================
# КУРСЫ - УЧИТЕЛЬ
# ============================================================

class TeacherCoursesView(APIView):
    """
    GET /api/courses/my/
    POST /api/courses/my/
    Курсы текущего преподавателя.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        if request.user.role != 'teacher':
            return Response(
                {'detail': 'Только для преподавателей'},
                status=status.HTTP_403_FORBIDDEN
            )

        courses = Course.objects.filter(teacher=request.user)

        serializer = TeacherCourseSerializer(courses, many=True)
        return Response({
            'courses': serializer.data,
            'total': courses.count(),
            'published': courses.filter(is_published=True).count(),
            'drafts': courses.filter(is_published=False).count(),
        })

    def post(self, request):
        """Создать новый курс"""
        if request.user.role != 'teacher':
            return Response(
                {'detail': 'Только для преподавателей'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CourseCreateSerializer(data=request.data)
        if serializer.is_valid():
            course = serializer.save(teacher=request.user)
            return Response(
                TeacherCourseSerializer(course).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherCourseDetailView(APIView):
    """
    GET /api/courses/my/<id>/
    PUT /api/courses/my/<id>/
    DELETE /api/courses/my/<id>/
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_course(self, request, pk):
        if request.user.role != 'teacher':
            return None, Response(
                {'detail': 'Только для преподавателей'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            course = Course.objects.get(pk=pk, teacher=request.user)
            return course, None
        except Course.DoesNotExist:
            return None, Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, pk):
        course, error = self.get_course(request, pk)
        if error:
            return error

        serializer = CourseDetailSerializer(course)
        data = serializer.data

        # Добавляем все модули (включая неопубликованные)
        modules = course.modules.all().order_by('order')
        data['modules'] = ModuleDetailSerializer(modules, many=True).data

        return Response(data)

    def put(self, request, pk):
        course, error = self.get_course(request, pk)
        if error:
            return error

        serializer = CourseCreateSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        course, error = self.get_course(request, pk)
        if error:
            return error

        course.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeacherStatsView(APIView):
    """
    GET /api/courses/stats/
    Статистика преподавателя.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'teacher':
            return Response(
                {'detail': 'Только для преподавателей'},
                status=status.HTTP_403_FORBIDDEN
            )

        courses = Course.objects.filter(teacher=request.user)
        total_students = Enrollment.objects.filter(course__teacher=request.user).count()

        return Response({
            'courses_count': courses.count(),
            'published_count': courses.filter(is_published=True).count(),
            'students_count': total_students,
        })


# ============================================================
# МОДУЛИ
# ============================================================

class ModuleListView(APIView):
    """
    GET /api/courses/<course_id>/modules/
    POST /api/courses/<course_id>/modules/
    """
    permission_classes = [IsAuthenticated]

    def get_course(self, request, course_id):
        try:
            return Course.objects.get(pk=course_id, teacher=request.user)
        except Course.DoesNotExist:
            return None

    def get(self, request, course_id):
        course = self.get_course(request, course_id)
        if not course:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        modules = course.modules.all().order_by('order')
        serializer = ModuleDetailSerializer(modules, many=True)
        return Response(serializer.data)

    def post(self, request, course_id):
        course = self.get_course(request, course_id)
        if not course:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ModuleCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Автоматически устанавливаем порядок
            max_order = course.modules.count()
            module = serializer.save(course=course, order=max_order + 1)
            return Response(
                ModuleSerializer(module).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ModuleDetailView(APIView):
    """
    GET /api/modules/<id>/
    PUT /api/modules/<id>/
    DELETE /api/modules/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get_module(self, request, pk):
        try:
            module = Module.objects.get(pk=pk)
            if module.course.teacher != request.user:
                return None, Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return module, None
        except Module.DoesNotExist:
            return None, Response(
                {'detail': 'Модуль не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, pk):
        module, error = self.get_module(request, pk)
        if error:
            return error

        serializer = ModuleDetailSerializer(module)
        return Response(serializer.data)

    def put(self, request, pk):
        module, error = self.get_module(request, pk)
        if error:
            return error

        serializer = ModuleCreateSerializer(module, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(ModuleSerializer(module).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        module, error = self.get_module(request, pk)
        if error:
            return error

        module.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ModuleReorderView(APIView):
    """
    POST /api/courses/<course_id>/modules/reorder/
    Изменить порядок модулей
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id, teacher=request.user)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Ожидаем список ID модулей в новом порядке
        module_ids = request.data.get('module_ids', [])
        for index, module_id in enumerate(module_ids):
            Module.objects.filter(pk=module_id, course=course).update(order=index + 1)

        return Response({'detail': 'Порядок обновлён'})


# ============================================================
# УРОКИ
# ============================================================

class LessonListView(APIView):
    """
    GET /api/modules/<module_id>/lessons/
    POST /api/modules/<module_id>/lessons/
    """
    permission_classes = [IsAuthenticated]

    def get_module(self, request, module_id):
        try:
            module = Module.objects.get(pk=module_id)
            if module.course.teacher != request.user:
                return None
            return module
        except Module.DoesNotExist:
            return None

    def get(self, request, module_id):
        module = self.get_module(request, module_id)
        if not module:
            return Response(
                {'detail': 'Модуль не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        lessons = module.lessons.all().order_by('order')
        serializer = LessonDetailSerializer(lessons, many=True)
        return Response(serializer.data)

    def post(self, request, module_id):
        module = self.get_module(request, module_id)
        if not module:
            return Response(
                {'detail': 'Модуль не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LessonCreateSerializer(data=request.data)
        if serializer.is_valid():
            max_order = module.lessons.count()
            lesson = serializer.save(module=module, order=max_order + 1)
            return Response(
                LessonSerializer(lesson).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LessonDetailView(APIView):
    """
    GET /api/lessons/<id>/
    PUT /api/lessons/<id>/
    DELETE /api/lessons/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get_lesson(self, request, pk):
        try:
            lesson = Lesson.objects.get(pk=pk)
            if lesson.module.course.teacher != request.user:
                return None, Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return lesson, None
        except Lesson.DoesNotExist:
            return None, Response(
                {'detail': 'Урок не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, pk):
        lesson, error = self.get_lesson(request, pk)
        if error:
            return error

        serializer = LessonDetailSerializer(lesson)
        return Response(serializer.data)

    def put(self, request, pk):
        lesson, error = self.get_lesson(request, pk)
        if error:
            return error

        serializer = LessonCreateSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(LessonDetailSerializer(lesson).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        lesson, error = self.get_lesson(request, pk)
        if error:
            return error

        lesson.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LessonMaterialView(APIView):
    """
    POST /api/lessons/<lesson_id>/materials/
    Загрузить материал к уроку
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, lesson_id):
        try:
            lesson = Lesson.objects.get(pk=lesson_id)
            if lesson.module.course.teacher != request.user:
                return Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Lesson.DoesNotExist:
            return Response(
                {'detail': 'Урок не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LessonMaterialSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(lesson=lesson)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MaterialDeleteView(APIView):
    """
    DELETE /api/materials/<id>/
    Удалить материал
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            material = LessonMaterial.objects.get(pk=pk)
            if material.lesson.module.course.teacher != request.user:
                return Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except LessonMaterial.DoesNotExist:
            return Response(
                {'detail': 'Материал не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        material.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# ТЕСТЫ
# ============================================================

class TestView(APIView):
    """
    GET /api/modules/<module_id>/test/
    POST /api/modules/<module_id>/test/
    PUT /api/modules/<module_id>/test/
    DELETE /api/modules/<module_id>/test/
    """
    permission_classes = [IsAuthenticated]

    def get_module(self, request, module_id):
        try:
            module = Module.objects.get(pk=module_id)
            if module.course.teacher != request.user:
                return None, Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return module, None
        except Module.DoesNotExist:
            return None, Response(
                {'detail': 'Модуль не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, module_id):
        module, error = self.get_module(request, module_id)
        if error:
            return error

        try:
            test = module.test
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TestSerializer(test)
        return Response(serializer.data)

    def post(self, request, module_id):
        module, error = self.get_module(request, module_id)
        if error:
            return error

        # Проверяем, есть ли уже тест
        if hasattr(module, 'test'):
            return Response(
                {'detail': 'Тест уже существует для этого модуля'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TestCreateSerializer(data=request.data)
        if serializer.is_valid():
            test = serializer.save(module=module)
            return Response(
                TestSerializer(test).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, module_id):
        module, error = self.get_module(request, module_id)
        if error:
            return error

        try:
            test = module.test
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TestCreateSerializer(test, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(TestSerializer(test).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, module_id):
        module, error = self.get_module(request, module_id)
        if error:
            return error

        try:
            test = module.test
            test.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )


class QuestionListView(APIView):
    """
    POST /api/tests/<test_id>/questions/
    Добавить вопрос к тесту
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, test_id):
        try:
            test = Test.objects.get(pk=test_id)
            if test.module.course.teacher != request.user:
                return Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = QuestionCreateSerializer(data=request.data)
        if serializer.is_valid():
            max_order = test.questions.count()
            question = serializer.save(test=test, order=max_order + 1)
            return Response(
                QuestionSerializer(question).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuestionDetailView(APIView):
    """
    PUT /api/questions/<id>/
    DELETE /api/questions/<id>/
    """
    permission_classes = [IsAuthenticated]

    def get_question(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
            if question.test.module.course.teacher != request.user:
                return None, Response(
                    {'detail': 'Нет доступа'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return question, None
        except Question.DoesNotExist:
            return None, Response(
                {'detail': 'Вопрос не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        question, error = self.get_question(request, pk)
        if error:
            return error

        serializer = QuestionCreateSerializer(question, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(QuestionSerializer(question).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        question, error = self.get_question(request, pk)
        if error:
            return error

        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================
# ЗАПИСЬ НА КУРС
# ============================================================

class EnrollCourseView(APIView):
    """
    POST /api/courses/<id>/enroll/
    DELETE /api/courses/<id>/enroll/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            course = Course.objects.get(pk=pk, is_published=True)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, не записан ли уже
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'detail': 'Вы уже записаны на этот курс'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment = Enrollment.objects.create(student=request.user, course=course)
        return Response(
            {'detail': 'Вы успешно записались на курс'},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        try:
            enrollment = Enrollment.objects.get(student=request.user, course_id=pk)
            enrollment.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Enrollment.DoesNotExist:
            return Response(
                {'detail': 'Вы не записаны на этот курс'},
                status=status.HTTP_404_NOT_FOUND
            )


class StudentEnrollmentsView(APIView):
    """
    GET /api/courses/enrolled/
    Курсы на которые записан студент.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)


# ============================================================
# ПРОГРЕСС СТУДЕНТА
# ============================================================

class LessonCompleteView(APIView):
    """
    POST /api/lessons/<id>/complete/
    Отметить урок как завершённый
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            lesson = Lesson.objects.get(pk=pk, is_published=True)
        except Lesson.DoesNotExist:
            return Response(
                {'detail': 'Урок не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем, записан ли студент на курс
        course = lesson.module.course
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'detail': 'Вы не записаны на этот курс'},
                status=status.HTTP_403_FORBIDDEN
            )

        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )
        progress.mark_completed()

        return Response({'detail': 'Урок отмечен как завершённый'})


class CourseProgressView(APIView):
    """
    GET /api/courses/<id>/progress/
    Прогресс студента по курсу
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем запись
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'detail': 'Вы не записаны на этот курс'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Собираем прогресс
        modules_data = []
        total_lessons = 0
        completed_lessons = 0

        for module in course.modules.filter(is_published=True).order_by('order'):
            lessons = module.lessons.filter(is_published=True)
            module_lessons = []

            for lesson in lessons:
                total_lessons += 1
                progress = LessonProgress.objects.filter(
                    student=request.user,
                    lesson=lesson
                ).first()

                is_completed = progress.is_completed if progress else False
                if is_completed:
                    completed_lessons += 1

                module_lessons.append({
                    'id': lesson.id,
                    'title': lesson.title,
                    'is_completed': is_completed,
                    'video_url': lesson.video_url,
                    'duration_minutes': lesson.duration_minutes,
                })

            # Проверяем тест модуля
            test_data = None
            if hasattr(module, 'test') and module.test.is_published:
                test = module.test
                best_attempt = TestAttempt.objects.filter(
                    student=request.user,
                    test=test
                ).order_by('-score').first()

                test_data = {
                    'id': test.id,
                    'title': test.title,
                    'is_passed': best_attempt.is_passed if best_attempt else False,
                    'best_score': best_attempt.score if best_attempt else None,
                    'attempts_count': TestAttempt.objects.filter(
                        student=request.user,
                        test=test
                    ).count(),
                }

            modules_data.append({
                'id': module.id,
                'title': module.title,
                'lessons': module_lessons,
                'test': test_data,
            })

        progress_percent = round((completed_lessons / total_lessons * 100)) if total_lessons > 0 else 0

        return Response({
            'course_id': course.id,
            'course_title': course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percent': progress_percent,
            'modules': modules_data,
        })


# ============================================================
# ПРОХОЖДЕНИЕ ТЕСТА
# ============================================================

class TestStartView(APIView):
    """
    GET /api/tests/<id>/start/
    Начать тест (получить вопросы)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            test = Test.objects.get(pk=pk, is_published=True)
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем запись на курс
        course = test.module.course
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'detail': 'Вы не записаны на этот курс'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Проверяем лимит попыток
        if test.attempts_allowed > 0:
            attempts_count = TestAttempt.objects.filter(
                student=request.user,
                test=test
            ).count()
            if attempts_count >= test.attempts_allowed:
                return Response(
                    {'detail': 'Превышен лимит попыток'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Возвращаем тест без правильных ответов
        serializer = TestStudentSerializer(test)
        return Response(serializer.data)


class TestSubmitView(APIView):
    """
    POST /api/tests/<id>/submit/
    Отправить ответы теста
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            test = Test.objects.get(pk=pk, is_published=True)
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем запись на курс
        course = test.module.course
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'detail': 'Вы не записаны на этот курс'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Создаём попытку
        attempt = TestAttempt.objects.create(
            student=request.user,
            test=test
        )

        # Обрабатываем ответы
        # Формат: { "answers": { "question_id": [answer_id, ...], ... } }
        answers_data = request.data.get('answers', {})

        for question in test.questions.all():
            question_id = str(question.id)
            selected_ids = answers_data.get(question_id, [])

            test_answer = TestAnswer.objects.create(
                attempt=attempt,
                question=question
            )
            test_answer.selected_answers.set(selected_ids)
            test_answer.check_answer()

        # Подсчитываем результат
        score = attempt.calculate_score()

        return Response({
            'attempt_id': attempt.id,
            'score': score,
            'is_passed': attempt.is_passed,
            'passing_score': test.passing_score,
        })


class TestResultsView(APIView):
    """
    GET /api/tests/<id>/results/
    Результаты теста (все попытки)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            test = Test.objects.get(pk=pk)
        except Test.DoesNotExist:
            return Response(
                {'detail': 'Тест не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        attempts = TestAttempt.objects.filter(
            student=request.user,
            test=test
        ).order_by('-started_at')

        serializer = TestAttemptSerializer(attempts, many=True)
        return Response({
            'test_title': test.title,
            'passing_score': test.passing_score,
            'attempts': serializer.data,
        })


# ============================================================
# СЕРТИФИКАТЫ
# ============================================================

class CertificateView(APIView):
    """
    GET /api/courses/<id>/certificate/
    Получить сертификат (если доступен)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
        except Course.DoesNotExist:
            return Response(
                {'detail': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем включены ли сертификаты
        if not course.enable_certificate:
            return Response(
                {'detail': 'Сертификаты не предусмотрены для этого курса'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, есть ли уже сертификат
        certificate = Certificate.objects.filter(
            student=request.user,
            course=course
        ).first()

        if certificate:
            serializer = CertificateSerializer(certificate)
            return Response(serializer.data)

        # Проверяем прогресс (все уроки и тесты)
        # Простая проверка: все модули должны быть пройдены
        modules = course.modules.filter(is_published=True)
        for module in modules:
            # Проверяем уроки
            for lesson in module.lessons.filter(is_published=True):
                progress = LessonProgress.objects.filter(
                    student=request.user,
                    lesson=lesson,
                    is_completed=True
                ).exists()
                if not progress:
                    return Response(
                        {'detail': 'Курс ещё не завершён'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Проверяем тест (если есть)
            if hasattr(module, 'test') and module.test.is_published:
                passed = TestAttempt.objects.filter(
                    student=request.user,
                    test=module.test,
                    is_passed=True
                ).exists()
                if not passed:
                    return Response(
                        {'detail': 'Не все тесты сданы'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        # Создаём сертификат
        certificate = Certificate.objects.create(
            student=request.user,
            course=course
        )

        serializer = CertificateSerializer(certificate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyCertificatesView(APIView):
    """
    GET /api/certificates/
    Мои сертификаты
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        certificates = Certificate.objects.filter(student=request.user)
        serializer = CertificateSerializer(certificates, many=True)
        return Response(serializer.data)


class VerifyCertificateView(APIView):
    """
    GET /api/certificates/<number>/verify/
    Публичная проверка сертификата
    """
    permission_classes = [AllowAny]

    def get(self, request, number):
        try:
            certificate = Certificate.objects.get(certificate_number=number)
        except Certificate.DoesNotExist:
            return Response(
                {'detail': 'Сертификат не найден', 'valid': False},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CertificateVerifySerializer(certificate)
        return Response({
            'valid': True,
            'certificate': serializer.data
        })


# ============================================================
# ОБУЧЕНИЕ (ПРОСМОТР УРОКА ДЛЯ СТУДЕНТА)
# ============================================================

class StudentLessonView(APIView):
    """
    GET /api/learn/lessons/<id>/
    Получить урок для просмотра студентом
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            lesson = Lesson.objects.get(pk=pk, is_published=True)
        except Lesson.DoesNotExist:
            return Response(
                {'detail': 'Урок не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем запись на курс
        course = lesson.module.course
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response(
                {'detail': 'Вы не записаны на этот курс'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Получаем прогресс
        progress = LessonProgress.objects.filter(
            student=request.user,
            lesson=lesson
        ).first()

        serializer = LessonDetailSerializer(lesson)
        data = serializer.data
        data['is_completed'] = progress.is_completed if progress else False

        # Добавляем навигацию (пред/след урок)
        module = lesson.module
        lessons = list(module.lessons.filter(is_published=True).order_by('order'))
        current_index = next(
            (i for i, l in enumerate(lessons) if l.id == lesson.id), 0
        )

        data['prev_lesson'] = lessons[current_index - 1].id if current_index > 0 else None
        data['next_lesson'] = lessons[current_index + 1].id if current_index < len(lessons) - 1 else None

        return Response(data)
