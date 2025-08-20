from django.contrib import admin
from .models import Profile, Lesson, Test, Question, Attempt
from django import forms

class TestAdminForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = '__all__'
        labels = {
            'review_enabled': 'Review disabled',  # يظهر في لوحة الإدارة
        }

class TestAdmin(admin.ModelAdmin):
    form = TestAdminForm

admin.site.register(Profile)
admin.site.register(Lesson)
admin.site.register(Test, TestAdmin)
admin.site.register(Question)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'score', 'completed', 'review_enabled')
    list_filter = ('test', 'completed', 'review_enabled')
    search_fields = ('user__username', 'test__title')
    readonly_fields = ('completed_at',)

    def save_model(self, request, obj, form, change):
        # obj هو كائن Attempt
        # التحقق مما إذا تم تغيير حقل الإجابات
        if 'answers' in form.changed_data:
            new_score = 0
            questions = Question.objects.filter(test=obj.test)
            student_answers = obj.answers or {}

            for question in questions:
                question_id_str = str(question.id)
                student_answer = student_answers.get(question_id_str)

                if student_answer is not None:
                    try:
                        # مقارنة الإجابة بالإجابة الصحيحة
                        if int(student_answer) == int(question.correct_answer):
                            new_score += 1
                    except (ValueError, TypeError):
                        # تجاهل الإجابات غير الصالحة
                        pass
            
            obj.score = new_score
        
        super().save_model(request, obj, form, change)

admin.site.register(Attempt, AttemptAdmin)
