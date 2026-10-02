"""
Automated Test Suite for Tech Manager & Mentor Module (M-01 to M-12)
PERFORMAX Intern Performance Management System
"""

import os
import sys
import json
import django

# Configure environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from decimal import Decimal
from django.test import Client
from django.utils import timezone
from apps.accounts.models import User, UserRole
from apps.employees.models import EmployeeProfile
from apps.goals.models import Goal, GoalStatus, GoalPriority
from apps.evidence.models import EvidenceSubmission, EvidenceReviewStatus
from apps.feedback.models import Feedback, FeedbackVisibility, FeedbackStatus
from apps.performance.models import (
    PerformanceCycle,
    Appraisal,
    AppraisalStatus,
    EvaluationCriterion,
    TechnicalCapabilityParameter,
    TechnicalCapabilityReview
)

def run_manager_tests():
    client = Client()
    passed = 0
    failed = 0
    total = 22

    def assert_test(cond, code, desc):
        nonlocal passed, failed
        if cond:
            print(f"  [PASS] {code}: {desc}")
            passed += 1
        else:
            print(f"  [FAIL] {code}: {desc}")
            failed += 1

    print("\n" + "=" * 80)
    print(" EXECUTING SOFTWARE TEST SUITE: TECH MANAGER & MENTOR MODULE (M-01 to M-12)")
    print("=" * 80 + "\n")

    # -------------------------------------------------------------
    # 0. AUTHENTICATION SETUP
    # -------------------------------------------------------------
    manager_user = User.objects.filter(role=UserRole.MANAGER).first()
    if not manager_user:
        manager_user = User.objects.create_user(
            username="manager_marcus",
            email="marcus.tech@company.com",
            password="MarcusPassword123!",
            role=UserRole.MANAGER
        )
    else:
        manager_user.set_password("MarcusPassword123!")
        manager_user.save()

    intern_user = User.objects.filter(role=UserRole.INTERN).first()
    if not intern_user:
        intern_user = User.objects.create_user(
            username="intern_alex",
            email="alex.dev@company.com",
            password="AlexPassword123!",
            role=UserRole.INTERN
        )
    else:
        intern_user.set_password("AlexPassword123!")
        intern_user.save()

    # Login Manager
    res = client.post('/api/auth/login/', data=json.dumps({
        'email': manager_user.email,
        'password': 'MarcusPassword123!'
    }), content_type='application/json')
    manager_token = res.json().get('access') or res.json().get('accessToken')
    manager_headers = {'HTTP_AUTHORIZATION': f'Bearer {manager_token}'}

    # Login Intern
    res_int = client.post('/api/auth/login/', data=json.dumps({
        'email': intern_user.email,
        'password': 'AlexPassword123!'
    }), content_type='application/json')
    intern_token = res_int.json().get('access') or res_int.json().get('accessToken')
    intern_headers = {'HTTP_AUTHORIZATION': f'Bearer {intern_token}'}

    # -------------------------------------------------------------
    # TC-M01-01: View Assigned Mentees (Positive)
    # -------------------------------------------------------------
    r = client.get('/api/manager/mentees/', **manager_headers)
    assert_test(r.status_code == 200 and 'data' in r.json(), "TC-M01-01", "M-01 View assigned mentees returns 200 OK with report list")

    # -------------------------------------------------------------
    # TC-M01-02: Search & Filter Mentees (Positive)
    # -------------------------------------------------------------
    r = client.get('/api/manager/mentees/?search=Alex', **manager_headers)
    assert_test(r.status_code == 200 and isinstance(r.json().get('data'), list), "TC-M01-02", "M-01 Filter mentees by query parameter returns filtered list")

    # -------------------------------------------------------------
    # TC-M02-01: Assign New Task to Mentee (Positive)
    # -------------------------------------------------------------
    mentee_profile = EmployeeProfile.objects.filter(user=intern_user).first()
    if not mentee_profile:
        mentee_profile = EmployeeProfile.objects.create(
            user=intern_user,
            employee_code="INT-TEST-001",
            first_name="Alex",
            last_name="Chen",
            manager=manager_user,
            designation="Software Intern",
            employment_status="ACTIVE"
        )
    else:
        mentee_profile.manager = manager_user
        mentee_profile.save()

    r = client.post('/api/manager/tasks/', data=json.dumps({
        'employee_id': str(mentee_profile.id),
        'title': 'Build API Unit Tests',
        'description': 'Implement pytest and Django TestCase for manager views',
        'priority': 'HIGH',
        'target_value': 100,
        'unit': '%'
    }), content_type='application/json', **manager_headers)
    created_task_id = r.json().get('data', {}).get('id') if r.status_code == 201 else None
    assert_test(r.status_code == 201 and created_task_id is not None, "TC-M02-01", "M-02 Assign new task to mentee succeeds with 201 Created")

    # -------------------------------------------------------------
    # TC-M02-02: Assign Task Missing Required Fields (Negative)
    # -------------------------------------------------------------
    r = client.post('/api/manager/tasks/', data=json.dumps({
        'title': ''
    }), content_type='application/json', **manager_headers)
    assert_test(r.status_code == 400, "TC-M02-02", "M-02 Assign task without required title/employee returns 400 Bad Request")

    # -------------------------------------------------------------
    # TC-M03-01: Retrieve Manager Tasks (Positive)
    # -------------------------------------------------------------
    r = client.get('/api/manager/tasks/', **manager_headers)
    assert_test(r.status_code == 200 and len(r.json().get('data', [])) >= 1, "TC-M03-01", "M-03 Retrieve manager tasks returns active task list")

    # -------------------------------------------------------------
    # TC-M03-02: Update Task Status & Completion Percentage (Positive)
    # -------------------------------------------------------------
    if created_task_id:
        r = client.patch(f'/api/manager/tasks/{created_task_id}/', data=json.dumps({
            'status': 'IN_PROGRESS',
            'completion_percentage': 50.0,
            'comment': 'Milestone 1 reached'
        }), content_type='application/json', **manager_headers)
        assert_test(r.status_code == 200 and r.json().get('data', {}).get('completionPercentage') == 50.0, "TC-M03-02", "M-03 Update task status and progress to 50% returns 200 OK")
    else:
        assert_test(False, "TC-M03-02", "M-03 Task not found for update test")

    # -------------------------------------------------------------
    # TC-M04-01: Create Technical Capability Parameter (Positive)
    # -------------------------------------------------------------
    r = client.post('/api/manager/technical-parameters/', data=json.dumps({
        'name': 'API Architecture & Security',
        'category': 'Backend Engineering',
        'description': 'Proficiency in REST/JSON design, JWT validation, and RBAC',
        'benchmark_score': 4.5,
        'weight': 25.0
    }), content_type='application/json', **manager_headers)
    param_id = r.json().get('data', {}).get('id') if r.status_code == 201 else None
    assert_test(r.status_code == 201 and param_id is not None, "TC-M04-01", "M-04 Create technical capability parameter returns 201 Created")

    # -------------------------------------------------------------
    # TC-M04-02: Retrieve Technical Parameters (Positive)
    # -------------------------------------------------------------
    r = client.get('/api/manager/technical-parameters/', **manager_headers)
    assert_test(r.status_code == 200 and len(r.json().get('data', [])) >= 1, "TC-M04-02", "M-04 Retrieve technical parameters returns list of benchmarks")

    # -------------------------------------------------------------
    # TC-M05-01: Save Technical Capability Review (Positive)
    # -------------------------------------------------------------
    if param_id:
        r = client.post('/api/manager/technical-reviews/', data=json.dumps({
            'employee_id': str(mentee_profile.id),
            'status': 'SUBMITTED',
            'reviews': [{
                'parameter_id': param_id,
                'score': 4.5,
                'mentor_assessment': 'Excellent grasp of authentication flows and DRF views.'
            }]
        }), content_type='application/json', **manager_headers)
        assert_test(r.status_code == 200 and r.json().get('code') == 200, "TC-M05-01", "M-05 Submit technical capability review scores returns 200 OK")
    else:
        assert_test(False, "TC-M05-01", "M-05 Parameter missing for review test")

    # -------------------------------------------------------------
    # TC-M05-02: Get Technical Review Dossier for Mentee (Positive)
    # -------------------------------------------------------------
    r = client.get(f'/api/manager/technical-reviews/?employee_id={mentee_profile.id}', **manager_headers)
    assert_test(r.status_code == 200 and r.json().get('data', {}).get('employeeId') == str(mentee_profile.id), "TC-M05-02", "M-05 Fetch mentee technical review dossier returns scored benchmarks")

    # -------------------------------------------------------------
    # TC-M06-01: View Evidence Submissions (Positive)
    # -------------------------------------------------------------
    # Create sample evidence if none exists
    task_obj = Goal.objects.filter(employee=mentee_profile).first()
    evidence_obj = EvidenceSubmission.objects.filter(employee=mentee_profile).first()
    if not evidence_obj:
        evidence_obj = EvidenceSubmission.objects.create(
            employee=mentee_profile,
            goal=task_obj,
            title="GitHub PR Link for Auth Endpoints",
            description="Implemented CustomTokenObtainPairView and tests",
            external_url="https://github.com/company/repo/pull/42",
            review_status=EvidenceReviewStatus.PENDING
        )

    r = client.get('/api/manager/evidence/', **manager_headers)
    assert_test(r.status_code == 200 and len(r.json().get('data', [])) >= 1, "TC-M06-01", "M-06 View evidence submissions returns submitted evidence list")

    # -------------------------------------------------------------
    # TC-M06-02: Make Evidence Review Decision (Positive)
    # -------------------------------------------------------------
    r = client.post(f'/api/manager/evidence/{evidence_obj.id}/decision/', data=json.dumps({
        'status': 'APPROVED',
        'remarks': 'Evidence verified and code reviewed.'
    }), content_type='application/json', **manager_headers)
    assert_test(r.status_code == 200 and r.json().get('data', {}).get('reviewStatus') == 'APPROVED', "TC-M06-02", "M-06 Approve evidence submission updates status to APPROVED")

    # -------------------------------------------------------------
    # TC-M07-01: Give Feedback to Mentee (Positive)
    # -------------------------------------------------------------
    r = client.post('/api/manager/feedback/', data=json.dumps({
        'employee_id': str(mentee_profile.id),
        'feedback_type': 'PRAISE',
        'message': 'Great speed on completing the backend tasks ahead of schedule!',
        'visibility': 'PUBLIC'
    }), content_type='application/json', **manager_headers)
    assert_test(r.status_code == 201 and 'id' in r.json().get('data', {}), "TC-M07-01", "M-07 Give feedback to mentee succeeds with 201 Created")

    # -------------------------------------------------------------
    # TC-M07-02: Give Feedback Missing Message (Negative)
    # -------------------------------------------------------------
    r = client.post('/api/manager/feedback/', data=json.dumps({
        'employee_id': str(mentee_profile.id),
        'message': ''
    }), content_type='application/json', **manager_headers)
    assert_test(r.status_code == 400, "TC-M07-02", "M-07 Give feedback without message returns 400 Bad Request")

    # -------------------------------------------------------------
    # TC-M08-01: Review Employee Feedbacks (Positive)
    # -------------------------------------------------------------
    r = client.get('/api/manager/employee-feedbacks/', **manager_headers)
    assert_test(r.status_code == 200 and isinstance(r.json().get('data'), list), "TC-M08-01", "M-08 Review employee feedbacks returns feedback feed")

    # -------------------------------------------------------------
    # TC-M08-02: Comment on Feedback (Positive)
    # -------------------------------------------------------------
    feedback_item = Feedback.objects.filter(recipient=intern_user).first()
    if feedback_item:
        r = client.post(f'/api/manager/employee-feedbacks/{feedback_item.id}/comment/', data=json.dumps({
            'comment': 'Acknowledged and noted for 1-1 discussion.'
        }), content_type='application/json', **manager_headers)
        assert_test(r.status_code == 201 and r.json().get('code') == 201, "TC-M08-02", "M-08 Add mentor comment to feedback returns 201 Created")
    else:
        assert_test(False, "TC-M08-02", "M-08 Feedback item missing for comment test")

    # -------------------------------------------------------------
    # TC-M09-01: Conduct Performance Review - View Appraisals (Positive)
    # -------------------------------------------------------------
    active_cycle = PerformanceCycle.objects.filter(status='ACTIVE').first() or PerformanceCycle.objects.first()
    appraisal = Appraisal.objects.filter(employee=mentee_profile, cycle=active_cycle).first()
    if not appraisal:
        appraisal = Appraisal.objects.create(
            employee=mentee_profile,
            cycle=active_cycle,
            status=AppraisalStatus.DRAFT,
            reviewer=manager_user
        )

    r = client.get('/api/manager/appraisals/', **manager_headers)
    assert_test(r.status_code == 200 and len(r.json().get('data', [])) >= 1, "TC-M09-01", "M-09 View mentee appraisals for evaluation returns 200 OK")

    # -------------------------------------------------------------
    # TC-M10-01: Save Appraisal Review as Draft (Positive)
    # -------------------------------------------------------------
    crit = EvaluationCriterion.objects.first()
    if not crit:
        crit = EvaluationCriterion.objects.create(
            name="Technical Problem Solving",
            category="CORE",
            weight=Decimal("50.00"),
            target_role=UserRole.INTERN
        )
    crit2 = EvaluationCriterion.objects.exclude(id=crit.id).first()
    if not crit2:
        crit2 = EvaluationCriterion.objects.create(
            name="Execution & Delivery",
            category="CORE",
            weight=Decimal("50.00"),
            target_role=UserRole.INTERN
        )

    r = client.post(f'/api/manager/appraisals/{appraisal.id}/save-draft/', data=json.dumps({
        'reviewer_comments': 'Work in progress draft evaluation.',
        'ratings': [
            {'criterion_id': str(crit.id), 'score': 4.0, 'comments': 'Solid work'},
            {'criterion_id': str(crit2.id), 'score': 4.5, 'comments': 'Fast delivery'}
        ]
    }), content_type='application/json', **manager_headers)
    assert_test(r.status_code == 200 and r.json().get('data', {}).get('status') == 'DRAFT', "TC-M10-01", "M-10 Save incomplete review as draft returns 200 with DRAFT status")

    # -------------------------------------------------------------
    # TC-M11-01: Submit Completed Review (Positive)
    # -------------------------------------------------------------
    r = client.post(f'/api/manager/appraisals/{appraisal.id}/submit/', data=json.dumps({
        'reviewer_comments': 'Final assessment completed. Strong performer.'
    }), content_type='application/json', **manager_headers)
    assert_test(r.status_code == 200 and r.json().get('data', {}).get('status') == 'SUBMITTED', "TC-M11-01", "M-11 Submit finalized review calculates overall score & sets SUBMITTED status")

    # -------------------------------------------------------------
    # TC-M12-01: View Previous / Historical Reviews (Positive)
    # -------------------------------------------------------------
    r = client.get('/api/manager/historical-reviews/', **manager_headers)
    assert_test(r.status_code == 200 and len(r.json().get('data', [])) >= 1, "TC-M12-01", "M-12 View previous reviews archive returns historical records with ratings")

    # -------------------------------------------------------------
    # TC-SEC-01: RBAC Enforcement - Intern Forbidden (Security)
    # -------------------------------------------------------------
    r = client.get('/api/manager/mentees/', **intern_headers)
    assert_test(r.status_code == 403, "TC-SEC-01", "RBAC: Intern accessing manager endpoint is blocked with 403 Forbidden")

    # -------------------------------------------------------------
    # TC-SEC-02: Direct Reports Isolation (Security)
    # -------------------------------------------------------------
    other_manager = User.objects.create_user(
        username="other_mgr",
        email="other.mgr@company.com",
        password="Password123!",
        role=UserRole.MANAGER
    )
    res_other = client.post('/api/auth/login/', data=json.dumps({
        'email': other_manager.email,
        'password': 'Password123!'
    }), content_type='application/json')
    other_token = res_other.json().get('access') or res_other.json().get('accessToken')
    other_headers = {'HTTP_AUTHORIZATION': f'Bearer {other_token}'}

    r_other = client.get('/api/manager/mentees/', **other_headers)
    other_mentees = r_other.json().get('data', [])
    assert_test(
        r_other.status_code == 200 and not any(m['id'] == str(mentee_profile.id) for m in other_mentees),
        "TC-SEC-02",
        "Data Scoping: Other manager cannot see Marcus's assigned direct reports"
    )

    print("\n" + "=" * 80)
    print(f" TEST EXECUTION SUMMARY: {passed}/{total} Passed ({(passed/total)*100:.1f}%) | {failed} Failed")
    print("=" * 80 + "\n")

    return passed == total

if __name__ == '__main__':
    success = run_manager_tests()
    sys.exit(0 if success else 1)
