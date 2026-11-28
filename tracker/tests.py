from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Budget, Category, Transaction


class AddTransactionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("vero", password="pass12345!")
        self.client.force_login(self.user)
        self.cat = Category.objects.get_or_create(name="Groceries")[0]
        self.url = reverse("tracker:add_transaction")

    def post(self, **overrides):
        data = {"type": "expense", "category": self.cat.id, "amount": "10.00", "date": "2026-11-06"}
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_page_loads(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_valid_post_saves_and_redirects(self):
        r = self.post()
        self.assertRedirects(r, reverse("tracker:dashboard"))
        self.assertEqual(Transaction.objects.count(), 1)

    def test_negative_amount_rejected(self):
        r = self.post(amount="-5")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "greater than zero")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_missing_category_rejected(self):
        r = self.post(category="")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 0)


class ListEditDeleteTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("vero", password="pass12345!")
        self.client.force_login(self.user)
        self.cat = Category.objects.get_or_create(name="Rent")[0]
        self.tx = Transaction.objects.create(user=self.user, category=self.cat, type="expense", amount=100, date="2026-11-01")

    def test_list_shows_transaction(self):
        r = self.client.get(reverse("tracker:transaction_list"))
        self.assertContains(r, "Rent")

    def test_filter_by_type(self):
        r = self.client.get(reverse("tracker:transaction_list") + "?type=income")
        self.assertNotContains(r, "Rent")

    def test_edit_updates(self):
        url = reverse("tracker:edit_transaction", args=[self.tx.pk])
        r = self.client.post(url, {"type": "expense", "category": self.cat.id, "amount": "250.00", "date": "2026-11-01"})
        self.assertRedirects(r, reverse("tracker:transaction_list"))
        self.tx.refresh_from_db()
        self.assertEqual(self.tx.amount, 250)

    def test_delete_requires_post(self):
        url = reverse("tracker:delete_transaction", args=[self.tx.pk])
        self.client.get(url)
        self.assertEqual(Transaction.objects.count(), 1)
        self.client.post(url)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_missing_returns_404(self):
        self.assertEqual(self.client.get(reverse("tracker:edit_transaction", args=[999])).status_code, 404)


class BudgetCrudTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("vero", password="pass12345!")
        self.client.force_login(self.user)
        self.cat = Category.objects.get_or_create(name="Food")[0]
        self.budget = Budget.objects.create(user=self.user, category=self.cat, monthly_limit=500)

    def test_list_shows_budget(self):
        self.assertContains(self.client.get(reverse("tracker:budget_list")), "Food")

    def test_add_budget(self):
        other = Category.objects.get_or_create(name="Fun")[0]
        r = self.client.post(reverse("tracker:add_budget"), {"category": other.id, "monthly_limit": "80"})
        self.assertRedirects(r, reverse("tracker:budget_list"))
        self.assertEqual(Budget.objects.count(), 2)

    def test_zero_limit_rejected(self):
        r = self.client.post(reverse("tracker:add_budget"), {"category": self.cat.id, "monthly_limit": "0"})
        self.assertEqual(r.status_code, 200)

    def test_edit_budget(self):
        r = self.client.post(reverse("tracker:edit_budget", args=[self.budget.pk]),
                             {"category": self.cat.id, "monthly_limit": "650"})
        self.assertRedirects(r, reverse("tracker:budget_list"))
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.monthly_limit, 650)

    def test_delete_budget(self):
        self.client.post(reverse("tracker:delete_budget", args=[self.budget.pk]))
        self.assertEqual(Budget.objects.count(), 0)

    def test_nav_links_resolve_on_every_page(self):
        for name in ["dashboard", "transaction_list", "budget_list", "about"]:
            self.assertEqual(self.client.get(reverse(f"tracker:{name}")).status_code, 200)


PROTECTED = ["dashboard", "transaction_list", "budget_list", "add_transaction", "add_budget"]


class LoginRequiredTests(TestCase):
    def test_anonymous_redirected_to_login(self):
        for name in PROTECTED:
            url = reverse(f"tracker:{name}")
            r = self.client.get(url)
            self.assertRedirects(r, f"{reverse('tracker:login')}?next={url}", msg_prefix=name)

    def test_about_and_auth_pages_are_public(self):
        for name in ["about", "login", "signup"]:
            self.assertEqual(self.client.get(reverse(f"tracker:{name}")).status_code, 200)


class SignupLoginTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        r = self.client.post(reverse("tracker:signup"), {
            "username": "newuser", "password1": "Str0ng-pass-99", "password2": "Str0ng-pass-99"})
        self.assertRedirects(r, reverse("tracker:dashboard"))
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertEqual(self.client.get(reverse("tracker:dashboard")).status_code, 200)

    def test_signup_password_mismatch(self):
        r = self.client.post(reverse("tracker:signup"), {
            "username": "newuser", "password1": "Str0ng-pass-99", "password2": "different"})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_weak_password_rejected(self):
        self.client.post(reverse("tracker:signup"), {"username": "x", "password1": "12345678", "password2": "12345678"})
        self.assertFalse(User.objects.filter(username="x").exists())

    def test_login_and_logout(self):
        User.objects.create_user("vero", password="pass12345!")
        r = self.client.post(reverse("tracker:login"), {"username": "vero", "password": "pass12345!"})
        self.assertRedirects(r, reverse("tracker:dashboard"))
        self.client.post(reverse("tracker:logout"))
        self.assertEqual(self.client.get(reverse("tracker:dashboard")).status_code, 302)

    def test_wrong_password_rejected(self):
        User.objects.create_user("vero", password="pass12345!")
        r = self.client.post(reverse("tracker:login"), {"username": "vero", "password": "nope"})
        self.assertEqual(r.status_code, 200)

    def test_logout_needs_post(self):
        self.client.force_login(User.objects.create_user("vero", password="pass12345!"))
        self.assertEqual(self.client.get(reverse("tracker:logout")).status_code, 405)


class DataIsolationTests(TestCase):
    """User B must never see or touch user A's data."""

    def setUp(self):
        self.a = User.objects.create_user("alice", password="pass12345!")
        self.b = User.objects.create_user("bob", password="pass12345!")
        self.cat = Category.objects.get_or_create(name="Food")[0]
        self.a_tx = Transaction.objects.create(user=self.a, category=self.cat, amount=111, description="alice-secret")
        self.a_budget = Budget.objects.create(user=self.a, category=self.cat, monthly_limit=900)
        self.client.force_login(self.b)

    def test_lists_hide_other_users_data(self):
        self.assertNotContains(self.client.get(reverse("tracker:transaction_list")), "alice-secret")
        self.assertNotContains(self.client.get(reverse("tracker:budget_list")), "900")

    def test_dashboard_totals_only_own_data(self):
        r = self.client.get(reverse("tracker:dashboard"))
        self.assertEqual(r.context["total_balance"], 0)

    def test_cannot_edit_or_delete_other_users_transaction(self):
        edit = reverse("tracker:edit_transaction", args=[self.a_tx.pk])
        delete = reverse("tracker:delete_transaction", args=[self.a_tx.pk])
        self.assertEqual(self.client.get(edit).status_code, 404)
        self.assertEqual(self.client.post(edit, {"type": "expense", "category": self.cat.id, "amount": "1", "date": "2026-11-06"}).status_code, 404)
        self.assertEqual(self.client.post(delete).status_code, 404)
        self.assertTrue(Transaction.objects.filter(pk=self.a_tx.pk).exists())

    def test_cannot_edit_or_delete_other_users_budget(self):
        self.assertEqual(self.client.post(reverse("tracker:delete_budget", args=[self.a_budget.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("tracker:edit_budget", args=[self.a_budget.pk])).status_code, 404)
        self.assertTrue(Budget.objects.filter(pk=self.a_budget.pk).exists())

    def test_new_records_belong_to_logged_in_user(self):
        self.client.post(reverse("tracker:add_transaction"),
                         {"type": "expense", "category": self.cat.id, "amount": "5", "date": "2026-11-06"})
        self.assertEqual(Transaction.objects.get(amount=5).user, self.b)

    def test_each_user_can_have_a_budget_for_same_category(self):
        r = self.client.post(reverse("tracker:add_budget"), {"category": self.cat.id, "monthly_limit": "50"})
        self.assertRedirects(r, reverse("tracker:budget_list"))

    def test_duplicate_budget_for_same_user_rejected(self):
        self.client.post(reverse("tracker:add_budget"), {"category": self.cat.id, "monthly_limit": "50"})
        r = self.client.post(reverse("tracker:add_budget"), {"category": self.cat.id, "monthly_limit": "60"})
        self.assertContains(r, "already have a budget")
        self.assertEqual(Budget.objects.filter(user=self.b).count(), 1)

    def test_spent_this_month_ignores_other_users(self):
        b_budget = Budget.objects.create(user=self.b, category=self.cat, monthly_limit=100)
        Transaction.objects.create(user=self.b, category=self.cat, amount=10, type="expense")
        Transaction.objects.create(user=self.a, category=self.cat, amount=70, type="expense")
        self.assertEqual(b_budget.spent_this_month, 10)


class ClaimOrphansTests(TestCase):
    def test_orphans_are_assigned(self):
        user = User.objects.create_user("vero", password="pass12345!")
        cat = Category.objects.get_or_create(name="Food")[0]
        Transaction.objects.create(category=cat, amount=5)
        Budget.objects.create(category=cat, monthly_limit=50)
        call_command("claim_orphans", "vero")
        self.assertEqual(Transaction.objects.filter(user=user).count(), 1)
        self.assertEqual(Budget.objects.filter(user=user).count(), 1)


class DefaultCategoriesTests(TestCase):
    """A brand-new database must already have categories to pick from."""

    def test_defaults_exist_after_migrate(self):
        names = set(Category.objects.values_list("name", flat=True))
        for expected in ["Groceries", "Rent", "Transport", "Salary", "Airtime & Data", "Other"]:
            self.assertIn(expected, names)

    def test_add_form_offers_categories(self):
        self.client.force_login(User.objects.create_user("vero", password="pass12345!"))
        r = self.client.get(reverse("tracker:add_transaction"))
        self.assertContains(r, "Groceries")
        self.assertContains(r, "Airtime &amp; Data")
