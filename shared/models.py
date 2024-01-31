from django.db import models
import uuid


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4,
                          unique=True,
                          editable=False)  # editable=False->Tahrirlab bolmaydi, primary_key=True->primary_key ligni elon qilyamiz
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        # (inhernt)meros olish uchunligni bildiradi db ga saqlanmaydi
