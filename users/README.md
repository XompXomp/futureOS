# Patient Health Portal

A comprehensive web application for patient sign-up, health assessment, and intelligent cluster assignment based on survey responses and medical records.

## Features

### 🔐 User Authentication
- Secure email/password registration and login
- Password hashing and session management
- User-friendly authentication flow

### 📋 Health Assessment
- 7-question comprehensive health survey
- Multiple choice and checkbox responses
- Real-time progress tracking
- Form validation and error handling

### 🧠 Intelligent Clustering
- 6 predefined health clusters:
  - **Mental Health**: Depression, anxiety, stress management
  - **Fitness Centric**: Sports injuries, performance optimization
  - **Maternal Health**: Pregnancy care and support
  - **Sleep Health**: Sleep disorders and quality improvement
  - **Preventive Health**: Disease prevention and wellness
  - **Senior Care**: Age-related health management

### 📁 Medical Records Upload
- Secure file upload system
- Support for pickle (.pkl) format files
- Automatic data parsing and analysis
- Privacy-focused data handling

### 📊 Personalized Dashboard
- Cluster assignment display with confidence scores
- Survey response summary
- Personalized health recommendations
- Next steps guidance

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (with SQLAlchemy ORM)
- **Authentication**: Flask-Login
- **Frontend**: Bootstrap 5, Font Awesome
- **Data Processing**: Pandas, NumPy

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd patient-health-portal
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## Usage

### 1. User Registration
- Visit the homepage and click "Get Started"
- Enter your email and create a secure password
- Complete the registration process

### 2. Health Assessment
- After login, complete the 7-question health survey
- Questions cover health goals, activity level, sleep quality, mental well-being, dietary habits, medical visits, and travel plans
- All questions must be answered to proceed

### 3. Medical Records Upload (Optional)
- Upload your medical records in pickle (.pkl) format
- Supported data types: diagnoses, medications, maternal health, patient demographics
- This step enhances cluster assignment accuracy

### 4. View Results
- Access your personalized dashboard
- Review assigned health clusters with confidence scores
- Get personalized health recommendations
- View your survey responses and next steps

## Cluster Assignment Logic

The system uses a sophisticated algorithm to assign users to health clusters based on:

### Survey Responses
- **Question 1**: Primary health goals (multiple selection)
- **Question 2**: Physical activity level
- **Question 3**: Sleep quality
- **Question 4**: Mental well-being
- **Question 5**: Dietary habits
- **Question 6**: Medical visit frequency
- **Question 7**: Travel plans

### Medical Records Analysis
- **Diagnoses**: Depression, anxiety, sleep disorders, sports injuries
- **Medications**: Protein supplements, sleep aids, mental health medications
- **Maternal Health**: Pregnancy status
- **Demographics**: Age for senior care classification

## Data Privacy & Security

- All user data is encrypted and stored securely
- Medical records are processed locally and not shared
- Users can delete their data at any time
- No third-party data sharing
- HIPAA-compliant data handling practices

## File Structure

```
patient-health-portal/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── base.html         # Base template with styling
│   ├── index.html        # Landing page
│   ├── signup.html       # User registration
│   ├── login.html        # User authentication
│   ├── survey.html       # Health assessment
│   ├── upload_records.html # Medical records upload
│   └── dashboard.html    # User dashboard
├── uploads/              # Uploaded medical records (created automatically)
├── patients.db           # SQLite database (created automatically)
└── questions.txt         # Survey questions reference
```

## Database Schema

### Users Table
- `id`: Primary key
- `email`: Unique email address
- `password_hash`: Encrypted password
- `created_at`: Account creation timestamp

### Survey Responses Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `question_1` through `question_7`: Survey responses
- `submitted_at`: Survey completion timestamp

### User Clusters Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `cluster_name`: Assigned health cluster
- `confidence_score`: Assignment confidence (0-1)
- `assigned_at`: Cluster assignment timestamp

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please contact the development team or create an issue in the repository.

## Future Enhancements

- [ ] Real-time health monitoring
- [ ] Integration with wearable devices
- [ ] Telemedicine appointment scheduling
- [ ] Advanced analytics and reporting
- [ ] Mobile application
- [ ] Multi-language support
- [ ] Advanced machine learning models
- [ ] Integration with EHR systems 