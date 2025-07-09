from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import pickle
import pandas as pd
import re
from datetime import datetime
import uuid
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)  # New field
    plan = db.Column(db.String(20), nullable=False, default='free')  # New field
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    survey_responses = db.relationship('SurveyResponse', backref='user', lazy=True, cascade="all, delete-orphan")
    clusters = db.relationship('UserCluster', backref='user', lazy=True, cascade="all, delete-orphan")

class SurveyResponse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_1 = db.Column(db.Text, nullable=False)  # Primary health goal
    question_2 = db.Column(db.Text, nullable=False)  # Physical activity level
    question_3 = db.Column(db.Text, nullable=False)  # Sleep quality
    question_4 = db.Column(db.Text, nullable=False)  # Mental well-being
    question_5 = db.Column(db.Text, nullable=False)  # Dietary habits
    question_6 = db.Column(db.Text, nullable=False)  # Medical visits frequency
    question_7 = db.Column(db.Text, nullable=False)  # Travel plans
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserCluster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cluster_name = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Float, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Cluster Assignment Logic
class ClusterAssigner:
    def __init__(self):
        self.clusters = {
            'Mental Health': {
                'conditions': {
                    'survey': ['q1_mental', 'q4_struggling'],
                    'diagnoses': ['Depression', 'Anxiety', 'Bipolar', 'PTSD']
                }
            },
            'Fitness Centric': {
                'conditions': {
                    'survey': ['q1_health_performance', 'q2_moderately_active', 'q2_very_active', 'q5_balanced'],
                    'diagnoses': ['Patellar Tendinopathy', 'Shin Splints'],
                    'medications': ['Protein Supplement']
                }
            },
            'Maternal Health': {
                'conditions': {
                    'maternal': ['is_pregnant']
                }
            },
            'Sleep Health': {
                'conditions': {
                    'survey': ['q1_sleep', 'q3_poor', 'q3_fair'],
                    'diagnoses': ['Insomnia', 'Obstructive Sleep Apnea', 'Restless Legs Syndrome']
                }
            },
            'Preventive Health': {
                'conditions': {
                    'survey': ['q1_preventing', 'q6_frequently', 'q6_few_times']
                }
            },
            'Senior Care': {
                'conditions': {
                    'age': 65
                }
            }
        }
    
    def assign_clusters(self, survey_data, medical_data=None):
        """Assign clusters based on survey responses and medical data"""
        assigned_clusters = []
        
        # Get Question 1 responses (user's primary health goals)
        q1_responses = survey_data.get('question_1', '').lower()
        
        # HIGH PRIORITY: Check Question 1 first (user's stated intentions)
        # Mental Health Cluster - if user explicitly mentions mental health goals
        if any(goal in q1_responses for goal in ['mental well-being', 'stress', 'anxiety', 'depression']):
            assigned_clusters.append(('Mental Health', 0.95))  # Higher confidence for user-stated goals
        
        # Fitness Centric Cluster - if user mentions health and performance
        if 'health and performance' in q1_responses:
            assigned_clusters.append(('Fitness Centric', 0.95))  # Higher confidence for user-stated goals
        
        # Sleep Health Cluster - if user mentions sleep improvement
        if 'sleep' in q1_responses:
            assigned_clusters.append(('Sleep Health', 0.95))  # Higher confidence for user-stated goals
        
        # Maternal Health Cluster - if user mentions maternal/child health
        if 'maternal' in q1_responses or 'child health' in q1_responses:
            assigned_clusters.append(('Maternal Health', 0.95))  # Higher confidence for user-stated goals
        
        # Preventive Health Cluster - if user mentions preventing future issues
        if 'preventing' in q1_responses or 'biohacking' in q1_responses:
            assigned_clusters.append(('Preventive Health', 0.95))  # Higher confidence for user-stated goals
        
        # Senior Care Cluster - if user mentions age-related concerns
        if 'age-related' in q1_responses or 'seniors' in q1_responses:
            assigned_clusters.append(('Senior Care', 0.95))  # Higher confidence for user-stated goals
        
        # MEDIUM PRIORITY: Check medical records for supporting evidence
        # Mental Health Cluster - medical record evidence
        if self._check_mental_health_medical(medical_data):
            if not any('Mental Health' in cluster for cluster in assigned_clusters):
                assigned_clusters.append(('Mental Health', 0.85))
        
        # Fitness Centric Cluster - medical record evidence
        if self._check_fitness_centric_medical(medical_data):
            if not any('Fitness Centric' in cluster for cluster in assigned_clusters):
                assigned_clusters.append(('Fitness Centric', 0.85))
        
        # Maternal Health Cluster - medical record evidence
        if self._check_maternal_health(medical_data):
            if not any('Maternal Health' in cluster for cluster in assigned_clusters):
                assigned_clusters.append(('Maternal Health', 0.90))
        
        # Sleep Health Cluster - medical record evidence
        if self._check_sleep_health_medical(medical_data):
            if not any('Sleep Health' in cluster for cluster in assigned_clusters):
                assigned_clusters.append(('Sleep Health', 0.85))
        
        # Senior Care Cluster - medical record evidence
        if self._check_senior_care(medical_data):
            if not any('Senior Care' in cluster for cluster in assigned_clusters):
                assigned_clusters.append(('Senior Care', 0.90))
        
        # LOW PRIORITY: Check other survey questions for additional context
        # Only if no clusters assigned yet or for additional support
        if not assigned_clusters:
            # Fallback to other questions if no clear Q1 match
            if self._check_mental_health_fallback(survey_data):
                assigned_clusters.append(('Mental Health', 0.75))
            if self._check_fitness_centric_fallback(survey_data):
                assigned_clusters.append(('Fitness Centric', 0.75))
            if self._check_sleep_health_fallback(survey_data):
                assigned_clusters.append(('Sleep Health', 0.75))
            if self._check_preventive_health_fallback(survey_data):
                assigned_clusters.append(('Preventive Health', 0.75))
        
        return assigned_clusters
    
    def _check_mental_health(self, survey_data, medical_data):
        """Check if user qualifies for Mental Health cluster"""
        # Check survey responses
        q1_mental = 'mental well-being' in survey_data.get('question_1', '').lower()
        q4_struggling = 'struggling' in survey_data.get('question_4', '').lower()
        
        # Check medical records for depression
        depression_in_records = False
        if medical_data and 'diagnoses' in medical_data:
            diagnoses = medical_data['diagnoses']
            if isinstance(diagnoses, pd.DataFrame):
                depression_in_records = diagnoses['diagnosis_name'].str.contains('Depression', case=False, na=False).any()
        
        return (q1_mental or q4_struggling) or depression_in_records
    
    def _check_fitness_centric(self, survey_data, medical_data):
        """Check if user qualifies for Fitness Centric cluster"""
        # Check survey responses
        q1_performance = 'health and performance' in survey_data.get('question_1', '').lower()
        q2_active = any(level in survey_data.get('question_2', '').lower() 
                       for level in ['moderately active', 'very active'])
        q5_balanced = 'balanced' in survey_data.get('question_5', '').lower()
        
        # Check medical records
        fitness_conditions = False
        protein_supplement = False
        
        if medical_data:
            if 'diagnoses' in medical_data and isinstance(medical_data['diagnoses'], pd.DataFrame):
                diagnoses = medical_data['diagnoses']
                fitness_conditions = (diagnoses['diagnosis_name'].str.contains('Patellar Tendinopathy|Shin Splints', 
                                                                              case=False, na=False).any())
            
            if 'medications' in medical_data and isinstance(medical_data['medications'], pd.DataFrame):
                medications = medical_data['medications']
                protein_supplement = medications['medication_name'].str.contains('Protein Supplement', 
                                                                                case=False, na=False).any()
        
        return (q1_performance and q2_active) or fitness_conditions or protein_supplement
    
    def _check_maternal_health(self, medical_data):
        """Check if user qualifies for Maternal Health cluster"""
        if medical_data and 'maternal_health' in medical_data:
            maternal = medical_data['maternal_health']
            if isinstance(maternal, pd.DataFrame):
                return maternal['is_pregnant'].any()
        return False
    
    def _check_sleep_health(self, survey_data, medical_data):
        """Check if user qualifies for Sleep Health cluster"""
        # Check survey responses
        q1_sleep = 'sleep' in survey_data.get('question_1', '').lower()
        q3_poor = any(quality in survey_data.get('question_3', '').lower() 
                     for quality in ['poor', 'fair'])
        
        # Check medical records
        sleep_conditions = False
        if medical_data and 'diagnoses' in medical_data:
            diagnoses = medical_data['diagnoses']
            if isinstance(diagnoses, pd.DataFrame):
                sleep_conditions = diagnoses['diagnosis_name'].str.contains('Insomnia|Sleep Apnea|Restless Legs', 
                                                                          case=False, na=False).any()
        
        return (q1_sleep and q3_poor) or sleep_conditions
    
    def _check_preventive_health(self, survey_data):
        """Check if user qualifies for Preventive Health cluster"""
        q1_preventing = 'preventing' in survey_data.get('question_1', '').lower()
        q6_frequent = any(freq in survey_data.get('question_6', '').lower() 
                         for freq in ['frequently', 'few times'])
        
        return q1_preventing or q6_frequent
    
    def _check_senior_care(self, medical_data):
        """Check if user qualifies for Senior Care cluster"""
        if medical_data and 'patients' in medical_data:
            patients = medical_data['patients']
            if isinstance(patients, pd.DataFrame):
                return (patients['age'] > 65).any()
        return False
    
    # New helper methods for medical record evidence
    def _check_mental_health_medical(self, medical_data):
        """Check medical records for mental health evidence"""
        if medical_data and 'diagnoses' in medical_data:
            diagnoses = medical_data['diagnoses']
            if isinstance(diagnoses, pd.DataFrame):
                return diagnoses['diagnosis_name'].str.contains('Depression|Anxiety|Bipolar|PTSD', case=False, na=False).any()
        return False
    
    def _check_fitness_centric_medical(self, medical_data):
        """Check medical records for fitness evidence"""
        fitness_conditions = False
        protein_supplement = False
        
        if medical_data:
            if 'diagnoses' in medical_data and isinstance(medical_data['diagnoses'], pd.DataFrame):
                diagnoses = medical_data['diagnoses']
                fitness_conditions = diagnoses['diagnosis_name'].str.contains('Patellar Tendinopathy|Shin Splints', case=False, na=False).any()
            
            if 'medications' in medical_data and isinstance(medical_data['medications'], pd.DataFrame):
                medications = medical_data['medications']
                protein_supplement = medications['medication_name'].str.contains('Protein Supplement', case=False, na=False).any()
        
        return fitness_conditions or protein_supplement
    
    def _check_sleep_health_medical(self, medical_data):
        """Check medical records for sleep health evidence"""
        if medical_data and 'diagnoses' in medical_data:
            diagnoses = medical_data['diagnoses']
            if isinstance(diagnoses, pd.DataFrame):
                return diagnoses['diagnosis_name'].str.contains('Insomnia|Sleep Apnea|Restless Legs', case=False, na=False).any()
        return False
    
    # Fallback methods for other survey questions
    def _check_mental_health_fallback(self, survey_data):
        """Check other questions for mental health indicators"""
        q4_struggling = 'struggling' in survey_data.get('question_4', '').lower()
        return q4_struggling
    
    def _check_fitness_centric_fallback(self, survey_data):
        """Check other questions for fitness indicators"""
        q2_active = any(level in survey_data.get('question_2', '').lower() 
                       for level in ['moderately active', 'very active'])
        q5_balanced = 'balanced' in survey_data.get('question_5', '').lower()
        return q2_active and q5_balanced
    
    def _check_sleep_health_fallback(self, survey_data):
        """Check other questions for sleep indicators"""
        q3_poor = any(quality in survey_data.get('question_3', '').lower() 
                     for quality in ['poor', 'fair'])
        return q3_poor
    
    def _check_preventive_health_fallback(self, survey_data):
        """Check other questions for preventive health indicators"""
        q6_frequent = any(freq in survey_data.get('question_6', '').lower() 
                         for freq in ['frequently', 'few times'])
        return q6_frequent

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        plan = request.form.get('plan', 'free')
        name = f"{first_name} {last_name}".strip()
        if not first_name or not last_name or not email or not password:
            flash('Please fill out all fields.', 'danger')
            return render_template('signup.html')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return render_template('signup.html')
        new_user = User(email=email, name=name, plan=plan, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not password:
            flash('Password is required.', 'error')
            return redirect(url_for('login'))
            
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/survey', methods=['GET', 'POST'])
@login_required
def survey():
    if request.method == 'POST':
        # Save survey responses
        # Handle multiple checkbox selections for question 1
        question_1_values = request.form.getlist('question_1')
        question_1_text = ', '.join(question_1_values) if question_1_values else ''
        
        survey_response = SurveyResponse(
            user_id=current_user.id,
            question_1=question_1_text,
            question_2=request.form.get('question_2'),
            question_3=request.form.get('question_3'),
            question_4=request.form.get('question_4'),
            question_5=request.form.get('question_5'),
            question_6=request.form.get('question_6'),
            question_7=request.form.get('question_7')
        )
        db.session.add(survey_response)
        db.session.commit()
        
        flash('Survey completed! You can now upload your medical records.', 'success')
        return redirect(url_for('upload_records'))
    
    return render_template('survey.html')

@app.route('/upload_records', methods=['GET', 'POST'])
@login_required
def upload_records():
    if request.method == 'POST':
        if 'medical_records' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['medical_records']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file and assign clusters
            try:
                medical_data = process_medical_records(filepath)
                assign_clusters_to_user(current_user.id, medical_data)
                flash('Medical records uploaded and clusters assigned successfully!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                flash(f'Error processing file: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload a pickle file.', 'error')
    
    return render_template('upload_records.html')

@app.route('/dashboard')
@login_required
def dashboard():
    user_clusters = UserCluster.query.filter_by(user_id=current_user.id).all()
    survey_response = SurveyResponse.query.filter_by(user_id=current_user.id).first()
    
    return render_template('dashboard.html', 
                         clusters=user_clusters, 
                         survey_response=survey_response)

@app.route('/staff-dashboard')
def staff_dashboard():
    users = User.query.all()
    return render_template('staff_dashboard.html', users=users)

@app.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('staff_dashboard'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pkl'}

def process_medical_records(filepath):
    """Process uploaded medical records pickle file"""
    try:
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        # If it's a single DataFrame, wrap it in a dict
        if isinstance(data, pd.DataFrame):
            # Try to determine what type of data this is based on columns
            if 'diagnosis_name' in data.columns:
                return {'diagnoses': data}
            elif 'is_pregnant' in data.columns:
                return {'maternal_health': data}
            elif 'age' in data.columns:
                return {'patients': data}
            elif 'medication_name' in data.columns:
                return {'medications': data}
            else:
                return {'unknown': data}
        
        return data
    except Exception as e:
        raise Exception(f"Failed to process medical records: {str(e)}")

def assign_clusters_to_user(user_id, medical_data):
    """Assign clusters to user based on survey and medical data"""
    # Get user's survey responses
    survey_response = SurveyResponse.query.filter_by(user_id=user_id).first()
    if not survey_response:
        raise Exception("No survey responses found for user")
    
    # Convert survey responses to dict
    survey_data = {
        'question_1': survey_response.question_1,
        'question_2': survey_response.question_2,
        'question_3': survey_response.question_3,
        'question_4': survey_response.question_4,
        'question_5': survey_response.question_5,
        'question_6': survey_response.question_6,
        'question_7': survey_response.question_7
    }
    
    # Assign clusters
    assigner = ClusterAssigner()
    assigned_clusters = assigner.assign_clusters(survey_data, medical_data)
    
    # Save cluster assignments
    for cluster_name, confidence in assigned_clusters:
        user_cluster = UserCluster(
            user_id=user_id,
            cluster_name=cluster_name,
            confidence_score=confidence
        )
        db.session.add(user_cluster)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 