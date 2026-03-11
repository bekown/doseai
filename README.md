# DoseAI - AI-Powered Medication Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

<p align="center">
  <img src="docs/images/doseai-logo.png" alt="DoseAI Logo" width="200"/>
</p>

<p align="center">
  <strong>Intelligent medication management powered by AI</strong>
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-demo">Demo</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-documentation">Documentation</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-contributing">Contributing</a> •
  <a href="#-license">License</a>
</p>

---

## 📋 **Table of Contents**

- [About The Project](#-about-the-project)
- [Features](#-features)
- [Demo](#-demo)
- [Quick Start](#-quick-start)
- [Installation Guide](#-installation-guide)
- [Usage Guide](#-usage-guide)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [AI Integration](#-ai-integration)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [Roadmap](#-roadmap)
- [License](#-license)
- [Contact](#-contact)
- [Acknowledgements](#-acknowledgements)

---

## 🎯 **About The Project**

### **The Problem**
Medication non-adherence is a global health crisis:
- **50%** of patients don't take medications as prescribed
- **125,000** preventable deaths annually in Europe
- **€125 billion** annual cost to European healthcare systems
- **1 in 3** medication-related hospitalizations are preventable

### **The Solution**
DoseAI is an intelligent medication assistant that uses artificial intelligence to help patients adhere to their medication regimens. Unlike simple reminder apps, DoseAI:

1. **Learns** from user behavior patterns
2. **Personalizes** reminders based on individual habits
3. **Predicts** potential issues before they occur
4. **Educates** patients about their medications
5. **Connects** patients with their care team

### **Built With**
- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite/PostgreSQL
- **AI**: Google Gemini API
- **Frontend**: HTML, CSS, JavaScript, Materialize CSS
- **Authentication**: Flask-Login, Flask-Bcrypt
- **Task Scheduling**: APScheduler

---

## ✨ **Features**

### **Core Features**

| Feature | Description | Status |
|---------|-------------|--------|
| **User Management** | Secure registration, login, and profile management | ✅ Complete |
| **Medication Tracking** | Add, edit, and track multiple medications | ✅ Complete |
| **Prescription Management** | Manage prescriptions with dosage, frequency, and duration | ✅ Complete |
| **Smart Reminders** | Intelligent notifications based on user patterns | ✅ Complete |
| **Dose Logging** | Log taken, missed, or snoozed doses | ✅ Complete |
| **Health Tracking** | Record vitals, symptoms, and mood | ✅ Complete |
| **Daily Check-ins** | Quick daily health status updates | ✅ Complete |

### **AI-Powered Features**

| Feature | Description | Status |
|---------|-------------|--------|
| **Medication Summaries** | Patient-friendly explanations of medications | 🚧 In Progress |
| **Drug Interaction Checking** | Identify potential interactions between medications | 🚧 In Progress |
| **Adherence Pattern Detection** | Learn user habits to optimize reminders | 🚧 In Progress |
| **Personalized Insights** | AI-generated health recommendations | 🚧 In Progress |
| **Missed Dose Guidance** | Intelligent advice for missed doses | 🚧 In Progress |
| **Wellness Score Calculation** | Composite health score based on multiple factors | 🚧 In Progress |

### **Advanced Features**

| Feature | Description | Status |
|---------|-------------|--------|
| **Emergency Contacts** | Notify family/caregivers in emergencies | ✅ Complete |
| **Healthcare Provider Portal** | Share data with doctors (coming soon) | ⏳ Planned |
| **Pharmacy Integration** | Automated refill reminders (coming soon) | ⏳ Planned |
| **Data Export** | Export health data for research/sharing | ⏳ Planned |
| **Wearable Integration** | Connect with fitness trackers (future) | 🔮 Future |
| **Multi-language Support** | Support for multiple languages (future) | 🔮 Future |

---

## 🎥 **Demo**

### **Live Demo**
🔗 **[https://doseai-demo.herokuapp.com](https://doseai-demo.herokuapp.com)**

*Demo credentials:*
- **Email**: demo@doseai.com
- **Password**: demo123

### **Screenshots**

<p align="center">
  <img src="docs/images/dashboard.png" alt="Dashboard" width="800"/>
  <br/>
  <em>Dashboard - Overview of medications and health status</em>
</p>

<br/>

<p align="center">
  <img src="docs/images/medications.png" alt="Medications" width="800"/>
  <br/>
  <em>Medications - Manage your medication list</em>
</p>

<br/>

<p align="center">
  <img src="docs/images/reminders.png" alt="Reminders" width="800"/>
  <br/>
  <em>Smart Reminders - Intelligent medication notifications</em>
</p>

<br/>

<p align="center">
  <img src="docs/images/insights.png" alt="Insights" width="800"/>
  <br/>
  <em>AI Insights - Personalized health recommendations</em>
</p>

### **Demo Video**
[![DoseAI Demo Video](https://img.youtube.com/vi/VIDEO_ID/0.jpg)](https://www.youtube.com/watch?v=VIDEO_ID)

---

## ⚡ **Quick Start**

Get DoseAI running in 5 minutes:

```bash
# Clone the repository
git clone https://github.com/yourusername/doseai.git
cd doseai

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Seed with sample data (optional)
flask seed-db

# Run the app
flask run
```

Visit **http://localhost:5000** in your browser.

---

## 📦 **Installation Guide**

### **Prerequisites**

- Python 3.9 or higher
- pip (Python package manager)
- Git
- SQLite (development) or PostgreSQL (production)
- Redis (optional, for caching)

### **Step-by-Step Installation**

#### **1. Clone the Repository**

```bash
git clone https://github.com/yourusername/doseai.git
cd doseai
```

#### **2. Set Up Virtual Environment**

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

#### **3. Install Dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### **4. Configure Environment Variables**

Create a `.env` file in the root directory:

```env
# Flask
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this

# Database
DATABASE_URL=sqlite:///doseai.db

# AI Services
GEMINI_API_KEY=your-gemini-api-key-here

# Email (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
```

#### **5. Initialize Database**

```bash
# Create database tables
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Or use the custom command
flask init-db
```

#### **6. Seed Database (Optional)**

```bash
# Add sample data for testing
flask seed-db

# Create admin user
flask create-admin --username admin --email admin@example.com --password admin123
```

#### **7. Run the Application**

```bash
# Development mode
flask run

# Or with debug mode
python run.py
```

#### **8. Access the Application**

Open your browser and navigate to: **http://localhost:5000**

---

## 📖 **Usage Guide**

### **First-Time User Guide**

#### **1. Registration**
1. Navigate to `/register`
2. Fill in your details (username, email, password)
3. Click "Register"
4. You'll be redirected to login

#### **2. Complete Your Profile**
1. After first login, complete your profile
2. Add personal information (name, date of birth, etc.)
3. Add emergency contacts (optional but recommended)
4. Save your profile

#### **3. Add Your Medications**
1. Go to "Medications" from the navigation bar
2. Click "Add Medication"
3. Fill in medication details:
   - Name (e.g., "Lisinopril")
   - Strength (e.g., "10mg")
   - Form (e.g., "tablet")
   - Dosage instructions
   - Frequency (times per day)
   - Start date
   - End date (if applicable)
4. Click "Save Medication"

#### **4. Set Up Reminders**
1. After adding a medication, click "Set Schedule"
2. Choose reminder times
3. Select days of the week
4. Configure advanced options (with food, before bed)
5. Save schedule

#### **5. Daily Use**
- **Dashboard**: View upcoming doses and health summary
- **Take Medications**: Click "Take" when you take a dose
- **Snooze**: Click "Snooze" to delay a reminder
- **Log Health**: Use daily check-in to record vitals and symptoms

### **Advanced Features**

#### **Health Tracking**
1. Go to "Health" → "Vitals"
2. Record blood pressure, heart rate, temperature
3. View trends over time

#### **View Insights**
1. Go to "Insights"
2. View adherence rates and trends
3. Read AI-generated health recommendations
4. Export your data

#### **Emergency Mode**
1. In case of emergency, click the emergency button
2. Notify emergency contacts
3. Share location (optional)
4. Get guidance on what to do

---

## 🛠️ **Tech Stack**

### **Backend**
```
├── Flask 3.0+              # Web framework
├── SQLAlchemy 2.0+         # ORM
├── Flask-Login             # Authentication
├── Flask-Bcrypt            # Password hashing
├── Flask-WTF               # Forms & CSRF protection
├── Flask-Migrate           # Database migrations
├── Flask-Caching           # Caching layer
├── APScheduler             # Task scheduling
├── Google Generative AI    # Gemini AI integration
└── Redis                   # Cache backend (optional)
```

### **Frontend**
```
├── HTML5                   # Structure
├── CSS3                    # Styling
├── JavaScript (ES6+)       # Interactivity
├── Materialize CSS 1.0+    # UI framework
├── Chart.js 4.0+          # Data visualization
└── Fetch API              # AJAX requests
```

### **Database**
```
├── SQLite (development)    # File-based database
└── PostgreSQL (production) # Production database
```

### **DevOps & Tools**
```
├── Git                     # Version control
├── Docker                  # Containerization
├── pytest                  # Testing
├── Black                   # Code formatting
├── Flake8                  # Linting
└── GitHub Actions          # CI/CD
```

---

## 📁 **Project Structure**

```
doseai/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models.py                 # Database models
│   ├── extensions.py             # Flask extensions
│   ├── commands.py               # CLI commands
│   │
│   ├── auth/                     # Authentication module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   │
│   ├── dashboard/                 # Dashboard module
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── medications/               # Medications module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── services.py
│   │
│   ├── health/                    # Health tracking module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   │
│   ├── insights/                  # Insights & analytics
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   ├── notifications/             # Notifications module
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── forms.py
│   │
│   └── utils/                     # Utility functions
│       ├── __init__.py
│       ├── validators.py
│       ├── helpers.py
│       ├── ai_service.py
│       ├── notification_service.py
│       ├── cache_service.py
│       └── file_upload.py
│
├── templates/                      # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── dashboard/
│   ├── medications/
│   ├── health/
│   ├── insights/
│   └── notifications/
│
├── static/                         # Static assets
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/
│
├── tests/                          # Unit tests
│   ├── test_auth.py
│   ├── test_medications.py
│   └── test_models.py
│
├── migrations/                      # Database migrations
├── docs/                            # Documentation
├── .env.example                     # Environment variables example
├── .gitignore                       # Git ignore file
├── requirements.txt                 # Python dependencies
├── config.py                        # Configuration
├── run.py                           # Application entry point
├── Dockerfile                       # Docker configuration
├── docker-compose.yml               # Docker Compose
└── README.md                        # This file
```

---

## 📚 **API Documentation**

### **Authentication Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | User login |
| POST | `/auth/register` | User registration |
| GET | `/auth/logout` | User logout |
| GET | `/auth/profile` | Get user profile |
| POST | `/auth/profile` | Update user profile |

### **Medication Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medications/` | Get all medications |
| GET | `/medications/<id>` | Get medication details |
| POST | `/medications/add` | Add new medication |
| POST | `/medications/<id>/edit` | Update medication |
| POST | `/medications/<id>/delete` | Delete medication |
| GET | `/medications/api/upcoming` | Get upcoming doses |
| GET | `/medications/api/adherence` | Get adherence data |

### **Health Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/vitals` | Get vital signs |
| POST | `/health/vitals` | Record vital signs |
| GET | `/health/symptoms` | Get symptoms |
| POST | `/health/symptoms` | Record symptom |
| GET | `/health/checkin` | Get daily check-in |
| POST | `/health/checkin` | Complete daily check-in |
| GET | `/health/lab-tests` | Get lab tests |
| POST | `/health/lab-tests` | Add lab test |

### **Insights Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/insights/` | Get insights dashboard |
| GET | `/insights/adherence` | Get adherence analytics |
| GET | `/insights/health-trends` | Get health trends |
| GET | `/insights/ai-insights` | Get AI insights |
| POST | `/insights/refresh-ai-insights` | Refresh AI insights |

### **Notifications Endpoints**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/notifications/` | Get notifications |
| POST | `/notifications/<id>/read` | Mark as read |
| POST | `/notifications/read-all` | Mark all as read |
| POST | `/notifications/<id>/delete` | Delete notification |
| GET | `/notifications/preferences` | Get preferences |
| POST | `/notifications/preferences` | Update preferences |

### **Example API Usage**

```javascript
// Get upcoming doses
fetch('/medications/api/upcoming?hours=24')
  .then(response => response.json())
  .then(data => console.log(data));

// Log a dose as taken
fetch('/medications/5/take', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ dose_id: 123 })
});
```

---

## 🤖 **AI Integration**

### **Google Gemini AI Integration**

DoseAI leverages Google's Gemini AI for intelligent features:

```python
# app/utils/ai_service.py

class AIService:
    """Service for AI-powered features using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model_name = 'gemini-2.0-flash-exp'
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
    
    def generate_medication_summary(self, medication_data):
        """Generate patient-friendly medication summary"""
        prompt = f"""
        Generate a patient-friendly summary for: {medication_data['name']} 
        {medication_data['strength']} {medication_data['form']}
        
        Include:
        - What it's used for
        - How to take it
        - Common side effects
        - Important warnings
        - What to do if you miss a dose
        
        Use simple, clear language. Avoid medical jargon.
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def check_drug_interactions(self, medications):
        """Check for potential drug interactions"""
        meds_text = "\n".join([f"- {med}" for med in medications])
        
        prompt = f"""
        Analyze these medications for potential interactions:
        {meds_text}
        
        Return JSON with:
        - interaction_name
        - severity (major/moderate/minor)
        - description
        - recommendation
        """
        
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
    
    def generate_health_insights(self, user_data):
        """Generate personalized health insights"""
        prompt = f"""
        Based on this health data, provide 3 actionable insights:
        
        Adherence: {user_data['adherence_rate']}%
        Symptoms: {user_data['symptoms_count']} active
        Medications: {user_data['medication_count']}
        
        Format as JSON with title, description, and priority.
        """
        
        response = self.model.generate_content(prompt)
        return json.loads(response.text)
```

### **AI Features Roadmap**

| Feature | Current Status | Target Completion |
|---------|---------------|-------------------|
| Medication Summaries | 🚧 70% complete | April 2026 |
| Drug Interaction Check | 🚧 50% complete | May 2026 |
| Adherence Pattern Detection | 🚧 30% complete | June 2026 |
| Personalized Insights | 🚧 20% complete | July 2026 |
| Missed Dose Guidance | ⏳ Planning | August 2026 |
| Predictive Alerts | 🔮 Future | 2027 |

---

## 🧪 **Testing**

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_medications.py

# Run with verbose output
pytest -v
```

### **Test Structure**

```
tests/
├── conftest.py              # Test fixtures
├── test_auth.py             # Authentication tests
├── test_medications.py      # Medication tests
├── test_health.py           # Health tracking tests
├── test_models.py           # Database model tests
├── test_services.py         # Service layer tests
└── test_api.py              # API endpoint tests
```

### **Example Test**

```python
# tests/test_medications.py

def test_add_medication(client, auth):
    """Test adding a new medication"""
    # Login first
    auth.login()
    
    # Add medication
    response = client.post('/medications/add', data={
        'name': 'Test Medication',
        'strength': '10mg',
        'form': 'tablet',
        'dosage': 'Take 1 tablet',
        'frequency': 2,
        'start_date': '2026-01-01'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Medication added successfully' in response.data
```

---

## 🚀 **Deployment**

### **Deploy to Heroku**

```bash
# Create Heroku app
heroku create doseai-app

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set GEMINI_API_KEY=your-api-key

# Deploy
git push heroku main

# Run migrations
heroku run flask db upgrade

# Open app
heroku open
```

### **Deploy with Docker**

```bash
# Build image
docker build -t doseai .

# Run container
docker run -p 5000:5000 --env-file .env doseai

# Or use docker-compose
docker-compose up -d
```

### **Docker Configuration**

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/doseai
    depends_on:
      - db
    volumes:
      - ./uploads:/app/static/uploads

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=doseai
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### **Production Checklist**

- [ ] Use PostgreSQL instead of SQLite
- [ ] Set up Redis for caching
- [ ] Configure proper logging
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Enable HTTPS with Let's Encrypt
- [ ] Set up database backups
- [ ] Configure email service (SendGrid, AWS SES)
- [ ] Set up CI/CD pipeline
- [ ] Load testing with Locust
- [ ] Security audit

---

## 🤝 **Contributing**

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

### **Code of Conduct**

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

### **How to Contribute**

1. **Fork the Project**
   ```bash
   git clone https://github.com/yourusername/doseai.git
   cd doseai
   git checkout -b feature/AmazingFeature
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements-dev.txt
   ```

3. **Make Your Changes**
   - Write code following our style guide
   - Add tests for new features
   - Update documentation

4. **Run Tests**
   ```bash
   pytest
   flake8 app
   black app
   ```

5. **Commit Your Changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```

6. **Push to Branch**
   ```bash
   git push origin feature/AmazingFeature
   ```

7. **Open a Pull Request**

### **Development Guidelines**

- **Python**: Follow PEP 8
- **JavaScript**: Use ES6+ features
- **CSS**: Follow BEM naming convention
- **Documentation**: Update README and docstrings
- **Tests**: Aim for 80%+ coverage

### **Feature Request Process**

1. Check existing issues for similar requests
2. Open a new issue with the "enhancement" tag
3. Describe the feature and its use case
4. Wait for maintainer feedback

### **Bug Report Process**

1. Check if the bug already exists
2. Open a new issue with the "bug" tag
3. Include steps to reproduce
4. Include expected vs actual behavior
5. Include screenshots if applicable
6. Include environment details

---

## 🗺️ **Roadmap**

### **Current Release: v0.5.0 (Development)**

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT SPRINT (March 2026)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🚧 AI Integration                                                │
│  │  • Medication summaries (70%)                                 │
│  │  • Drug interactions (50%)                                    │
│  │  • Adherence patterns (30%)                                   │
│  └───────────────────────────────────────────────────────────── │
│                                                                   │
│  🚧 Notification System                                           │
│  │  • Push notifications (80%)                                   │
│  │  • Email service (60%)                                        │
│  │  • Smart scheduling (40%)                                     │
│  └───────────────────────────────────────────────────────────── │
│                                                                   │
│  🚧 Analytics                                                     │
│  │  • Adherence reports (75%)                                    │
│  │  • Health trends (50%)                                        │
│  │  • Data export (30%)                                          │
│  └───────────────────────────────────────────────────────────── │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### **Upcoming Releases**

#### **v0.6.0 - AI Core (April 2026)**
- ✅ Complete medication summaries
- ✅ Complete drug interaction checking
- ✅ Basic adherence pattern detection
- ✅ Initial personalized insights

#### **v0.7.0 - Beta Release (May 2026)**
- ✅ Complete notification system
- ✅ Complete analytics dashboard
- ✅ Provider portal v1
- ✅ Beta testing with 50 users

#### **v0.8.0 - Polish & Scale (June 2026)**
- ✅ Performance optimization
- ✅ UX improvements from feedback
- ✅ Comprehensive testing
- ✅ Documentation complete

#### **v1.0.0 - Production Release (July 2026)**
- ✅ Production-ready
- ✅ Full AI feature set
- ✅ HIPAA/GDPR compliance
- ✅ Enterprise features

#### **v2.0.0 - Future (2027)**
- 🔮 Mobile apps (iOS/Android)
- 🔮 Wearable integration
- 🔮 EHR integration
- 🔮 Multi-language support
- 🔮 Telemedicine integration

---

## 📄 **License**

Distributed under the MIT License. See `LICENSE` for more information.

```
MIT License

Copyright (c) 2026 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 **Contact**

**Project Lead:** [Your Name]
- 📧 **Email**: [your.email@example.com]
- 🐦 **Twitter**: [@yourhandle]
- 💼 **LinkedIn**: [linkedin.com/in/yourprofile]
- 🐙 **GitHub**: [github.com/yourusername]

**Project Links:**
- 📦 **Repository**: [github.com/yourusername/doseai](https://github.com/yourusername/doseai)
- 🐛 **Issue Tracker**: [github.com/yourusername/doseai/issues](https://github.com/yourusername/doseai/issues)
- 📖 **Documentation**: [doseai.readthedocs.io](https://doseai.readthedocs.io)
- 🎥 **Demo**: [doseai-demo.herokuapp.com](https://doseai-demo.herokuapp.com)

---

## 🙏 **Acknowledgements**

### **Research & Inspiration**
- World Health Organization - Adherence reports
- University of Twente - Digital Health research
- Cochrane Collaboration - Systematic reviews
- Open mHealth - Data standards

### **Open Source Libraries**
- Flask and extensions
- SQLAlchemy
- Google Gemini API
- Materialize CSS
- Chart.js

### **Beta Testers**
- My grandfather (the original inspiration)
- Margaret, 68 - Hypertension patient
- James, 54 - Diabetes patient
- Dr. Smith - Primary care physician
- Dr. Jones - Clinical pharmacist

### **Mentors & Advisors**
- Prof. [Name] - Technical guidance
- Dr. [Name] - Clinical insights
- [Name] - UX design

### **Special Thanks**
- University of Twente Digital Health program
- Open source community
- Family and friends for support and feedback

---

## ⭐ **Support**

If you find this project helpful, please consider:
- Starring the repository on GitHub
- Sharing with others who might benefit
- Contributing code or documentation
- Reporting bugs or suggesting features

---

<p align="center">
  Made with ❤️ for better health outcomes
  <br/>
  <br/>
  <a href="https://github.com/yourusername/doseai">GitHub</a>
  ·
  <a href="https://doseai.readthedocs.io">Documentation</a>
  ·
  <a href="https://doseai-demo.herokuapp.com">Demo</a>
  ·
  <a href="https://github.com/yourusername/doseai/issues">Report Bug</a>
  ·
  <a href="https://github.com/yourusername/doseai/issues">Request Feature</a>
</p>
