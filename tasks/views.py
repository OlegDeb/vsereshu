from django.http import Http404
from django.shortcuts import get_object_or_404, render

from .models import Task

__all__ = ["task_list", "task_detail"]


def task_list(request):
    tasks = (
        Task.objects.select_related("category", "city", "author")
        .filter(is_active=True)
        .order_by("-created_at")
    )
    return render(request, "tasks/task_list.html", {"tasks": tasks})


def task_detail(request, slug: str):
    id_part, sep, slug_part = slug.partition("-")
    if sep == "" or not id_part.isdigit():
        raise Http404("Task not found")

    task = get_object_or_404(
        Task.objects.select_related("category", "city", "author"),
        pk=int(id_part),
        slug=slug_part,
        is_active=True,
    )
    return render(request, "tasks/task_detail.html", {"task": task})
