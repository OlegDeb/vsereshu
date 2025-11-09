from django.shortcuts import render

from .models import Task


def task_list(request):
    tasks = (
        Task.objects.select_related("category", "city", "author")
        .filter(is_active=True)
        .order_by("-created_at")
    )
    return render(request, "tasks/task_list.html", {"tasks": tasks})
