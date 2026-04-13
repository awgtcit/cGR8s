"""
Authentication blueprint — SSO + Direct Login (Auth-first architecture).
Users arrive via launch-token from the Auth Platform,
or log in directly via username/password validated against Auth.
"""
import logging
import os
from flask import Blueprint, redirect, session, flash, current_app, render_template, request, url_for

from app.sdk.auth_client import validate_token as sdk_validate_token, app_login, create_login_challenge, poll_login_challenge, sso_login, poll_sso_challenge

bp = Blueprint('auth', __name__, template_folder='templates')
logger = logging.getLogger(__name__)


def _init_sso_session(user_info, method='sso'):
    """Populate Flask session from validated Auth user info."""
    session['sso_user'] = user_info['user']
    session['sso_roles'] = [r['code'] for r in user_info.get('roles', [])]
    session['sso_permissions'] = user_info.get('permissions', [])
    session['sso_authenticated'] = True
    session.permanent = True
    logger.info("%s login: %s", method.capitalize(), user_info['user'].get('email'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Show login form or process direct login."""
    if session.get('sso_authenticated'):
        return redirect('/')

    auth_base = current_app.config.get(
        'AUTH_APP_URL',
        os.getenv('AUTH_APP_URL', 'http://ams-it-126:5000'),
    )
    app_code = current_app.config.get(
        'AUTH_APP_CODE',
        os.getenv('AUTH_APP_CODE', 'CGRS'),
    )

    if request.method == 'POST':
        login_id = request.form.get('login_id', '').strip()
        password = request.form.get('password', '')

        if not login_id or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('auth/login.html', auth_url=auth_base)

        # Try direct app-login via Auth API
        result = app_login(login_id, password, app_code)

        if result and result.get('status') == 'challenge_created':
            # Mobile confirmation required — redirect to pending page
            return redirect(url_for('auth.pending_confirmation',
                                    challenge_id=result['challenge_id'],
                                    challenge_code=result['challenge_code'],
                                    poll_token=result.get('poll_token', '')))

        if result and result.get('launch_token'):
            # Direct login succeeded — validate token & create session
            user_info = sdk_validate_token(result['launch_token'])
            if user_info:
                _init_sso_session(user_info, method='direct')
                return redirect('/')

        # Login failed
        error_msg = 'Invalid credentials or access denied.'
        if result and result.get('message'):
            error_msg = result['message']
        flash(error_msg, 'error')
        return render_template('auth/login.html', auth_url=auth_base)

    return render_template('auth/login.html', auth_url=auth_base)


@bp.route('/login/pending')
def pending_confirmation():
    """Show pending-confirmation page while waiting for mobile approval."""
    challenge_id = request.args.get('challenge_id', '')
    challenge_code = request.args.get('challenge_code', '')
    poll_token = request.args.get('poll_token', '')
    sso = request.args.get('sso', '')
    if not challenge_id:
        return redirect(url_for('auth.login'))
    return render_template('auth/pending_confirmation.html',
                           challenge_id=challenge_id,
                           challenge_code=challenge_code,
                           poll_token=poll_token,
                           sso=sso)


@bp.route('/login/poll/<challenge_id>')
def poll_challenge(challenge_id):
    """AJAX endpoint — polls login challenge status from Auth API."""
    from flask import jsonify
    poll_token = request.args.get('poll_token', '')
    sso = request.args.get('sso', '')
    if not poll_token:
        return jsonify({'status': 'ERROR', 'message': 'Missing poll token'}), 400

    # Use SSO poll endpoint for SSO challenges, regular for MFA
    if sso:
        result = poll_sso_challenge(challenge_id, poll_token=poll_token)
    else:
        result = poll_login_challenge(challenge_id, poll_token=poll_token)
    if not result:
        return jsonify({'status': 'ERROR', 'message': 'Unable to check status'}), 500

    status = result.get('status', 'PENDING')
    response = {'status': status}

    if status == 'APPROVED' and result.get('launch_token'):
        # Validate the launch token and create session
        user_info = sdk_validate_token(result['launch_token'])
        if user_info:
            _init_sso_session(user_info, method='sso_confirmed' if sso else 'confirmed')
            response['redirect'] = '/'

    return jsonify(response)


@bp.route('/login/sso', methods=['POST'])
def sso_login_route():
    """Handle SSO login via employee ID — creates challenge, sends push to mobile."""
    from flask import jsonify

    employee_id = request.form.get('employee_id', '').strip()
    if not employee_id:
        return jsonify({'success': False, 'message': 'Please enter your Employee ID.'}), 400

    app_code = current_app.config.get(
        'AUTH_APP_CODE',
        os.getenv('AUTH_APP_CODE', 'CGRS'),
    )

    result = sso_login(employee_id, app_code)

    if result and result.get('challenge_id'):
        return jsonify({
            'success': True,
            'redirect': url_for('auth.pending_confirmation',
                                challenge_id=result['challenge_id'],
                                challenge_code=result.get('challenge_code', ''),
                                poll_token=result.get('poll_token', ''),
                                sso='1'),
        })

    error_msg = result.get('message', 'SSO login failed') if result else 'SSO login failed'
    return jsonify({'success': False, 'message': error_msg}), 400


@bp.route('/logout')
def logout():
    """Clear SSO session and redirect to login page."""
    user_email = (session.get('sso_user') or {}).get('email', 'unknown')
    session.clear()
    logger.info('User %s logged out (SSO session cleared)', user_email)
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@bp.route('/login/test-bypass')
def test_login_bypass():
    """DEV ONLY: Bypass auth for Playwright testing. Disabled in production."""
    if not current_app.debug:
        return redirect(url_for('auth.login'))

    from app.config.constants import Permissions
    all_permissions = [p.value for p in Permissions]

    session['sso_user'] = {
        'id': 'test-user-001',
        'email': 'playwright@test.local',
        'first_name': 'Playwright',
        'last_name': 'Tester',
        'display_name': 'Playwright Tester',
    }
    session['sso_roles'] = ['ADMIN', 'USER', 'QA_MANAGER']
    session['sso_permissions'] = all_permissions
    session['sso_authenticated'] = True
    session.permanent = True
    logger.info('DEV test-bypass login activated for Playwright testing')
    return redirect('/')
