from flask import Flask, request, flash, render_template, session, abort, redirect, url_for
from models import Case, db, Evidence, Admin
from werkzeug.security import check_password_hash

admin_app = Flask(__name__)
admin_app.secret_key = 'myadminsecretkey123'
admin_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db.init_app(admin_app)

@admin_app.route('/')
def admin_index():
    if 'logged_in' in session and session['user_type'] == 'Admin':
        return render_template('admin_index.html')
    else:
        return redirect(url_for('admin_login'))


@admin_app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin_user = Admin.query.filter_by(username=username).first()

        if admin_user and check_password_hash(admin_user.password, password):
            session['logged_in'] = True
            session['user_type'] = 'Admin'
            session['username'] = admin_user.username
            flash('Login successful.', 'success')
            return redirect(url_for('admin_index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('admin_login.html')
@admin_app.route('/review_cases')
def review_cases():
    if 'logged_in' in session and session['user_type'] == 'Admin':
        pending_cases = Case.query.filter_by(status='Submitted').all()
        for case in pending_cases:
            case.evidences = Evidence.query.filter_by(case_id=case.id).all()
        return render_template('review_cases.html', cases=pending_cases)
    else:
        abort(403)  # Forbidden access

@admin_app.route('/approve_case/<int:case_id>')
def approve_case(case_id):
    if 'logged_in' in session and session['user_type'] == 'Admin':
        case = Case.query.get_or_404(case_id)
        case.status = 'Approved'
        db.session.commit()

        flash('Case approved.', 'success')
        return redirect(url_for('review_cases'))
    else:
        abort(403)  # Forbidden access

@admin_app.route('/reject_case/<int:case_id>')
def reject_case(case_id):
    if 'logged_in' in session and session['user_type'] == 'Admin':
        case = Case.query.get_or_404(case_id)
        case.status = 'Rejected'
        db.session.commit()

        flash('Case rejected.', 'info')
        return redirect(url_for('review_cases'))
    else:
        abort(403)  # Forbidden access
@admin_app.route('/admin_logout')
def admin_logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))
if __name__ == '__main__':
    admin_app.run(debug=True, port=5001)
