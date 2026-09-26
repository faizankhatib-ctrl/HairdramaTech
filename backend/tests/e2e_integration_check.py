"""
End-to-End Local Integration Verification Script
Tests real interaction between Next.js (port 3000) and Flask (port 5000),
verifying routes, CORS preflight, database seeding, JWT auth, CRUD operations,
assignment, completion, and deletion.
"""

import sys
sys.path.insert(0, '.')

import urllib.request
import urllib.error
import json
import datetime
import jwt
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.task import Task

API_BASE = 'http://localhost:5000'
FRONT_BASE = 'http://localhost:3000'

def run_tests():
    print('=== 1. VERIFY FRONTEND APP ROUTER ROUTES ===')
    for route in ['/', '/login', '/dashboard', '/tasks']:
        url = f'{FRONT_BASE}{route}'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            html = resp.read().decode('utf-8')
            print(f'Route {route} -> HTTP {resp.status} (Length: {len(html)} bytes)')
            assert resp.status == 200
            assert '<html' in html or '<!DOCTYPE html>' in html

    print('\n=== 2. VERIFY CORS PREFLIGHT (localhost:3000 -> localhost:5000) ===')
    preflight_req = urllib.request.Request(
        f'{API_BASE}/api/tasks',
        method='OPTIONS',
        headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Authorization, Content-Type'
        }
    )
    with urllib.request.urlopen(preflight_req) as resp:
        print('OPTIONS /api/tasks -> HTTP', resp.status)
        allow_origin = resp.headers.get('Access-Control-Allow-Origin')
        allow_cred = resp.headers.get('Access-Control-Allow-Credentials')
        print('Access-Control-Allow-Origin:', allow_origin)
        print('Access-Control-Allow-Credentials:', allow_cred)
        assert allow_origin == 'http://localhost:3000', f'Expected http://localhost:3000 but got {allow_origin}'
        assert allow_cred == 'true'

    print('\n=== 3. PREPARE INTEGRATION TEST USERS IN DATABASE ===')
    app = create_app('development')
    with app.app_context():
        alice = User.query.filter_by(email='alice.e2e@hairdrama.com').first()
        if not alice:
            alice = User(
                google_id='google_alice_e2e_12345',
                name='Alice E2E Tester',
                email='alice.e2e@hairdrama.com',
                profile_image='https://lh3.googleusercontent.com/a/default-user'
            )
            db.session.add(alice)

        bob = User.query.filter_by(email='bob.e2e@hairdrama.com').first()
        if not bob:
            bob = User(
                google_id='google_bob_e2e_67890',
                name='Bob E2E Assignee',
                email='bob.e2e@hairdrama.com',
                profile_image='https://lh3.googleusercontent.com/a/default-user-2'
            )
            db.session.add(bob)
        db.session.commit()

        alice_id = str(alice.id)
        bob_id = str(bob.id)
        jwt_secret = app.config['JWT_SECRET_KEY']

    # Generate authentic JWT signed with the server secret
    payload = {
        'sub': alice_id,
        'email': 'alice.e2e@hairdrama.com',
        'name': 'Alice E2E Tester',
        'iat': datetime.datetime.now(datetime.timezone.utc),
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
    }
    token = jwt.encode(payload, jwt_secret, algorithm='HS256')

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Origin': 'http://localhost:3000'
    }

    def api_call(path, method='GET', body=None):
        data = json.dumps(body).encode('utf-8') if body else None
        req = urllib.request.Request(f'{API_BASE}{path}', data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    print('\n=== 4. TEST AUTHENTICATED ENDPOINTS ===')
    # 4. GET /api/auth/me
    status, res = api_call('/api/auth/me')
    print('4. GET /api/auth/me ->', status, res['data']['user']['name'])
    assert status == 200
    assert res['data']['user']['id'] == alice_id

    # 5. GET /api/dashboard/stats
    status, res = api_call('/api/dashboard/stats')
    print('5. GET /api/dashboard/stats ->', status, 'Total tasks:', res['data']['total_tasks'])
    assert status == 200
    assert 'total_tasks' in res['data']
    assert 'completed' in res['data']

    # 6. GET /api/users
    status, res = api_call('/api/users')
    users_list = res['data']['users']
    print(f'6. GET /api/users -> {status}, found {len(users_list)} registered users')
    assert status == 200
    assert len(users_list) >= 2

    # 7. POST /api/tasks (Create Task)
    create_payload = {
        'title': 'Phase 6.5 Integration Test Task',
        'description': 'End-to-end task created via authenticated integration test',
        'priority': 'HIGH',
        'status': 'TODO',
        'assigned_to': bob_id
    }
    status, res = api_call('/api/tasks', method='POST', body=create_payload)
    print('7. POST /api/tasks ->', status, res['message'])
    assert status == 201
    task = res['data']['task']
    task_id = task['id']
    assert task['created_by'] == alice_id
    assert task['assigned_to'] == bob_id

    # 8. PUT /api/tasks/<id> (Edit Task)
    update_payload = {
        'title': 'Phase 6.5 Integration Test Task (Updated)',
        'description': 'Updated description from integration test',
        'priority': 'URGENT',
        'status': 'IN_PROGRESS'
    }
    status, res = api_call(f'/api/tasks/{task_id}', method='PUT', body=update_payload)
    print('8. PUT /api/tasks/<id> ->', status, 'Updated Priority:', res['data']['task']['priority'])
    assert status == 200
    assert res['data']['task']['priority'] == 'URGENT'

    # 9. PATCH /api/tasks/<id>/assign (Reassign Task)
    status, res = api_call(f'/api/tasks/{task_id}/assign', method='PATCH', body={'assigned_to': alice_id})
    print('9. PATCH /api/tasks/<id>/assign ->', status, 'New Assignee:', res['data']['task']['assignee']['name'])
    assert status == 200
    assert res['data']['task']['assigned_to'] == alice_id

    # 10. PATCH /api/tasks/<id>/complete (Mark Completed)
    status, res = api_call(f'/api/tasks/{task_id}/complete', method='PATCH')
    print('10. PATCH /api/tasks/<id>/complete ->', status, 'Status:', res['data']['task']['status'])
    assert status == 200
    assert res['data']['task']['status'] == 'COMPLETED'
    assert res['data']['task']['completed_at'] is not None

    # 11. DELETE /api/tasks/<id> (Delete Task)
    status, res = api_call(f'/api/tasks/{task_id}', method='DELETE')
    print('11. DELETE /api/tasks/<id> ->', status, res['message'])
    assert status == 200

    # 12. Verify deleted task returns 404
    status, res = api_call(f'/api/tasks/{task_id}', method='GET')
    print('12. GET /api/tasks/<id> after deletion ->', status, res['error']['code'])
    assert status == 404

    # 13. Test unauthenticated request returns 401
    unauth_req = urllib.request.Request(f'{API_BASE}/api/tasks')
    try:
        with urllib.request.urlopen(unauth_req) as resp:
            pass
    except urllib.error.HTTPError as e:
        print('13. Unauthenticated GET /api/tasks -> HTTP', e.code)
        assert e.code == 401

    print('\n============================================================')
    print('ALL LOCAL INTEGRATION SCENARIOS TESTED & VERIFIED!')
    print('============================================================')

if __name__ == '__main__':
    run_tests()
