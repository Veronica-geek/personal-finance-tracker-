from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BudgetForm, SignupForm, TransactionForm
from .models import Budget, Transaction

DAY_LABELS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
BAR_COLORS = ["#241F3D", "#EB5757", "#8C6FF7", "#8C6FF7", "#F5A623", "#241F3D", "#EB5757"]
TAG_PALETTE = ["#EB5757", "#8C6FF7", "#F5A623", "#4F86F7", "#27AE60", "#ED64A6"]

QUICK_ACTIONS = [
    {"label": "Home", "color": "#EB5757", "icon": "⌂"},
    {"label": "Gas", "color": "#8C6FF7", "icon": "⛽"},
    {"label": "Security", "color": "#F5A623", "icon": "⛨"},
    {"label": "Videos", "color": "#4F86F7", "icon": "▶"},
    {"label": "Games", "color": "#F5A623", "icon": "●"},
    {"label": "Papers", "color": "#27AE60", "icon": "☷"},
    {"label": "Shops", "color": "#ED64A6", "icon": "■"},
    {"label": "Travel", "color": "#8C6FF7", "icon": "✈"},
    {"label": "Service", "color": "#27AE60", "icon": "⚙"},
]


def _tag_color(name):
    if not name:
        return "#9AA0C3"
    total = sum(ord(c) for c in name)
    return TAG_PALETTE[total % len(TAG_PALETTE)]


def _tx_to_dict(tx):
    category_name = tx.category.name if tx.category else "Uncategorized"
    return {
        "date": tx.date,
        "category": category_name,
        "description": tx.description,
        "amount": tx.amount,
        "type": tx.type,
        "color": _tag_color(category_name),
    }


@login_required
def dashboard(request):
   
    user_tx = Transaction.objects.filter(user=request.user)
    today = timezone.localdate()
    yesterday = today - timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())  # Monday of this week
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)

    # --- Current balance (all-time income minus all-time expenses) ---
    all_income = user_tx.filter(type=Transaction.INCOME).aggregate(t=Sum("amount"))["t"] or 0
    all_expense = user_tx.filter(type=Transaction.EXPENSE).aggregate(t=Sum("amount"))["t"] or 0
    total_balance = all_income - all_expense

    month_income = (
        user_tx.filter(type=Transaction.INCOME, date__year=today.year, date__month=today.month)
        .aggregate(t=Sum("amount"))["t"]
        or 0
    )

    # --- This week's daily spend, Monday through Sunday ---
    daily_totals = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        amount = (
            user_tx.filter(type=Transaction.EXPENSE, date=day).aggregate(t=Sum("amount"))["t"] or 0
        )
        daily_totals.append(float(amount))

    max_day = max(daily_totals) if any(daily_totals) else 0
    daily_spend = []
    for i, amount in enumerate(daily_totals):
        pct = round((amount / max_day) * 100) if max_day else 0
        daily_spend.append(
            {"label": DAY_LABELS[i], "amount": amount, "pct": max(pct, 4), "color": BAR_COLORS[i]}
        )
    week_total = sum(daily_totals)

    last_week_total = float(
        user_tx.filter(
            type=Transaction.EXPENSE, date__gte=last_week_start, date__lte=last_week_end
        ).aggregate(t=Sum("amount"))["t"]
        or 0
    )
    trend_pct = round(((week_total - last_week_total) / last_week_total) * 100, 1) if last_week_total else None

    # --- Sparkline points for the "spending trend" mini chart ---
    width, height = 100, 28
    n = len(daily_totals)
    step = width / (n - 1) if n > 1 else width
    if max_day:
        points = [
            f"{round(i * step, 1)},{round(height - (val / max_day) * height, 1)}"
            for i, val in enumerate(daily_totals)
        ]
    else:
        points = [f"{round(i * step, 1)},{height}" for i in range(n)]
    sparkline_points = " ".join(points)

    # --- Budgets / savings ---
    budgets = list(Budget.objects.filter(user=request.user).select_related("category"))
    total_savings = sum((b.remaining for b in budgets if b.remaining > 0), 0)

    top_category = (
        user_tx.filter(type=Transaction.EXPENSE, date__year=today.year, date__month=today.month)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
        .first()
    )

    # --- Activity feed, grouped ---
    today_activity = [
        _tx_to_dict(t) for t in user_tx.select_related("category").filter(date=today)[:5]
    ]
    yesterday_activity = [
        _tx_to_dict(t) for t in user_tx.select_related("category").filter(date=yesterday)[:5]
    ]

    # --- Last month's activity table ---
    last_30 = today - timedelta(days=30)
    activities = [
        _tx_to_dict(t)
        for t in user_tx.select_related("category").filter(date__gte=last_30).order_by("-date")[:6]
    ]

    context = {
        "today": today,
        "total_balance": total_balance,
        "month_income": month_income,
        "daily_spend": daily_spend,
        "week_total": week_total,
        "trend_pct": trend_pct,
        "sparkline_points": sparkline_points,
        "total_savings": total_savings,
        "top_category": top_category,
        "today_activity": today_activity,
        "yesterday_activity": yesterday_activity,
        "activities": activities,
        "quick_actions": QUICK_ACTIONS,
    }
    return render(request, "tracker/dashboard.html", context)


def about(request):
    """Renders a PROJECT-level template (templates/about.html), separate from
    the app-level templates used by dashboard() above. Public: no login needed."""
    return render(request, "about.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("tracker:dashboard")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account is ready.")
            return redirect("tracker:dashboard")
    else:
        form = SignupForm()
    return render(request, "tracker/signup.html", {"form": form})


def _save_for_user(form, user):
    """Save a ModelForm and stamp the new object with its owner."""
    obj = form.save(commit=False)
    obj.user = user
    obj.save()
    return obj


@login_required
def add_transaction(request):
    form = TransactionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        _save_for_user(form, request.user)
        messages.success(request, "Transaction saved.")
        return redirect("tracker:dashboard")
    return render(request, "tracker/transaction_form.html", {"form": form, "title": "Add transaction"})


@login_required
def transaction_list(request):
    transactions = Transaction.objects.filter(user=request.user).select_related("category")
    tx_type = request.GET.get("type")
    if tx_type in (Transaction.INCOME, Transaction.EXPENSE):
        transactions = transactions.filter(type=tx_type)
    page = Paginator(transactions, 10).get_page(request.GET.get("page"))
    return render(request, "tracker/transaction_list.html", {"page": page, "tx_type": tx_type})


@login_required
def edit_transaction(request, pk):
    # Filtering by user means someone else's pk gives a 404, not their data.
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = TransactionForm(request.POST or None, instance=transaction)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Transaction updated.")
        return redirect("tracker:transaction_list")
    return render(request, "tracker/transaction_form.html", {"form": form, "title": "Edit transaction"})


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == "POST":
        transaction.delete()
        messages.success(request, "Transaction deleted.")
        return redirect("tracker:transaction_list")
    return render(request, "tracker/transaction_confirm_delete.html", {"transaction": transaction})


@login_required
def add_budget(request):
    form = BudgetForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        _save_for_user(form, request.user)
        messages.success(request, "Budget saved.")
        return redirect("tracker:budget_list")
    return render(request, "tracker/transaction_form.html", {"form": form, "title": "Add budget"})


@login_required
def budget_list(request):
    budgets = Budget.objects.filter(user=request.user).select_related("category")
    return render(request, "tracker/budget_list.html", {"budgets": budgets})


@login_required
def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    form = BudgetForm(request.POST or None, instance=budget, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Budget updated.")
        return redirect("tracker:budget_list")
    return render(request, "tracker/transaction_form.html", {"form": form, "title": "Edit budget"})


@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == "POST":
        budget.delete()
        messages.success(request, "Budget deleted.")
        return redirect("tracker:budget_list")
    return render(request, "tracker/budget_confirm_delete.html", {"budget": budget})
