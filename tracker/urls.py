from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/<int:pk>/edit/", views.edit_transaction, name="edit_transaction"),
    path("transactions/<int:pk>/delete/", views.delete_transaction, name="delete_transaction"),
    path("transactions/add/", views.add_transaction, name="add_transaction"),
    path("budgets/add/", views.add_budget, name="add_budget"),
    path("budgets/", views.budget_list, name="budget_list"),
    path("budgets/<int:pk>/edit/", views.edit_budget, name="edit_budget"),
    path("budgets/<int:pk>/delete/", views.delete_budget, name="delete_budget"),
    path("about/", views.about, name="about"),
    path("accounts/signup/", views.signup, name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="tracker/login.html", redirect_authenticated_user=True),
        name="login",
    ),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
]
