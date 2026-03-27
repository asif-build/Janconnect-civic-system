from datetime import timedelta
from django.utils import timezone
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User

from django.db.models import Count, Q
from django.db.models.functions import TruncDate

from .models import Area, Complaint, Department, Officer
from .models import ComplaintHistory

def detect_category(description):

    text = description.lower()

    if any(word in text for word in ["road", "pothole","street","damage"]):
        return "Infrastructure"

    elif any(word in text for word in ["water", "pipe", "leak","drain","sewage"]):
        return "Water & Utilities"

    elif any(word in text for word in ["electric", "light", "power","outage","electricity"]):
        return "Electricity"

    elif any(word in text for word in ["garbage", "waste", "trash","sanitation","cleanliness","dirty","clean"]):
        return "Sanitation"

    elif any(word in text for word in ["health", "hospital", "clinic","medical"]):
        return "Healthcare"

    else:
        return "Other"
    
    
def assign_officer(category, lat, lng):
    try:
        dept = Department.objects.get(name__iexact=category)

        area = get_nearest_area(float(lat), float(lng))

        print("Detected area:", area)

        officer = Officer.objects.filter(
            department=dept,
            area=area
        ).first()

        if not officer:
            officer = Officer.objects.filter(department=dept).first()

        print("Assigned officer:", officer)

        return officer
    
    except Exception as e:
        print("ASSIGN ERROR:", e)
        return None
         

# ================= PROFILE =========================== #

@login_required
def profile_view(request):
    return render(request, "complaints/profile.html", {
        "user": request.user
    })

# ================= LOGOUT =========================== #

@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("login")



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
    if request.method == "POST":
     try:
        complaint = get_object_or_404(Complaint, id=id)
        complaint.mark_closed()
        return JsonResponse({
           "success": True,
           "status": "closed"
        })
     except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=400)
    return JsonResponse({
         "success": False,
         "error": "Invalid request"
     }, status=400)


# ================= AUTO CLOSE FUNCTION ================= #

def auto_close_resolved():
    now = timezone.now()
    seven_days_ago = now - timedelta(days=7)

    Complaint.objects.filter(
        status="Resolved",
        resolved_at__lt=seven_days_ago
    ).update(status="Closed", closed_at=now)


# ================= LOGIN ================= #

def login_view(request):
    
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "complaints/login.html", {"error": "Invalid credentials"})

    return render(request, "complaints/login.html")


# ================= REGISTER ================= #

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

        user.first_name = phone
        user.save()

        return redirect("login")

    return redirect("login")


# ================= ADD PAGE ================= #

def add_page(request):
    return render(request, "complaints/add_complaint.html")


# ================= DEPARTMENT DETECTION ================= #

def detect_department(description):

    text = description.lower()
    
    print(f"Description: {description}")

    try:

        if any(word in text for word in ["road", "pothole","street","damage"]):
            return Department.objects.filter(name__iexact="Road Department").first()

        elif any(word in text for word in ["water", "pipe", "leak","drain","sewage"]):
            return Department.objects.filter(name__iexact="Water Department").first()

        elif any(word in text for word in ["electric", "light", "power","outage","electricity"]):
            return Department.objects.filter(name__iexact="Electricity Department").first()

        elif any(word in text for word in ["garbage", "waste", "trash","sanitation","cleanliness","dirty","clean"]):
            return Department.objects.filter(name__iexact="Sanitation Department").first()

        else:
            return Department.objects.filter(name__iexact="General").first()   

    except Department.DoesNotExist:
        return None


# =================GET NEAREST AREA ================= #

import math
from.models import Area

def get_nearest_area(lat, lng):
    areas = Area.objects.exclude(latitude=None).exclude(longitude=None)

    nearest_area = None
    min_distance = float("inf")

    for area in areas:
        dist = math.sqrt(
            (lat - area.latitude) ** 2 + 
            (lng - area.longitude) ** 2

        )

        if dist < min_distance:
            min_distance = dist
            nearest_area = area

    return nearest_area


# ================= ADD COMPLAINT API ================= #
from .models import Area
@login_required
def add_complaint_api(request):

    if request.method == "POST":

        name = request.POST.get("name")
        phone = request.POST.get("phone")
        description = request.POST.get("description")
        photo = request.FILES.get("photo")
        lat = request.POST.get("lat")
        lng = request.POST.get("lng")

        try:
            lat = float(lat) if lat else None
            lng = float(lng) if lng else None
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid location"}, status=400)
        
        if lat is None or lng is None:
            return JsonResponse({"status": "error", "message": "Location not selected"}, status=400)

        area = get_nearest_area(float(lat), float(lng))

        if not area:
            print("⚠️ Area not found")
            area = Area.objects.first()  # Fallback to any area

        category = detect_category(description)
        
        dept = None
        
        dept = Department.objects.filter(name__iexact=category).first()

        print("Category:", category)
        print("Dept from DB:", dept)

        if not dept:
            print("⚠️ Department not found, using fallback")
            dept = Department.objects.first()
        

        officer = None

        print("----DEBUG START----")
        print("Category:", category)
        print("Dept:", dept)
        print("Area:", area)

        officers = Officer.objects.all()
        print("All officers:", list(officers.values('id','department__name','area__name')))
        if dept and area:
            officer = Officer.objects.filter(
                department=dept, 
                area = area
            ).first()
        
        if not officer and dept:
            print("⚠️ No exact area match, assigning from department")
            officer = Officer.objects.filter(department=dept).first()

        if not officer:
            print("⚠️ No officer at all, assigning any")
            officer = Officer.objects.first()

        print("Detected category:", category)
        print("Assigned department:", dept)
        print("Area:", area)
        print("Assigned officer:", officer)


        complaint = Complaint.objects.create(
            name=name,
            phone=phone,
            area=area,
            lat=lat,
            lng=lng,
            department = dept,
            category=category,
            assigned_officer=officer,
            description=description,
            complaint_photo=photo
           
        )

        ComplaintHistory.objects.create(
            complaint=complaint,
            status="Pending",
            note="Complaint registered"
        )

        if officer:
            ComplaintHistory.objects.create(
                complaint=complaint,
                status="Assigned  ",
                note=f"Assigned to officer {officer.user.username if officer.user else 'Officer'}"
            )

        return JsonResponse({
            "status": "success",
            "message": "Complaint submitted successfully"
        })

    return JsonResponse({"error": "Invalid request"}, status=400)


# ================= COMPLAINTS API ================= #

def complaints_api(request):
    if request.method == "GET":

     complaints = Complaint.objects.select_related(
        "area",
        "department",
        "assigned_officer__user"
    ).all()

    data = []

    for c in complaints:
        if c.lat is None or c.lng is None:
            continue

        data.append({
            "id": c.id,
            "name": c.name,
            "phone": c.phone,
            "description": c.description,
            "area": c.area.name if c.area else None,
            "department": c.department.name if c.department else None,
            "assigned_officer": c.assigned_officer.user.username if c.assigned_officer else None,
            "status": c.status,
            "category": c.category,
            "lat": c.lat,
            "lng": c.lng,
        })

    return JsonResponse(data, safe=False)


# ================= DASHBOARD ================= #

@login_required
def dashboard(request):

    areas = Area.objects.all()

    status_filter = request.GET.get("status")

    complaints = Complaint.objects.all().order_by("-created_at")

    if status_filter and status_filter != "All":
        complaints = complaints.filter(status=status_filter)

    total = Complaint.objects.count()
    pending = Complaint.objects.filter(status="Pending").count()
    resolved = Complaint.objects.filter(status="Resolved").count()
    escalated = Complaint.objects.filter(status="Escalated").count()

    daily_data = (
        Complaint.objects
        .annotate(date=TruncDate("created_at"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    dates = [str(item["date"]) for item in daily_data]
    counts = [item["count"] for item in daily_data]

    return render(request, "complaints/dashboard.html", {
        "areas": areas,
        "complaints": complaints,
        "total": total,
        "pending": pending,
        "resolved": resolved,
        "escalated": escalated,
        "chart_dates": json.dumps(dates),
        "chart_counts": json.dumps(counts),
        "status_data": json.dumps([pending, resolved, escalated]),
        "selected_status": status_filter or "All"
    })


# ================= HEATMAP ================= #

def heatmap_data(request):
    if request.method != "GET":

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



def submit_complaint(request):
    return render(request, 'complaints/add_complaint.html')