from django.urls import path

from .views import (
    category_list,
    product_detail,
    product_list,
    product_question_answer,
    product_questions,
    product_reviews,
    product_review_summary,
)

urlpatterns = [
    path('', product_list),
    path('categories/', category_list),
    path('<int:pk>/', product_detail),
    path('<int:pk>/reviews/', product_reviews),
    path('<int:pk>/reviews/summary/', product_review_summary),
    path('<int:pk>/questions/', product_questions),
    path('<int:pk>/questions/<int:question_id>/answer/', product_question_answer),
]
