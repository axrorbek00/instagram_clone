from rest_framework import serializers
from post.models import Post, PostLike, Comment, CommentLike
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)  # id ni uuidi korniwga otkazberadi

    class Meta:
        model = User
        fields = ('id', 'username', 'photo')


# serializer username, post image, caption, like count, comment cont created time va biz bu postga
# like bosgan yoki yoqligni qaytaradi
class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    post_likes_count = serializers.SerializerMethodField('get_post_likes_count')  # 'get_likes_count' funksiya chaqramiz
    post_comments_count = serializers.SerializerMethodField('get_post_comments_count')
    me_liked = serializers.SerializerMethodField('get_me_likes')  # request jonatyotgan postga like bosganmanmi yoqmi

    class Meta:
        model = Post
        fields = (
            'id',
            'author',
            'image',
            'caption',
            'created_time',
            'post_likes_count',
            'post_comments_count',
            'me_liked'
        )
        extra_kwargs = {"image": {"required": False}}

    @staticmethod
    def get_post_likes_count(obj):  # obj request kelyotgan post
        return obj.post_likes.count()  # post_likes Like modeldagi related_name='post_likes'

    @staticmethod
    def get_post_comments_count(obj):
        return obj.comments.count()

    def get_me_likes(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                PostLike.objects.get(post=obj, author=request.user)
                return True
            except PostLike.DoesNotExist:
                return False
        return False


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField('get_replies')
    me_liked = serializers.SerializerMethodField('get_me_likes')
    likes_count = serializers.SerializerMethodField('get_likes')

    class Meta:
        model = Comment
        fields = ['id', 'author', 'created_time', 'post', 'comment', 'parent', 'replies', 'me_liked', 'likes_count']

    def get_replies(self, obj):
        if obj.children.exists():  # children comment modelda yozlgan, bu commentga replay bormi yoqmi degani
            # serializer = CommentSerializer(obj.children.all(), many=True, context=self.context), ichma ich chaqrish
            serializer = self.__class__(obj.children.all(), many=True, context=self.context)  # bir birga teng
            return serializer.data
        else:
            return None

    def get_me_likes(self, obj):  # camentga like bosganmizmi yoqmi
        user = self.context['request'].user  # request contextni olyamiz bu viewdan keladi
        if user.is_authenticated:
            return obj.comment_likes.filter(author=user).exists()  # wu comment like bosganlar ichda men bor bolsam
        else:
            return False

    @staticmethod
    def get_likes(obj):  # comment yiqan likelar soni
        return obj.comment_likes.count()


class CommentLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ("id", "author", "comment")


class PostLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ("id", "author", "post")


