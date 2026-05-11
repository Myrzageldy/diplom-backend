from django.urls import path
from .views import (
    # Публичные
    CourseListView, CourseDetailView, CategoryListView,

    # Учитель - курсы
    TeacherCoursesView, TeacherCourseDetailView, TeacherStatsView, CourseUploadImageView,
    TeacherStudentsView,

    # Модули
    ModuleListView, ModuleDetailView, ModuleReorderView,

    # Уроки
    LessonListView, LessonDetailView, LessonMaterialView, MaterialDeleteView,

    # Тесты
    TestView, QuestionListView, QuestionDetailView,

    # Запись на курс
    EnrollCourseView, StudentEnrollmentsView,

    # Платежи
    PaymentInitView, PaymentConfirmView, PaymentStatusView,

    # Прогресс
    LessonCompleteView, CourseProgressView,

    # Прохождение теста
    TestStartView, TestSubmitView, TestResultsView,

    # Сертификаты
    CertificateView, MyCertificatesView, VerifyCertificateView,

    # Обучение
    StudentLessonView,
)

urlpatterns = [
    # ============================================================
    # ПУБЛИЧНЫЕ
    # ============================================================
    path('', CourseListView.as_view(), name='course-list'),
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),

    # ============================================================
    # УЧИТЕЛЬ - КУРСЫ
    # ============================================================
    path('my/', TeacherCoursesView.as_view(), name='teacher-courses'),
    path('my/students/', TeacherStudentsView.as_view(), name='teacher-students'),
    path('my/<int:pk>/', TeacherCourseDetailView.as_view(), name='teacher-course-detail'),
    path('my/<int:pk>/upload-image/', CourseUploadImageView.as_view(), name='course-upload-image'),
    path('stats/', TeacherStatsView.as_view(), name='teacher-stats'),

    # ============================================================
    # МОДУЛИ
    # ============================================================
    path('<int:course_id>/modules/', ModuleListView.as_view(), name='module-list'),
    path('<int:course_id>/modules/reorder/', ModuleReorderView.as_view(), name='module-reorder'),
    path('modules/<int:pk>/', ModuleDetailView.as_view(), name='module-detail'),

    # ============================================================
    # УРОКИ
    # ============================================================
    path('modules/<int:module_id>/lessons/', LessonListView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', LessonDetailView.as_view(), name='lesson-detail'),
    path('lessons/<int:lesson_id>/materials/', LessonMaterialView.as_view(), name='lesson-materials'),
    path('materials/<int:pk>/', MaterialDeleteView.as_view(), name='material-delete'),

    # ============================================================
    # ТЕСТЫ
    # ============================================================
    path('modules/<int:module_id>/test/', TestView.as_view(), name='module-test'),
    path('tests/<int:test_id>/questions/', QuestionListView.as_view(), name='question-list'),
    path('questions/<int:pk>/', QuestionDetailView.as_view(), name='question-detail'),

    # ============================================================
    # ЗАПИСЬ НА КУРС
    # ============================================================
    path('<int:pk>/enroll/', EnrollCourseView.as_view(), name='course-enroll'),
    path('enrolled/', StudentEnrollmentsView.as_view(), name='student-enrollments'),

    # ============================================================
    # ПЛАТЕЖИ
    # ============================================================
    path('<int:pk>/payment/init/', PaymentInitView.as_view(), name='payment-init'),
    path('payment/<uuid:payment_id>/confirm/', PaymentConfirmView.as_view(), name='payment-confirm'),
    path('payment/<uuid:payment_id>/status/', PaymentStatusView.as_view(), name='payment-status'),

    # ============================================================
    # ПРОГРЕСС И ОБУЧЕНИЕ
    # ============================================================
    path('<int:pk>/progress/', CourseProgressView.as_view(), name='course-progress'),
    path('lessons/<int:pk>/complete/', LessonCompleteView.as_view(), name='lesson-complete'),
    path('learn/lessons/<int:pk>/', StudentLessonView.as_view(), name='student-lesson'),

    # ============================================================
    # ПРОХОЖДЕНИЕ ТЕСТА
    # ============================================================
    path('tests/<int:pk>/start/', TestStartView.as_view(), name='test-start'),
    path('tests/<int:pk>/submit/', TestSubmitView.as_view(), name='test-submit'),
    path('tests/<int:pk>/results/', TestResultsView.as_view(), name='test-results'),

    # ============================================================
    # СЕРТИФИКАТЫ
    # ============================================================
    path('<int:pk>/certificate/', CertificateView.as_view(), name='course-certificate'),
    path('certificates/', MyCertificatesView.as_view(), name='my-certificates'),
    path('certificates/<str:number>/verify/', VerifyCertificateView.as_view(), name='verify-certificate'),
]
