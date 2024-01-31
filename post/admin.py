from django.contrib import admin
from .models import Post, Comment, PostLike, CommentLike


class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'caption', 'created_time')
    list_filter = ('id', 'author__username', 'caption', 'created_time')
    search_fields = ('id', 'author__username', 'caption', 'created_time')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_time')
    list_filter = ('id', 'author__username', 'comment', 'created_time')
    search_fields = ('id', 'author__username', 'comment', 'created_time')


class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'post', 'created_time')
    list_filter = ('id', 'author__username', 'post', 'created_time')
    search_fields = ('id', 'author__username', 'post', 'created_time')


class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'author_username', 'comment', 'created_time')
    list_filter = ('id', 'author', 'comment', 'created_time')  # 'user' o'rniga 'author' ni qo'shing
    search_fields = ('id', 'author__username', 'comment', 'created_time')  # 'user' o'rniga 'author__username' ni qo'shing

    def author_username(self, obj):
        return obj.author.username

    author_username.short_description = 'Author Username'

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(PostLike, PostLikeAdmin)
admin.site.register(CommentLike, CommentLikeAdmin)
