from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask import g




DATABASE = "users.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # Allows fetching rows as dictionaries
    return g.db



app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


users = {
    "admin@example.com": {"password": "admin123", "role": "admin"},
    "student@example.com": {"password": "student123", "role": "student"}
}

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    election_type = db.Column(db.String(50), nullable=False)
    party = db.Column(db.String(50), nullable=False)
    votes = db.Column(db.Integer, default=0)
    
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)  # Store voter ID
    presidential_vote = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    finance_vote = db.Column(db.Integer, db.ForeignKey('candidate.id'))
    accommodation_vote = db.Column(db.Integer, db.ForeignKey('candidate.id'))


@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        
        if User.query.filter_by(email=email).first():
            return "Email already registered!"
        
        new_user = User(name=name, email=email, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Store user ID in session
            session['role'] = user.role
            session['email'] = user.email  # Store email in session for profile display

            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('student_dashboard'))
        
        return "Invalid email or password. Please try again!"

    return render_template('login.html')



@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('page1.html'))
    return render_template('profile.html', name=session['name'], email=session['email'], role=session['role'])

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    return render_template('student_dashboard.html', user=user)



@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    return render_template('admin_dashboard.html')


@app.route('/add_candidate', methods=['GET', 'POST'])
def add_candidate():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        election_type = request.form['election_type']
        party = request.form['party']

        new_candidate = Candidate(name=name, election_type=election_type, party=party)
        db.session.add(new_candidate)
        db.session.commit()

        return redirect(url_for('add_candidate'))  # Refresh to show success message

    return render_template('add_candidates.html')

@app.route('/candidate_list')
def candidate_list():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    candidates = Candidate.query.all()
    return render_template('candidate_list.html', candidates=candidates)



@app.route('/submit_vote', methods=['POST'])
def submit_vote():
    selected_candidates = {}

    for key in request.form:
        candidate_id = request.form[key]
        candidate = Candidate.query.get(candidate_id)
        if candidate:
            selected_candidates[candidate.election_type] = {
                'name': candidate.name,
                'party': candidate.party
            }

    # Store the selected candidates in session
    session['selected_candidates'] = selected_candidates

    return redirect(url_for('thank_you'))


@app.route('/delete_candidate/<int:candidate_id>', methods=['POST'])
def delete_candidate(candidate_id):
    candidate = Candidate.query.get(candidate_id)
    if candidate:
        db.session.delete(candidate)
        db.session.commit()
    return redirect(url_for('candidate_list'))


@app.route('/results')
def results():
    # Use SQLAlchemy to query the Candidate model
    candidates = Candidate.query.order_by(Candidate.votes.desc()).all()
    return render_template('results.html', candidates=candidates)




@app.route('/thank_you')
def thank_you():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get the user's last vote
    vote = Vote.query.filter_by(user_id=session['user_id']).order_by(Vote.id.desc()).first()
    
    if not vote:
        return redirect(url_for('student_dashboard'))
    
    selected_candidates = {
        'Presidential': Candidate.query.get(vote.presidential_vote),
        'Finance': Candidate.query.get(vote.finance_vote),
        'Accommodation': Candidate.query.get(vote.accommodation_vote)
    }
    
    return render_template('thank_you.html', selected_candidates=selected_candidates)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/voting', methods=['GET', 'POST'])
def voting():
    if request.method == 'POST':
        presidential_vote = request.form.get('presidential_vote')
        finance_vote = request.form.get('finance_vote')
        accommodation_vote = request.form.get('accommodation_vote')

        if not presidential_vote or not finance_vote or not accommodation_vote:
            flash("You must vote for all categories!", "error")
            return redirect(url_for('voting'))

        # Save vote to database
        new_vote = Vote(
            user_id=session.get('user_id', 1),  # Replace with actual session handling
            presidential_vote=int(presidential_vote),
            finance_vote=int(finance_vote),
            accommodation_vote=int(accommodation_vote)
        )
        db.session.add(new_vote)
        db.session.commit()

        flash("Your vote has been submitted successfully!", "success")
        return redirect(url_for('thank_you'))

    # Fetch candidates
    candidates = Candidate.query.all()
    return render_template('voting.html', candidates=candidates)
   



@app.route('/election_type')
def election_type():
    return render_template('election_type.html')


@app.route('/voting_page')
def voting_page():
    return render_template('voting_page.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
