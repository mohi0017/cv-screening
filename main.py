from functions import process_pdfs_in_loop
from flask import Flask, request, send_from_directory, jsonify,render_template
import shutil
import os
import zipfile
import asyncio
import firebase_admin
from firebase_admin import credentials, db
from flask_cors import CORS
from send_email import *
import time
import json

# Initialize Firebase Admin SDK with the placeholder file
cred = credentials.Certificate("./cv_screening_credentials_placeholder.json")
firebase_admin.initialize_app(cred, {"databaseURL": "https://your-database-url.firebaseio.com/"})

app = Flask(__name__)
CORS(app)

# Home Page
@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

# HR Dashboard
@app.route("/hr_dashboard", methods=["GET"])
def hr_dashboard():
    try:
        return render_template("hr_dashboard.html")
    except Exception as e:
        print("Error rendering HR Dashboard:", e)
        return jsonify({"error": "Error rendering HR Dashboard"}), 500
    
@app.route("/display_candidates", methods=["GET"])
def all_candidates():
    try:
        return render_template("all_candidates.html")
    except Exception as e:
        print("Error rendering all_candidates :", e)
        return jsonify({"error": "Error rendering all_candidates"}), 500

@app.route("/api/candidates", methods=["GET"])
def get_candidates():
    try:
        ref = db.reference("/")
        candidates_data = ref.get()

        if not candidates_data:
            return jsonify({"candidates": []})

        candidates = []
        for position, data in candidates_data.items():
            for cand in list(data.keys()):
                candidate_info = data[cand]
                candidates.append({
                    "name": candidate_info["user_name"],
                    "email": candidate_info["email"],
                    "score": candidate_info["score"],
                    "position": position,
                    "file_path": candidate_info["file_path"],
                    "feedback": candidate_info["feed_back"]
                })

        return jsonify({"candidates": candidates})
    except Exception as e:
        print("Error fetching candidates from Firebase:", e)
        return jsonify({"error": "Error fetching candidates"}), 500

@app.route('/download/<path:filename>')
def download_cv(filename):
    # Ensure that the file is served from the 'static/cv-folder' directory
    return send_from_directory('static/cv-folder', filename, as_attachment=True)

@app.route("/cv_screening", methods=["POST"])
def screening():
    try:
        if request.method != "POST":
            return jsonify({"error": "Invalid request method"}), 400
        
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        # Save the file temporarily before further processing
        temp_file_path = os.path.join(os.getcwd(), file.filename)
        file.save(temp_file_path)
        
        # Check if the uploaded file is a zip file
        if not zipfile.is_zipfile(temp_file_path):
            os.remove(temp_file_path)  # Clean up the temporary file
            return jsonify({"error": "Uploaded file is not a valid zip file"}), 400
        
        destination_folder = os.path.join("static", "cv-folder")
        destination_folder = destination_folder.replace("\\", "/")  # Ensure correct path format
        
        # Ensure the destination folder exists
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        
        # Extract the contents of the zip file into the destination folder
        with zipfile.ZipFile(temp_file_path, "r") as zip_ref:
            try:
                zip_ref.extractall(destination_folder)
            except (zipfile.BadZipFile, RuntimeError) as e:
                os.remove(temp_file_path)  # Clean up the temporary file
                return jsonify({"error": f"Failed to extract ZIP file: {str(e)}"}), 400
        
        # Clean up the temporary file after extraction
        os.remove(temp_file_path)

        # Get a list of PDF files in the destination folder
        pdf_files = [f for f in os.listdir(destination_folder) if f.endswith(".pdf")]

        # Create subdirectories and move PDF files into them
        for i in range(0, len(pdf_files), 10):
            sub_folder = os.path.join(destination_folder, f"subfolder_{i // 10}")
            os.makedirs(sub_folder, exist_ok=True)
            for pdf_file in pdf_files[i:i + 10]:
                shutil.move(
                    os.path.join(destination_folder, pdf_file),
                    os.path.join(sub_folder, pdf_file)
                )

        # Process PDFs asynchronously
        try:
            req_dict = {
                "position": request.form.get("position"),
                "jobDescription": request.form.get("jobDescription"),
                "experience": request.form.get("experience"),
                "skills": request.form.get("skills"),
                "projects": request.form.get("projects"),
                "research": request.form.get("research"),
                "university": request.form.get("university"),
                "region": request.form.get("region"),
            }
            x = req_dict.get("position")
            if not x:
                return jsonify({"error": "Position not provided"}), 400
            
            x = f"/{x}"
            ref = db.reference(x)

            results = []
            for folder in os.listdir(destination_folder):
                folder_path = os.path.join(destination_folder, folder)
                if os.path.isdir(folder_path):
                    sub_results, sub_not_cv_list = asyncio.run(
                        process_pdfs_in_loop(folder_path, req_dict)
                    )
                    if sub_results or sub_not_cv_list:
                        time.sleep(5)
                        results.append(
                            {
                                "cv_file": sub_results,
                                "not_cv_files": sub_not_cv_list,
                            }
                        )

                        # Prepare data for Firebase
                        data_dict = {}
                        for i, result in enumerate(results):
                            for j, candidate in enumerate(result['cv_file']):
                                candidate_data = candidate.get("data", {})
                                custom_key = f"candidate_{i}_{j}"
                                data_dict[custom_key] = candidate_data

                        ref.set(data_dict)

            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": f"Error processing PDFs: {str(e)}"}), 500

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

@app.route("/interview_invite", methods=["POST"])
def interview_invite():
    if request.method == "POST":
        try:
            # Decode and load the JSON data
            data = request.get_json()
            # print(f"Received data: {data}")

            if not data:
                return jsonify({"error": "No data provided"}), 400

            # Extract fields from the data
            hr_name = data.get("name")
            hr_designation = data.get("designation")
            hr_email = data.get("email")
            password = data.get("password")
            emails = data.get("emails", [])
            names = data.get("names", [])
            candidatePosition = data.get("candidatePosition")

            # Validate the data
            if not (isinstance(emails, list) and isinstance(names, list)):
                return jsonify({"error": "Emails and names must be lists"}), 400

            if len(emails) != len(names):
                return jsonify({"error": "Mismatch between number of emails and names"}), 400

            # Set up the SMTP server
            try:
                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                    server.starttls()
                    # print(f"Attempting to log in with email: {hr_email,password}")
                    try:
                        server.login(hr_email, password)
                        print("Login successful")
                    except smtplib.SMTPAuthenticationError as auth_err:
                        print(f"Authentication error: {auth_err}")
                        return jsonify({"error": "Authentication failed. Please check email and password."}), 401
                    except smtplib.SMTPException as e:
                        print(f"SMTP error occurred: {e}")
                        return jsonify({"error": f"SMTP error occurred: {e}"}), 500

                    print(f"Sending emails to: {emails}")
                    for i in range(len(emails)):
                        email_message = send_interview_invitation(
                            emails[i],
                            names[i],
                            candidatePosition,
                            hr_email,
                            hr_name,
                            hr_designation,
                            server
                        )
                        server.send_message(email_message)
                        print(f"Sent email to {emails[i]}")

            except smtplib.SMTPException as e:
                print(f"SMTP error occurred: {e}")
                return jsonify({"error": f"SMTP error occurred: {e}"}), 500

            return jsonify({"return": "success"}), 200

        except Exception as e:
            print(f"An internal error occurred: {e}")
            return jsonify({"error": f"An internal error occurred: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=True)
