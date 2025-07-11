from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Memo(models.Model):
    memo_id = models.AutoField(primary_key=True)
    create_date = models.DateTimeField(default=timezone.now)
    comment = models.TextField()
    task_assign_id = models.IntegerField()
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'memo'
        
    def __str__(self):
        return f"Memo {self.memo_id} - {self.comment[:50]}"