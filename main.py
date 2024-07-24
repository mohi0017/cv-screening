from functions import process_pdfs_in_loop
from flask import Flask, request, jsonify
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

# Initialize Firebase Admin SDK
cred = credentials.Certificate("./firebase_credentials.json")
firebase_admin.initialize_app(
    cred,
    {"databaseURL": "https://cv-screening-a346d-default-rtdb.firebaseio.com/"},
)

# Get a reference to the Firebase database

parent_directory = r"C:\Users\LENOVO\Desktop\Screening w Firebase"

app = Flask(__name__)
CORS(app)


@app.route("/cv_screening", methods=["POST"])
def screening():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]
        if file.filename == "":
            return "No selected file"

        if file:
            file.save(file.filename)
            parent_directory = os.path.abspath(os.path.dirname(__file__))
            destination_folder = os.path.join(parent_directory, "cv-folder")
            destination_folder = destination_folder.replace("\\", "/")
            if not os.path.exists(destination_folder):
                os.makedirs(destination_folder)

            # Check if the uploaded file is a zip file
            if not zipfile.is_zipfile(file):
                return "Uploaded file is not a valid zip file"

            with zipfile.ZipFile(file, "r") as zip_ref:
                zip_ref.extractall(destination_folder)

            # Get list of PDF files
            pdf_files = [
                f for f in os.listdir(destination_folder) if f.endswith(".pdf")
            ]

            # Create subdirectories and move PDF files
            num_folders = (len(pdf_files) // 10) + 1
            for i in range(num_folders):
                sub_folder = os.path.join(destination_folder, f"subfolder_{i}")
                os.makedirs(sub_folder)
                for j in range(10):
                    index = i * 10 + j
                    if index < len(pdf_files):
                        shutil.move(
                            os.path.join(destination_folder, pdf_files[index]),
                            sub_folder,
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
                x = req_dict["position"]
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

                            # ref.set(results)
                            data_dict = {}
                            for i, result in enumerate(results):
                                custom_key = f"list_{i}"
                                data_dict[custom_key] = result

                            ref.set(data_dict)

                # Clean up temporary files
                if os.path.exists(f"./{file.filename}"):
                    os.remove(f"./{file.filename}")
                    print("Zip file deleted successfully.")

                shutil.rmtree(destination_folder)

                return jsonify({"success": True})
            except Exception as e:
                if os.path.exists(f"./{file.filename}"):
                    os.remove(f"./{file.filename}")
                    print("Zip file deleted successfully.")

                shutil.rmtree(destination_folder)

                print("Error processing PDFs:", e)
                return jsonify({"error": str(e)})

    return "Invalid request method"


@app.route("/interview_invite", methods=["POST"])
def interview_invite():
    global data
    if request.method == "POST":
        try:
            if request.data:
                data = request.data.decode("utf-8")
                data = json.loads(data)
                print(data)

                hr_name = data["name"]
                hr_designation = data["designation"]
                hr_email = data["email"]
                password = data["password"]
                emails = data["emails"]
                names = data["names"]
                candidatePosition = data["candidatePosition"]

                # Ensure emails and names are lists
                if isinstance(emails, str):
                    emails = [emails]
                if isinstance(names, str):
                    names = [names]

                if len(emails) == len(names):
                    print("same length")
                    
                    # Set up the SMTP server
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(hr_email, password)

                        for i in range(len(emails)):
                            print(emails[i], names[i])

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

                        server.quit()
                    except smtplib.SMTPException as e:
                        print(f"SMTP error occurred: {e}")
                        return jsonify({"error": "SMTP error occurred"}), 500

                else:
                    print("there are some missing details in candidates names or emails")
                    return jsonify({"error": "Mismatch between number of emails and names"}), 400

                return jsonify({"return": "success"}), 200
            else:
                print("error: error in data")
                return jsonify({"error": "Error in data"}), 400
        except Exception as e:
            print(f"An error occurred: {e}")
            return jsonify({"error": "An internal error occurred"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500, debug=False)
