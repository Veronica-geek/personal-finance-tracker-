from django.db import models
from django.utils import timezone
from django.db.models import Sum


class Category(models.Model):
    """A spending/income category, e.g. Groceries, Rent, Salary."""

    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(
        max_length=10,
        blank=True,
        help_text="Optional emoji or short icon label shown on the dashboard, e.g. 'groceries'",
    )

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    """A single income or expense entry.

    NOTE: once Authentication (Phase 7) is added, give this a
    `user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)`
    field so each user only ever sees their own transactions.
    """

    INCOME = "income"
    EXPENSE = "expense"
    TYPE_CHOICES = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]

    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="transactions"
    )
    type = models.CharField(max_length=7, choices=TYPE_CHOICES, default=EXPENSE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.get_type_display()}: {self.amount} ({self.category})"


class Budget(models.Model):
    """A monthly spending limit for one category."""

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="budgets")
    monthly_limit = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["category__name"]

    def __str__(self):
        return f"{self.category} budget: {self.monthly_limit}"

    @property
    def spent_this_month(self):
        today = timezone.localdate()
        total = self.category.transactions.filter(
            type=Transaction.EXPENSE, date__year=today.year, date__month=today.month
        ).aggregate(total=Sum("amount"))["total"]
        return total or 0

    @property
    def remaining(self):
        return self.monthly_limit - self.spent_this_month

    @property
    def percent_used(self):
        if not self.monthly_limit:
            return 0
        pct = (self.spent_this_month / self.monthly_limit) * 100
        return min(round(pct), 100)
