import time
import os
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.exc import StaleDataError
from flask import Flask, render_template, flash, redirect, url_for, session, request
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Consumer, Company, Mediator, Case, Evidence, Comment, Support, Admin
from flask_migrate import Migrate

app = Flask(__name__)
app.secret_key = 'mysecretkey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Directory to store uploaded evidence files
db.init_app(app)

migrate = Migrate(app, db)

@app.route('/submit_case', methods=['GET', 'POST'])
def submit_case():
    if 'logged_in' in session and session['user_type'] == 'Consumer':
        if request.method == 'POST':
            brand_name = request.form.get('brand_name')
            company_id = request.form.get('company_id')
            title = request.form.get('title')
            description = request.form.get('description')
            evidence = request.files.getlist('evidence')

            if not brand_name and not company_id:
                flash('Please enter a brand name or select a company.', 'error')
                return redirect(url_for('submit_case'))

            if not title:
                flash('Please enter a title for the case.', 'error')
                return redirect(url_for('submit_case'))

            if not description:
                flash('Please enter a description for the case.', 'error')
                return redirect(url_for('submit_case'))

            if not evidence:
                flash('Please upload at least one evidence file.', 'error')
                return redirect(url_for('submit_case'))

            if company_id:
                company = Company.query.get(company_id)
                brand_name = company.username
            else:
                brand_name = brand_name

            case = Case(brand_name=brand_name, title=title, description=description,
                        consumer_id=session['user_id'], status='Submitted')
            db.session.add(case)
            db.session.commit()

            for file in evidence:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                evidence = Evidence(filename=filename, case_id=case.id)
                db.session.add(evidence)

            db.session.commit()

            flash('Your case has been submitted for review.', 'success')
            return redirect(url_for('case_management'))

        companies = Company.query.all()
        return render_template('submit_case.html', companies=companies)
    else:
        flash('Please log in as a consumer to submit a case.', 'info')
        return redirect(url_for('login'))


@app.route('/delete_case/<int:case_id>', methods=['POST'])
def delete_case(case_id):
    if 'logged_in' in session:
        case = Case.query.get_or_404(case_id)
        if case.consumer_id == session['user_id'] or session['user_type'] == 'Admin':
            # Delete all related comments
            comments = Comment.query.filter_by(case_id=case_id).all()
            for comment in comments:
                db.session.delete(comment)

            # Delete all related evidence
            evidence = Evidence.query.filter_by(case_id=case_id).all()
            for ev in evidence:
                db.session.delete(ev)

            # Delete all related supports
            supports = Support.query.filter_by(case_id=case_id).all()
            for support in supports:
                db.session.delete(support)

            # Now delete the case itself
            db.session.delete(case)
            db.session.commit()
            flash('Case deleted successfully.', 'success')
        else:
            flash('You are not authorized to delete this case.', 'error')
    else:
        flash('Please log in to delete comments.', 'error')
    return redirect(url_for('index'))


@app.route('/case_management', methods=['GET', 'POST'])
def case_management():
    if 'logged_in' in session and session['user_type'] == 'Consumer':
        if request.method == 'POST':
            brand_name = request.form['brand_name']
            company_id = request.form.get('company_id')
            title = request.form['title']
            description = request.form['description']
            evidence = request.files.getlist('evidence')

            if company_id:
                company = Company.query.get(company_id)
                brand_name = company.username
            else:
                brand_name = brand_name

            case = Case(brand_name=brand_name, title=title, description=description,
                        consumer_id=session['user_id'], status='Submitted')
            db.session.add(case)
            db.session.commit()

            for file in evidence:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                evidence = Evidence(filename=filename, case_id=case.id)
                db.session.add(evidence)

            db.session.commit()

            flash('Your case has been submitted for review.', 'success')
            return redirect(url_for('case_management'))

        cases = Case.query.filter_by(consumer_id=session['user_id']).all()
        companies = Company.query.all()
        return render_template('case_management.html', cases=cases, companies=companies)
    else:
        flash('Please log in as a consumer to access case management.', 'info')
        return redirect(url_for('login'))


@app.route('/case_details/<int:case_id>', methods=['GET', 'POST'])
def case_details(case_id):
    case = Case.query.options(db.joinedload(Case.comments)).get_or_404(case_id)
    evidence = Evidence.query.filter_by(case_id=case_id).all()
    comments = Comment.query.filter_by(case_id=case_id).order_by(Comment.created_at.desc()).all()
    supports = case.supports

    if 'logged_in' in session:
        if session['user_type'] == 'Consumer' and case.consumer_id == session['user_id'] and case.status == 'Resolved':
            if request.method == 'POST' and 'consumer_message' in request.form:
                consumer_message = request.form['consumer_message']
                message_color = request.form['message_color']
                case.consumer_message = consumer_message
                case.message_color = message_color
                case.status = 'Closed'
                db.session.commit()
                flash('Your message has been added and the case is now closed.', 'success')
                return redirect(url_for('case_details', case_id=case_id))

        if request.method == 'POST' and 'content' in request.form:
            content = request.form['content']
            comment = Comment(content=content, user_id=session['user_id'], case_id=case_id)
            db.session.add(comment)
            db.session.commit()
            flash('Your comment has been submitted.', 'success')
            return redirect(url_for('case_details', case_id=case_id))

    return render_template('case_details.html', case=case, evidence=evidence, comments=comments, supports=supports)
@app.route('/support_case/<int:case_id>')
def support_case(case_id):
    if 'logged_in' in session and (session['user_type'] == 'Mediator' or session['user_type'] == 'Consumer'):
        existing_support = Support.query.filter_by(user_id=session['user_id'], case_id=case_id).first()
        if existing_support:
            flash('You have already supported this case.', 'info')
        else:
            support = Support(user_id=session['user_id'], case_id=case_id)
            db.session.add(support)
            db.session.commit()
            flash('You have supported this case.', 'success')
    else:
        flash('Please log in as a mediator or consumer to support a case.', 'info')

    return redirect(url_for('case_details', case_id=case_id))



def delete_comment_with_retry(comment_id, max_retries=3, backoff_factor=0.1):
    retry_count = 0
    while retry_count < max_retries:
        try:
            with db.session.begin_nested():
                comment = Comment.query.get(comment_id)
                if comment:
                    db.session.delete(comment)
                else:
                    return False
            db.session.commit()
            return True
        except OperationalError as e:
            db.session.rollback()
            retry_count += 1
            if retry_count >= max_retries:
                raise
            sleep_time = backoff_factor * (2 ** (retry_count - 1))
            time.sleep(sleep_time)
        except StaleDataError:
            db.session.rollback()
            return False

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    if 'logged_in' in session:
        comment = Comment.query.get_or_404(comment_id)
        if comment.is_owner(session['user_id']):
            case_id = comment.case_id
            success = delete_comment_with_retry(comment_id)
            if success:
                flash('Your comment has been deleted.', 'success')
            else:
                flash('The comment has already been deleted.', 'info')
            return redirect(url_for('case_details', case_id=case_id))
        else:
            flash('You are not authorized to delete this comment.', 'error')
    else:
        flash('Please log in to delete comments.', 'error')
    return redirect(url_for('case_details', case_id=comment.case_id))

@app.route("/")
def index():
    approved_cases = Case.query.filter(Case.status.in_(['Approved', 'Resolved', 'Closed'])).order_by(Case.created_at.desc()).all()
    for case in approved_cases:
        case.comment_count = len(case.comments)
        case.support_count = len(case.supports)
    companies = Company.query.all()

    return render_template("index.html", cases=approved_cases, companies=companies)
@app.route("/search_cases")
def search_cases():
    company = request.args.get('company')
    keyword = request.args.get('keyword')
    status = request.args.get('status')
    sort_by = request.args.get('sort_by')

    query = Case.query.filter(Case.status != 'Rejected')  # Exclude rejected cases

    if company:
        query = query.filter(Case.brand_name == company)
    if keyword:
        query = query.filter(Case.title.ilike(f'%{keyword}%') | Case.description.ilike(f'%{keyword}%'))
    if status:
        query = query.filter(Case.status == status)

    if sort_by == 'support_count':
        query = query.outerjoin(Support).group_by(Case.id).order_by(db.func.count(Support.id).desc())
    elif sort_by == 'comment_count':
        query = query.outerjoin(Comment).group_by(Case.id).order_by(db.func.count(Comment.id).desc())
    else:
        query = query.order_by(Case.created_at.desc())

    cases = query.all()
    companies = Company.query.all()

    return render_template("search_results.html", cases=cases, companies=companies,
                           selected_company=company, selected_keyword=keyword,
                           selected_status=status, selected_sort_by=sort_by)



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        uname = request.form["uname"]
        passw = request.form["passw"]

        login = User.query.filter_by(username=uname).first()
        if login and check_password_hash(login.password, passw):
            session['logged_in'] = True
            session['user_type'] = login.user_type
            session['username'] = login.username
            session['user_id'] = login.id  # Store the user's ID in the session

            flash('Login successful.', 'success')
            return redirect(url_for("index"))
        else:
            flash('Invalid username or password.')
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        uname = request.form.get('uname')
        mail = request.form.get('mail')
        passw = request.form.get('passw')
        confirm_passw = request.form.get('confirm_passw')
        user_type = request.form.get('user_type')

        if not uname:
            flash('Username is required.', 'error')
            return redirect(url_for('register'))


        existing_user = User.query.filter_by(username=uname).first()
        if existing_user:
            flash('Username already exists. Please choose a different username.')
            return redirect(url_for('register'))

        existing_email = User.query.filter_by(email=mail).first()
        if existing_email:
            flash('Email already exists. Please use a different email.')
            return redirect(url_for('register'))

        # Password strength validation
        if len(passw) < 8 or not any(char.isdigit() for char in passw) or not any(char.isupper() for char in passw) or not any(char.islower() for char in passw) or not any(char in '!@#$%^&*(.)' for char in passw):
            flash('Password must be at least 8 characters long and include uppercase letters, lowercase letters, numbers, and special characters.', 'error')
            return redirect(url_for('register'))

        if passw != confirm_passw:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('register'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(passw)

        if user_type == 'Consumer':
            user = Consumer(username=uname, email=mail, password=hashed_password)
        elif user_type == 'Company':
            user = Company(username=uname, email=mail, password=hashed_password)
        elif user_type == 'Mediator':
            user = Mediator(username=uname, email=mail, password=hashed_password)
        else:
            flash('Invalid user type.', 'error')
            return redirect(url_for('register'))

        db.session.add(user)
        db.session.commit()

        flash('Registration successful. Please login.')
        return redirect(url_for("login"))

    return render_template("register.html")



@app.route('/mediators')
def mediators():
    mediators_list = Mediator.query.all()
    return render_template('mediators.html', mediators=mediators_list)


@app.route('/mediator_profile', methods=['GET', 'POST'])
def mediator_profile():
    if 'logged_in' in session and session['user_type'] == 'Mediator':
        username = session['username']
        mediator = Mediator.query.filter_by(username=username).first()

        if request.method == 'POST':
            biography = request.form.get('biography')

            if 'profile_photo' in request.files:
                profile_photo = request.files['profile_photo']
                if profile_photo.filename != '':
                    filename = secure_filename(profile_photo.filename)
                    profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    mediator.profile_photo = filename

            mediator.biography = biography
            db.session.commit()

            flash('Profile updated successfully.', 'success')
            return redirect(url_for('mediator_profile'))

        return render_template('mediator_profile.html', mediator=mediator)
    else:
        flash('Please log in as a mediator to access the profile page.', 'info')
        return redirect(url_for('login'))

@app.route('/mediator/<username>')
def mediator_details(username):
    mediator = Mediator.query.filter_by(username=username).first()
    if mediator and mediator.user_type == 'Mediator':
        return render_template('mediator_details.html', mediator=mediator)
    else:
        flash('Mediator not found.', 'error')
        return redirect(url_for('mediators'))


@app.route('/company_profile', methods=['GET', 'POST'])
def company_profile():
    if 'logged_in' in session and session['user_type'] == 'Company':
        company_id = session['user_id']
        company = Company.query.get(company_id)
        cases = Case.query.filter_by(brand_name=company.username).all()
        print("Company ID:", company_id)
        print("Cases:", cases)
        if request.method == 'POST':
            if 'profile_photo' in request.files:
                profile_photo = request.files['profile_photo']
                if profile_photo:
                    filename = secure_filename(profile_photo.filename)
                    profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    company.profile_photo = filename

            if 'introduction' in request.form:
                company.introduction = request.form['introduction']

            if 'case_id' in request.form:
                case_id = request.form['case_id']
                case = Case.query.get(case_id)
                if case and case.brand_name == company.username:
                    case.status = 'Resolved'
                    flash('Case status updated successfully.', 'success')
                else:
                    flash('Invalid case.', 'error')

            db.session.commit()

        return render_template('company_profile.html', company=company, cases=cases)
    else:
        flash('Please log in as a company to access the profile page.', 'error')
        return redirect(url_for('login'))


@app.route('/company/<username>')
def company_details(username):
    company = Company.query.filter_by(username=username).first()
    if company:
        cases = Case.query.filter_by(brand_name=company.username).all()
        return render_template('company_details.html', company=company, cases=cases)
    else:
        flash('Company not found.', 'error')
        return redirect(url_for('index'))


with app.app_context():
    db.create_all()

    admin_username = 'Admin1'
    admin_email = 'admin1@gmail.com'
    admin_password = generate_password_hash('123', method='pbkdf2:sha256')

    # Check if the admin user already exists
    existing_admin = Admin.query.filter_by(email=admin_email).first()

    if not existing_admin:
        # Create a new admin user
        admin_user = Admin(username=admin_username, email=admin_email, password=admin_password)
        db.session.add(admin_user)
        db.session.commit()
        print('Admin user created successfully.')
    else:
        print('Admin user already exists.')
app.run(debug=True)
if __name__ == "__main__":
    pass

