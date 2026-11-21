from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Budget, Category, Transaction


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["type", "category", "amount", "description", "date"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_category(self):
        category = self.cleaned_data.get("category")
        if category is None:
            raise forms.ValidationError("Please choose a category.")
        return category


class BudgetForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    class Meta:
        model = Budget
        fields = ["category", "monthly_limit"]
        widgets = {"monthly_limit": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"})}

    def clean_monthly_limit(self):
        limit = self.cleaned_data["monthly_limit"]
        if limit <= 0:
            raise forms.ValidationError("Budget limit must be greater than zero.")
        return limit

    def clean_category(self):
        category = self.cleaned_data["category"]
        taken = Budget.objects.filter(user=self.user, category=category).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError("You already have a budget for this category. Edit it instead.")
        return category


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=False, help_text="Optional.")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ["username", "email"]
