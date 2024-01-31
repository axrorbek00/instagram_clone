from django.core.validators import FileExtensionValidator, MaxLengthValidator
from django.db import models
from users.models import User
from shared.models import BaseModel


class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    caption = models.TextField(validators=[MaxLengthValidator(5000)])
    image = models.ImageField(upload_to='post_images', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])

    def __str__(self):
        return f'{self.author} post about {self.caption}'

    class Meta:
        db_table = 'post'
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'


class Comment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(validators=[MaxLengthValidator(800)])
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    # commentga coment yozish un (parent)

    def __str__(self):
        return f'{self.author}--{self.comment}'

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'


# 1) id=1248
#    comment = juda chroylik
#    parent = null (brinchi camment parenti doyim null boladi)
#
# 2) id=8967
#    comment = qaysi birini aytyapsiz
#    parent = 1248


class PostLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='post_likes')

    def __str__(self):
        return f'{self.author} liked post {self.post}'

    class Meta:
        verbose_name = 'PostLike'
        verbose_name_plural = 'PostLikes'
        unique_together = ('author', 'post')  # user faqat 1 ta postga 1 ta like berwini anglatadi


class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='comment_likes')

    def __str__(self):
        return f'{self.author} liked comment {self.comment}'

    class Meta:
        verbose_name = 'CommentLike'
        verbose_name_plural = 'CommentLikes'
        unique_together = ('author', 'comment')
