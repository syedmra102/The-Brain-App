🧠 The Brain App

A comprehensive productivity platform that combines machine learning performance prediction with gamified habit-building challenges to help users overcome distractions and achieve their goals.

🌟 Live Demo
➡️ Try The Brain App Live ⬅️

*Currently serving 50+ active users with proven engagement*

📊 The Problem
Modern productivity challenges:

❌ Distraction overload from social media and notifications

❌ Lack of motivation to maintain consistent habits

❌ No personalized insights about productivity patterns

❌ Difficulty tracking progress toward long-term goals

🎯 Key Features
🧪 ML Performance Predictor
AI-powered performance scoring based on daily habits

Personalized percentile rankings across 8 key metrics

Data-driven recommendations for improvement

Feature importance analysis using trained ML models

🏆 Gamified Challenge System
text
🎮 Three Difficulty Levels:
• Silver (15 Days - Easy) - Build foundation habits
• Platinum (30 Days - Medium) - Intermediate commitment  
• Gold (60 Days - Hard) - Elite performance training
📈 Advanced Analytics Dashboard
Progress visualization with interactive charts

Distraction trend analysis over time

Savings tracking with financial motivation

Streak maintenance and milestone recognition

🎨 User Experience
Persistent login sessions - No logout on refresh

Real-time Firebase integration for seamless data sync

PDF certificate generation upon challenge completion

Mobile-responsive design with Streamlit

🔐 Enterprise-Grade Security
BCrypt password hashing with salt

Secure token-based authentication

Email password recovery system

Input sanitization against injection attacks

🛠 Technical Architecture
Frontend
python
Streamlit 🎈 → Real-time UI | Session Management | Interactive Components
Backend & Database
python
Python 🐍 → Business Logic | ML Models | PDF Generation | Analytics
Firebase 🔥 → User Auth | Real-time Database | Secure Storage
Machine Learning
python
Scikit-learn 🤖 → Performance Prediction | Feature Analysis | Percentile Ranking
Pickle 🥒 → Model Serialization | Feature Engineering | Data Processing
Additional Technologies
python
Matplotlib 📊 → Data Visualization | Progress Charts | Analytics
FPDF 📄 → Certificate Generation | Achievement Documentation
BCrypt 🔒 → Password Security | Encryption
📁 Project Structure
text


Firebase project

Streamlit account

Installation
bash
# Clone repository
git clone (https://github.com/syedmra102/The-Brain-App)
cd brain-app

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp firebase-config.example.json firebase-config.json
# Add your Firebase credentials

# Run the application
streamlit run app.py
Environment Setup
python
# secrets.toml (Streamlit secrets)
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "your-private-key"
client_email = "your-client-email"
client_id = "your-client-id"


[email]
EMAIL_ADDRESS = "zada44919@gmail.com"
🎮 How It Works
1. User Onboarding
Secure registration with password validation

Profile setup with field specialization

Challenge stage selection (Silver/Platinum/Gold)

2. Daily Workflow
text
📊 Performance Prediction → 🎯 Daily Challenges → 
📈 Progress Tracking → 🏆 Achievement Unlocking
3. ML Integration
python
# Example prediction input
input_data = {
    'hours': 6,
    'distraction_count': 3,
    'avoid_sugar': 1,
    'avoid_junk_food': 1,
    'drink_5L_water': 0,
    'sleep_early': 1,
    'exercise_daily': 1,
    'wakeup_early': 0
}
# Output: Performance Score: 82.5% (Excellent Performer)
📊 ML Model Details
Training Data
Features: Study hours, distraction counts, habit compliance

Target: Performance scores (0-100 scale)

Algorithms: Ensemble methods with feature scaling

Prediction Output
Overall performance score (0-100%)

Percentile rankings across 8 key metrics

Personalized improvement recommendations

🌍 Real-World Impact
User Statistics
✅ 50+ Active Users and growing

✅ Proven engagement with daily check-ins

✅ Consistent habit formation across user base

✅ Positive feedback on distraction reduction


🏆 Achievement System
Badges & Rewards
🥈 Silver Achiever - Complete 15-day challenge

🥈 Platinum Performer - Maintain 30-day streak

🥇 Gold Master - Conquer 60-day elite challenge

📊 Analytics Expert - Utilize all tracking features

🎯 Distraction Slayer - Maintain 90%+ focus days

Certificate Generation
Professional PDF certificates upon completion

Personalized achievement details

Shareable digital credentials

🔮 Future Roadmap
Mobile app development (React Native)

Advanced AI coaching with personalized recommendations

Social features for accountability partners

Integration with productivity tools (Google Calendar, Notion)

Enterprise version for team productivity

🤝 Contributing
We welcome contributions! Please see our Contributing Guidelines for details.

Development Setup
bash
# Fork and clone the repository
git clone(https://github.com/syedmra102/The-Brain-App)
# Create a feature branch
git checkout -b feature/amazing-feature

# Make your changes and test
streamlit run app.py

# Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# Create a Pull Request
📄 License
This project is licensed under the MIT License - see the LICENSE.md file for details.

👨‍💻 Author
Syed Imran Shah

GitHub: syedmra102

LinkedIn: https://www.linkedin.com/in/syed-imran-96bb6931a/



🙏 Acknowledgments
Streamlit team for amazing deployment platform

Firebase for robust backend infrastructure

Scikit-learn for machine learning capabilities

Our 50+ active users for valuable feedback and testing

<div align="center">
⭐ If you find this project helpful, please give it a star! ⭐

Live Demo: Try The Brain App
Report Issues: GitHub Issues

Built with ❤️ using Streamlit, Python, and Machine Learning

Helping users worldwide overcome distractions and achieve their goals

</div>
📞 Contact & Support
Documentation: Full Documentation

Issues: GitHub Issues

Email: zada44919@gmail.com



