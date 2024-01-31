from django.urls import path
from .views import PostListView, CreatePostView, PostRetrieveUpdateDestroyView, PostCommentLIstView, \
    CreatePostCommentView, CreateCommentListView, PostLikeListView, RetrieveCommentView, CommentLikesView, \
    PostLikeView, CommentLikeView

urlpatterns = [
    path('posts/', PostListView.as_view()),
    path('create/', CreatePostView.as_view()),
    path('posts/<uuid:pk>/', PostRetrieveUpdateDestroyView.as_view()),
    path('posts/<uuid:pk>/comments/', PostCommentLIstView.as_view()),
    path('posts/<uuid:pk>/comments/create/', CreatePostCommentView.as_view()),
    path('posts/<uuid:pk>/likes/', PostLikeListView.as_view()),
    path('posts/comments/', CreateCommentListView.as_view()),
    path('posts/comments/<uuid:pk>/', RetrieveCommentView.as_view()),
    path('posts/comments/<uuid:pk>/likes/', CommentLikesView.as_view()),

    path('posts/<uuid:pk>/create_delete_like/', PostLikeView.as_view()),
    path('comment/<uuid:pk>/create_delete_like/', CommentLikeView.as_view()),
]
