"""Populate the database with demo recruiters, job seekers, jobs, applications and messages.

Usage: python manage.py seed_demo
All demo accounts use the password demo12345:
  recruiter: recruiter
  job seeker: seeker
Coordinates are hardcoded so seeding never calls the geocoding API.
"""
from django.core.management.base import BaseCommand

from applications.models import Application, Message, Notification
from jobs.models import JobPosting
from users.models import JobSeekerProfile, RecruiterProfile, User

PASSWORD = "demo12345"

RECRUITERS = [
    ("recruiter", "Riley", "Chen", "Peachtree Labs", "Technical Recruiter"),
    ("hiring_mgr", "Dana", "Brooks", "Midtown Analytics", "Engineering Manager"),
]

JOBS = [
    ("recruiter", "Software Engineer I", "Build and ship features across our Django + React platform used by 2M+ customers.",
     "1100 Peachtree St NE", "Atlanta", "GA", "30309", 33.7866, -84.3833, 95000, 120000, "Python, Django, React, SQL", False, True),
    ("recruiter", "Backend Engineer (New Grad)", "Design REST APIs and data pipelines for our logistics products.",
     "75 5th St NW", "Atlanta", "GA", "30308", 33.7771, -84.3895, 100000, 125000, "Python, PostgreSQL, AWS, Docker", False, False),
    ("recruiter", "Frontend Developer", "Own the UI of our customer dashboard. Strong eye for design required.",
     "3340 Peachtree Rd NE", "Atlanta", "GA", "30326", 33.8466, -84.3689, 85000, 110000, "JavaScript, React, CSS, TypeScript", False, False),
    ("hiring_mgr", "Data Analyst", "Turn product data into insights and dashboards for leadership.",
     "1 Glenlake Pkwy", "Sandy Springs", "GA", "30328", 33.9338, -84.3537, 75000, 95000, "SQL, Python, Tableau", False, True),
    ("hiring_mgr", "Machine Learning Engineer", "Train and deploy recommendation models in production.",
     "2 Alpharetta Pl", "Alpharetta", "GA", "30009", 34.0754, -84.2941, 120000, 150000, "Python, PyTorch, ML, AWS", False, True),
    ("hiring_mgr", "Full-Stack Engineer (Remote)", "Work across the stack on our analytics SaaS. Fully remote within the US.",
     "", "", "", "", None, None, 100000, 130000, "Python, Django, JavaScript, SQL", True, False),
    ("recruiter", "DevOps Engineer", "Own CI/CD, infrastructure-as-code and observability.",
     "200 Galleria Pkwy", "Marietta", "GA", "30339", 33.8836, -84.4652, 105000, 135000, "Docker, Kubernetes, Terraform, AWS", False, False),
]

SEEKERS = [
    ("seeker", "Jamie", "Rivera", "CS new grad from Georgia Tech", "Python, Django, React, SQL",
     "B.S. Computer Science, Georgia Tech", "SWE Intern, Acme Corp (Summer 2025)",
     "JobFinder web app, RAG job-prep chatbot", "Atlanta", "GA", "30332", 33.7756, -84.3963, 15),
    ("priya", "Priya", "Nair", "Data science student", "Python, SQL, Tableau, ML",
     "B.S. Data Science, Georgia State", "Research Assistant", "Sales forecasting model", "Decatur", "GA", "30030", 33.7748, -84.2963, 20),
    ("marcus", "Marcus", "Hill", "Frontend-focused developer", "JavaScript, React, CSS, TypeScript",
     "B.S. Computer Science, Kennesaw State", "Web Dev Intern", "Portfolio site, design system", "Marietta", "GA", "30060", 33.9526, -84.5499, 10),
    ("sofia", "Sofia", "Lopez", "Backend engineer in training", "Python, PostgreSQL, Docker, AWS",
     "B.S. Computer Engineering, Georgia Tech", "Backend Intern, Fintech startup", "Distributed cache", "Sandy Springs", "GA", "30328", 33.9304, -84.3733, 25),
]

APPLICATIONS = [
    ("seeker", "Software Engineer I", "interview"),
    ("seeker", "Backend Engineer (New Grad)", "review"),
    ("seeker", "Full-Stack Engineer (Remote)", "applied"),
    ("priya", "Data Analyst", "offer"),
    ("priya", "Software Engineer I", "applied"),
    ("marcus", "Frontend Developer", "interview"),
    ("marcus", "Software Engineer I", "review"),
    ("sofia", "Backend Engineer (New Grad)", "interview"),
    ("sofia", "DevOps Engineer", "applied"),
    ("sofia", "Software Engineer I", "closed"),
]


def make_user(username, first, last, **flags):
    user, created = User.objects.get_or_create(username=username, defaults={
        "first_name": first, "last_name": last, "email": f"{username}@example.com", **flags,
    })
    if created:
        user.set_password(PASSWORD)
        user.save()
    return user


class Command(BaseCommand):
    help = "Seed the database with demo recruiters, job seekers, jobs, applications and messages."

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin12345")

        recruiters = {}
        for username, first, last, company, title in RECRUITERS:
            user = make_user(username, first, last, is_recruiter=True)
            RecruiterProfile.objects.get_or_create(user=user, defaults={"company_name": company, "title": title})
            recruiters[username] = user

        jobs = {}
        for (owner, title, desc, street, city, state, zip_code, lat, lng,
             lo, hi, skills, remote, visa) in JOBS:
            job, _ = JobPosting.objects.get_or_create(title=title, recruiter=recruiters[owner], defaults={
                "description": desc, "street_address": street, "city": city, "state": state, "zip_code": zip_code,
                "latitude": lat, "longitude": lng, "min_salary": lo, "max_salary": hi,
                "salary_range": f"${lo // 1000}k - ${hi // 1000}k", "skills": skills,
                "is_remote": remote, "visa_sponsorship": visa,
            })
            jobs[title] = job

        seekers = {}
        for (username, first, last, headline, skills, edu, work, projects,
             city, state, zip_code, lat, lng, radius) in SEEKERS:
            user = make_user(username, first, last, is_job_seeker=True)
            JobSeekerProfile.objects.update_or_create(user=user, defaults={
                "headline": headline, "skills": skills, "education": edu, "work_experience": work,
                "projects": projects, "city": city, "state": state, "zip_code": zip_code,
                "location": f"{city}, {state} {zip_code}",
                "latitude": lat, "longitude": lng, "preferred_commute_radius_miles": radius,
                "links": f"https://github.com/{username}",
            })
            seekers[username] = user

        for username, title, status in APPLICATIONS:
            Application.objects.get_or_create(job=jobs[title], applicant=seekers[username],
                                              defaults={"status": status, "note": "Excited about this role!"})

        if not Message.objects.exists():
            recruiter, seeker = recruiters["recruiter"], seekers["seeker"]
            Message.objects.create(
                sender=recruiter, recipient=seeker, job=jobs["Software Engineer I"],
                subject="Interview invitation: Software Engineer I",
                body="Hi Jamie, thanks for applying! We'd love to schedule a 45-minute technical interview next week.",
            )
            Message.objects.create(
                sender=recruiter, recipient=seekers["sofia"], job=jobs["Backend Engineer (New Grad)"],
                subject="Next steps", body="Hi Sofia, your application moved to the interview stage.",
            )
            Notification.objects.create(recipient=seeker, message="Your application for Software Engineer I moved to Interview.")
            Notification.objects.create(recipient=seeker, message="New message from Riley Chen (Peachtree Labs).")

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {JobPosting.objects.count()} jobs, {len(seekers)} job seekers, {Application.objects.count()} applications. "
            f"Log in as 'seeker' or 'recruiter' with password {PASSWORD}."
        ))
