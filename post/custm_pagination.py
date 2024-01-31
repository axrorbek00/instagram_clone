from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    page_size = 10  # 1 ta pagedan nechta bolshi defolt holda
    page_size_query_param = 'page_size'  # bu defolt holdan bowqa qiymat kirtiw imkonini beradi
    max_page_size = 100  # maksimal 1 ta pageda 100 chaqra olamiz

    def get_paginated_response(self, data):
        return Response(
            {
                "next": self.get_next_link(),  # keyingi page ga link
                "previous": self.get_previous_link(),  # avalgi page ga link
                "count": self.page.paginator.count,  # pagelar soni
                "results": data
            }
        )
