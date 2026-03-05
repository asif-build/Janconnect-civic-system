# JanConnect

JanConnect is a smart civic complaint management platform that connects citizens with government departments for transparent issue reporting, automated officer assignment, and real-time resolution tracking.

---

## 🚀 Problem

Citizens often struggle to report civic issues such as potholes, garbage, water leakage, or streetlight failures.  
Existing systems lack transparency, tracking, and accountability.

---

## 💡 Solution

JanConnect provides a centralized platform where citizens can:

• Submit complaints with photos  
• Automatically route issues to the correct department  
• Track complaint progress in real time  
• View problem hotspots using heatmaps  
• Ensure transparency through proof-based resolution

---

## ⚙️ Features

### 📝 Complaint Submission
Citizens can submit issues with description, category, location, and photo evidence.

### 🏛 Department Detection
The system automatically detects the relevant department based on complaint description.

### 👮 Officer Assignment
Complaints are automatically assigned to government officers responsible for that area.

### ⚖️ Workload Balancing
The system assigns complaints to the officer with the least active workload.

### ⏱ SLA Deadline Tracking
Each complaint has a resolution deadline based on its category.

### 📊 Heatmap Analytics
Visualizes complaint hotspots using geographic data.

### 📸 Resolution Proof
Officers must upload photo evidence when marking an issue as resolved.

### 📜 Complaint History
Every status change is recorded to maintain transparency.

---

## 🏗 System Architecture
Citizen → Submit Complaint
↓
Department Detection
↓
Officer Assignment
↓
Workload Balancing
↓
Complaint Tracking
↓
Resolution Proof
↓
Citizen Feedback

---

## 🛠 Tech Stack

Backend  
• Python  
• Django  
• MySQL  

Frontend  
• HTML  
• CSS  
• JavaScript  
• Chart.js  

Other  
• Heatmap visualization  
• Image upload system  
• REST-style APIs

---

## 📊 Key Modules

| Module | Description |
|------|-------------|
| Complaint Management | Handles submission, tracking, and resolution |
| Officer Management | Assigns complaints based on department and area |
| Heatmap Engine | Visualizes complaint density across locations |
| SLA Engine | Tracks deadlines and escalates overdue complaints |
| Resolution Verification | Requires photo proof before closing complaints |

---

## 📂 Project Structure
janconnect/
│
├── complaints/
│ ├── models.py
│ ├── views.py
│ ├── urls.py
│ └── templates/
│
├── static/
├── media/
├── manage.py

---

## 🔐 Transparency Features

• Photo proof for complaints  
• Photo proof for resolution  
• Complaint history timeline  
• Officer accountability system

---

## 🌍 Future Improvements

• AI complaint categorization  
• Mobile application  
• Real-time map heatmap  
• SMS notifications  
• Government dashboard analytics

---

## 🏆 Hackathon

Built for **India Innovates 2026 Hackathon**

---

## 👨‍💻 Author

**Asif**

---
