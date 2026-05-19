from django.contrib import admin
from .models import (
    Category, Course, Module, Lesson, LessonMaterial,
    Enrollment, LessonProgress, Test, Question, Answer,
    TestAttempt, Certificate, Payment,
)

admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(LessonMaterial)
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(Test)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(TestAttempt)
admin.site.register(Certificate)
admin.site.register(Payment)
