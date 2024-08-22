# CV Screening Project

## Overview

The CV Screening Project is designed to automate the HR hiring process. This application streamlines the management of CVs and interview invitations, making it easier for HR departments to handle job applications efficiently. 

### Key Features:
- Upload a ZIP file containing multiple CVs.
- Process CVs using a model and save results in Firebase.
- Send interview invitations to candidates who meet the job requirements.

## Getting Started

### Prerequisites

Before you begin, ensure you have the following:

- A Google Firebase project for storing CV data.
- An OpenAI API key for processing CVs.
- Basic knowledge of Python, Flask, and Firebase.

### Setup Instructions

1. **Download the Repository**

   Clone the repository to your local machine:
   ```bash
   git clone https://github.com/yourusername/cv-screening.git
   cd cv-screening


   Install Dependencies

Install the required Python packages:

bash
Copy code
pip install -r requirements.txt
Configure Firebase

Replace the placeholder Firebase credentials file with your actual Firebase Admin SDK credentials:

File: ./cv_screening_credentials_placeholder.json
Action: Update this file with your Firebase project credentials.
Set Up Firebase in main.py

Open main.py and replace the Firebase configuration placeholders with your Firebase project details:

python
Copy code
# Replace placeholders with your Firebase configuration
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://your-firebase-database-url.firebaseio.com/"
})
Update OpenAI API Key

In functions.py, replace the placeholder OpenAI API key with your actual key:

python
Copy code
api_key = "your-openai-api-key"
client = openai.AsyncOpenAI(api_key=api_key)
Customize Email Content

Modify send_email.py to include your company's branding details:

Replace company_name, logo, and signature placeholders with your actual company information.
python
Copy code
# Define paths to your assets
asset1 = "static/assets/your_company_logo.png"
asset2 = "static/assets/your_company_signature.jpg"

def send_interview_invitation(
    dest_email, c_name, c_designation, sendermail, hr_name, hr_pos, server
):
    # Customize email content and placeholders
    ...
Usage
Start the Application

Run the Flask application:

bash
Copy code
python main.py
Access the Home Page

Open your web browser and navigate to http://localhost:5000 to access the home page where you can upload CVs and input job details.

Upload CVs

Upload a ZIP file containing CVs. The application will process the CVs and store the results in Firebase.

Send Interview Invitations

After processing the CVs, review the results and send interview invitations to candidates who meet the job criteria.

Contributing
Contributions are welcome! Please open an issue or submit a pull request if you have suggestions or improvements.
# cv-screening
