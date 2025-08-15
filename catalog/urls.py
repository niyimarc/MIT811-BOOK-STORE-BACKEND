from django.urls import path
from .views import (
    AuthorListView,
    CategoryListView,
    PublisherListView,
    TagListView,
    BookListView,
    BookDetailView,
    BookImageListView,
    RatingCountsView,
    SubmitProductRatingView
)

urlpatterns = [
    path("api/catalog/authors/", AuthorListView.as_view(), name="author-list"),
    path("api/catalog/categories/", CategoryListView.as_view(), name="category-list"),
    path("api/catalog/publishers/", PublisherListView.as_view(), name="publisher-list"),
    path("api/catalog/tags/", TagListView.as_view(), name="tag-list"),
    path("api/catalog/books/", BookListView.as_view(), name="book-list"),
    path("api/catalog/books/<slug:slug>/", BookDetailView.as_view(), name="book-detail"),
    path("api/catalog/book-images/", BookImageListView.as_view(), name="book-image-list"),
    path("api/catalog/rating-counts/", RatingCountsView.as_view(), name="rating-counts"),
    path("api/catalog/<slug:slug>/reviews/", SubmitProductRatingView.as_view(), name="submit-product-reviews"),
]
