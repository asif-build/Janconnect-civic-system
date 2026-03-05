from datetime import timedelta
from email.mime import text
from django.utils import timezone

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

import json
from .models import Area, Complaint, Department, Officer


# ================= RESOLVE COMPLAINT ================= #

@csrf_exempt
@login_required
def resolve_complaint(request, id):
    if request.method == "POST":
        complaint = get_object_or_404(Complaint, id=id)

        photo = request.FILES.get("photo")
        note = request.POST.get("note")

        complaint.mark_resolved(photo, note)

        return JsonResponse({"status": "resolved"})

    return JsonResponse({"error": "Invalid request"}, status=400)


# ================= CONFIRM RESOLUTION ================= #

@csrf_exempt
@login_required
def confirm_resolution(request, id):
    complaint = get_object_or_404(Complaint, id=id)
    complaint.mark_closed()
    return JsonResponse({"status": "closed"})


# ================= AUTO CLOSE FUNCTION ================= #

def auto_close_resolved():
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)

    Complaint.objects.filter(
        status="Resolved",
        resolved_at__lt=seven_days_ago
    ).update(status="Closed", closed_at=now)


# ================= LOGIN ================= #

from django.shortcuts import redirect

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

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

# ================= REGISTER ================= #

from django.contrib.auth.models import User
from .models import Complaint   # keep existing

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, "complaints/login.html", {
                "error": "Username already exists"
            })

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # You can save phone in profile model (recommended)
        # For now, just store in first_name temporarily:
        user.first_name = phone
        user.save()

        return redirect("login")

    return redirect("login")
def add_page(request):
    return render(request, 'complaints/add_complaint.html')

# ================= DEPARTMENT DETECTION ================= #

def detect_department(description):

    text = description.lower()

    try:
        if "road" in text or "pothole" in text:
            return Department.objects.get(name="Road Department")

        elif "water" in text or "pipe" in text or "leak" in text:
            return Department.objects.get(name="Water Department")

        elif "electric" in text or "light" in text or "power" in text:
            return Department.objects.get(name="Electricity Department")

        elif "garbage" in text or "waste" in text or "trash" in text:
            return Department.objects.get(name="Sanitation Department")

        else:
            return Department.objects.get(name="General")

    except Department.DoesNotExist:
        return None
# ================= OFFICER ASSIGNMENT ================= #

from django.db.models import Count, Q
from .models import Officer


def assign_officer(department, area):
    """
    Assign complaint to the officer with the least active complaints
    in the same department and area.
    """

    officer = (
        Officer.objects
        .filter(department=department, area=area)
        .annotate(
            active_complaints=Count(
                "complaint",
                filter=Q(complaint__status__in=["Pending", "In Progress"])
            )
        )
        .order_by("active_complaints")
        .first()
    )

    return officer



# ================= ADD COMPLAINT API ================= #

@login_required
def add_complaint_api(request):

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        description = request.POST.get("description")
        photo = request.FILES.get("photo")

        area = Area.objects.get(id=request.POST.get("area"))

        department = detect_department(description)

        officer = assign_officer(department, area)

        Complaint.objects.create(
            name=name,
            phone=phone,
            area=area,
            department=department,
            assigned_officer=officer,
            description=description,
            complaint_photo=photo
        )

        return JsonResponse({
            "status": "success",
            "message": "Complaint submitted successfully"
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

# ================= DASHBOARD ================= #

from django.db.models import Count
from django.db.models.functions import TruncDate

@login_required
def dashboard(request):
    status_filter = request.GET.get('status')

    complaints = Complaint.objects.all().order_by('-created_at')

    if status_filter and status_filter != "All":
        complaints = complaints.filter(status=status_filter)

    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status='Pending').count()
    resolved = Complaint.objects.filter(status='Resolved').count()
    escalated = Complaint.objects.filter(status='Escalated').count()

    from django.db.models import Count
    from django.db.models.functions import TruncDate
    import json

    daily_data = (
        Complaint.objects
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    dates = [str(item['date']) for item in daily_data]
    counts = [item['count'] for item in daily_data]

    return render(request, 'complaints/dashboard.html', {
        'complaints': complaints,
        'total': total,
        'pending': pending,
        'resolved': resolved,
        'escalated': escalated,
        'chart_dates': json.dumps(dates),
        'chart_counts': json.dumps(counts),
        'status_data': json.dumps([pending, resolved, escalated]),
        'selected_status': status_filter or "All"
    })

# ================= HEATMAP ================== #

from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Complaint


def heatmap_data(request):
    """
    Returns complaint counts per area with coordinates
    for heatmap visualization.
    """

    data = (
        Complaint.objects
        .values(
            "area__name",
            "area__city",
            "area__latitude",
            "area__longitude"
        )
        .annotate(
            pending=Count("id", filter=Q(status="Pending")),
            in_progress=Count("id", filter=Q(status="In Progress")),
            resolved=Count("id", filter=Q(status="Resolved"))
        )
    )

    return JsonResponse(list(data), safe=False)

