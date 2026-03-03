from datetime import timedelta, timezone

from django.shortcuts import render
from django.http import JsonResponse
import json
from .models import Complaint
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404

@csrf_exempt
def resolve_complaint(request, id):
    if request.method == "POST":

        complaint = get_object_or_404(Complaint, id=id)

        photo = request.FILES.get("photo")
        note = request.POST.get("note")

        complaint.mark_resolved(photo, note)

        return JsonResponse({"status": "resolved"})

    return JsonResponse({"error": "Invalid request"}, status=400)

@csrf_exempt
def confirm_resolution(request, id):
    complaint = get_object_or_404(Complaint, id=id)

    complaint.mark_closed()

    return JsonResponse({"status": "closed"})

@staticmethod
def auto_close_resolved():
    now = timezone.now()

    seven_days_ago = now - timedelta(days=7)

    Complaint.objects.filter(
        status="Resolved",
        resolved_at__lt=seven_days_ago
    ).update(status="Closed", closed_at=now)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "complaints/login.html", {"error": "Invalid credentials"})

    return render(request, "complaints/login.html")



# 🔹 This renders the page
def add_page(request):
    return render(request, 'complaints/add_complaint.html')


# 🔹 This handles JS fetch
def add_complaint_api(request):
    if request.method == "POST":
        data = json.loads(request.body)

        Complaint.objects.create(
            name=data.get("name"),
            phone=data.get("phone"),
            area=data.get("area"),
            description=data.get("description")
        )

        return JsonResponse({
            "status": "success",
            "message": "Complaint submitted successfully"
        })

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def dashboard(request):
    complaints = Complaint.objects.all().order_by('-created_at')

    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status='Pending').count()
    resolved = Complaint.objects.filter(status='Resolved').count()
    escalated = Complaint.objects.filter(status='Escalated').count()

    return render(request, 'complaints/dashboard.html', {
        'complaints': complaints,
        'total': total,
        'pending': pending,
        'resolved': resolved,
        'escalated': escalated,
    })