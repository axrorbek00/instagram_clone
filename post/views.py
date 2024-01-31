from django.shortcuts import render
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .custm_pagination import CustomPagination
from .models import Post, Comment, CommentLike, PostLike
from .serializers import PostSerializer, CommentSerializer, PostLikeSerializer, CommentLikeSerializer
from rest_framework import generics


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [AllowAny]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.all()


class CreatePostView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def put(self, request, *args, **kwargs):
        post = self.get_object()  # utldan kelyotgan id ni postga briktradi
        serializer = self.serializer_class(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "success": True,
                "code": status.HTTP_200_OK,
                "message": "Post updated successfully",
                "data": serializer.data
            }
        )

    def delete(self, request, *args, **kwargs):
        post = self.get_object()
        post.delete()
        return Response(
            {
                "success": True,
                "code": status.HTTP_204_NO_CONTENT,
                "message": "Post deleted successfully",
            }
        )


# Retrieve = get, Destroy = delete
# IsAuthenticatedOrReadOnly = Retrieve un AllowAny,  Update va Destroy IsAuthenticated soraydi


class PostCommentLIstView(generics.ListAPIView):  # post commentlarni korish
    serializer_class = CommentSerializer
    permission_classes = [AllowAny, ]

    def get_queryset(self):
        post_id = self.kwargs['pk']
        queryset = Comment.objects.filter(post__id=post_id)
        return queryset


class CreatePostCommentView(generics.CreateAPIView):  # comment yozish
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        post_id = self.kwargs['pk']
        serializer.save(author=self.request.user, post_id=post_id)


class CreateCommentListView(generics.ListCreateAPIView):  # hamma commentlarni korish, postga comment yozish
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = CustomPagination
    queryset = Comment.objects.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class RetrieveCommentView(generics.RetrieveAPIView):  # 1 ta kamentni olish
    serializer_class = CommentSerializer
    permission_classes = [AllowAny, ]
    queryset = Comment.objects.all()


class PostLikeListView(generics.ListAPIView):  # Post like larni olish
    serializer_class = PostLikeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        post_id = self.kwargs['pk']
        return PostLike.objects.filter(post__id=post_id)


class CommentLikesView(generics.ListAPIView):  # comentga like bosganlarni royxatni chiqaradi
    serializer_class = CommentLikeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        comment_id = self.kwargs['pk']
        return CommentLike.objects.filter(comment__id=comment_id)


class PostLikeView(APIView):  # postga like bosw va ochrish

    def post(self, request, pk):
        # post_id = self.kwargs['pk'] --> 2 - usul faqat postda pk yozlmaydi
        try:
            post_like = PostLike.objects.get(
                author=self.request.user,
                post_id=pk
            )
            post_like.delete()
            data = {
                "success": True,
                "message": "Postga LIKE muvofaqiyatlik o'chrildi",
                "data": None
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except PostLike.DoesNotExist:
            post_like = PostLike.objects.create(
                author=self.request.user,
                post_id=pk
            )
            serializer = PostLikeSerializer(post_like)
            data = {
                "success": True,
                "message": "Postga LIKE muvofaqiyatlik qo'yildi",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)


class CommentLikeView(APIView):  # commentga like bosw va ochriw

    def post(self, request, pk):
        try:
            comment_like = CommentLike.objects.get(
                author=self.request.user,
                comment_id=pk
            )
            comment_like.delete()
            data = {
                "success": True,
                "message": "LIKE muvofaqiyatlik o'chrildi",
                "data": None
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except CommentLike.DoesNotExist:
            comment_like = CommentLike.objects.create(
                author=self.request.user,
                comment_id=pk
            )
            serializer = CommentLikeSerializer(comment_like)
            data = {
                "success": True,
                "message": "LIKE muvofaqiyatlik qo'yildi",
                "data": serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)

# class PostLikeView(APIView):  # postga like bosw va ochrish
#
#     def post(self, request, pk):
#         # post_id = self.kwargs['pk'] --> 2 - usul faqat postda pk yozlmaydi
#         try:
#             post_like = PostLike.objects.create(
#                 author=self.request.user,
#                 post_id=pk
#             )
#             serializer = PostLikeSerializer(post_like)
#             data = {
#                 "success": True,
#                 "message": "Postga LIKE muvofaqiyatlik qoshldi",
#                 "data": serializer.data
#             }
#             return Response(data, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             data = {
#                 "success": False,
#                 "message": f'{str(e)}',
#                 "data": None
#             }
#             return Response(data, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self, request, pk):
#
#         try:
#             post_like = PostLike.objects.get(
#                 author=self.request.user,
#                 post__id=pk
#             )
#             post_like.delete()
#             data = {
#                 "success": True,
#                 "message": "LIKE muvofaqiyatlik ochrildi",
#                 "data": None
#             }
#             return Response(data, status=status.HTTP_204_NO_CONTENT)
#
#         except Exception as e:
#             data = {
#                 "success": False,
#                 "message": f'{str(e)}',
#                 "data": None
#             }
#             return Response(data, status=status.HTTP_400_BAD_REQUEST)
#
#
# class CommentLikeView(APIView):  # commentga like bosw va ochriw
#
#     def post(self, request, pk):
#         try:
#             comment_like = CommentLike.objects.create(
#                 author=self.request.user,
#                 comment_id=pk
#             )
#             serializer = CommentLikeSerializer(comment_like)
#             data = {
#                 "success": True,
#                 "message": "LIKE muvofaqiyatlik qoyildi",
#                 "data": serializer.data
#             }
#             return Response(data, status=status.HTTP_201_CREATED)
#         except Exception as e:
#             data = {
#                 "success": False,
#                 "message": f'{str(e)}',
#                 "data": None
#             }
#             return Response(data, status=status.HTTP_400_BAD_REQUEST)
#
#     def delete(self, request, pk):
#         try:
#             comment_like = CommentLike.objects.get(
#                 author=self.request.user,
#                 comment_id=pk
#             )
#             comment_like.delete()
#             data = {
#                 "success": True,
#                 "message": "LIKE muvofaqiyatlik ochrildi",
#                 "data": None
#             }
#             return Response(data, status=status.HTTP_204_NO_CONTENT)
#         except Exception as e:
#             data = {
#                 "success": False,
#                 "message": f'{str(e)}',
#                 "data": None
#             }
#             return Response(data, status=status.HTTP_400_BAD_REQUEST)
