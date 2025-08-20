from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    ROLE_CHOICES = (('student','Student'), ('admin','Admin'))
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.user.username} ({self.role})"

class Lesson(models.Model):
    TYPE_CHOICES = (
        ('text', 'Text'),
        ('video', 'Video'),
        ('text_video', 'Text + Video'),  # جديد
    )
    title = models.CharField(max_length=255)
    lesson_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    content = models.TextField(blank=True)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True, null=True)
    text_position = models.CharField(
        max_length=10,
        choices=(('top', 'النص فوق الفيديو'), ('bottom', 'النص تحت الفيديو')),
        default='top',
        blank=True,
        null=True
    )
    is_hidden = models.BooleanField(default=False, verbose_name="إخفاء الدرس", help_text="إذا تم تحديده، سيتم إخفاء الدرس عن الطلاب.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Test(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    time_limit = models.IntegerField(default=0)
    time_unit = models.CharField(
        max_length=10,
        choices=(('seconds', 'ثواني'), ('minutes', 'دقائق'), ('hours', 'ساعات')),
        default='minutes'
    )
    prevent_review = models.BooleanField(
        default=False, 
        verbose_name="منع مراجعة الاختبار", 
        help_text="إذا تم تحديده، لن يتمكن الطالب من مراجعة إجاباته بعد انتهاء الاختبار."
    )

    def __str__(self):
        return self.title

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    image = models.ImageField(upload_to='questions/', blank=True, null=True)  # جديد
    choices = models.TextField(help_text='comma separated choices')
    correct_answer = models.PositiveSmallIntegerField(help_text='رقم الخيار الصحيح (1 أو 2 أو 3 أو 4)')  # جديد

    def get_choices(self):
        return [c.strip() for c in self.choices.split(',')]

    def correct_choice_text(self):
        choices = self.get_choices()
        idx = self.correct_answer - 1
        if 0 <= idx < len(choices):
            return choices[idx]
        return ""

class Attempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    answers = models.JSONField(default=dict, blank=True)
    review_enabled = models.BooleanField(default=False)  # أضف هذا السطر أو عدله ليكون هكذا

    class Meta:
        unique_together = ('user','test')

    def __str__(self):
        return f"{self.user.username} - {self.test.title}"
