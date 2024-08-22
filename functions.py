import PyPDF2
import os
import time

# import pdfplumber
from multiprocessing import Pool
import asyncio
from concurrent.futures import ThreadPoolExecutor
import openai
import backoff
import zipfile
from werkzeug.exceptions import HTTPException
import asyncio
import json


# Placeholder for API key
api_key = "your-api-key-placeholder"
client = openai.AsyncOpenAI(api_key=api_key)


def is_cv(text):
    # List of common CV keywords
    cv_keywords = ["education", "skills", "experience"]

    for key in cv_keywords:
        if key in text.lower():
            return True
    return False


def get_file_size(file_path):
    # Check if file exists
    if os.path.exists(file_path):
        # Get file size in bytes
        file_size = os.path.getsize(file_path)
        # Convert bytes to kilobytes (optional)
        file_size_kb = file_size / 1024
        if file_size_kb > 1024:
            return False
        else:
            return True
    else:
        print("File not found.")
        return None


def check_pdf_for_cv(pdf_path):
    if not get_file_size(pdf_path):
        print("The PDF file size exceeds the limit.")
        return pdf_path, False
    with open(pdf_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
        if is_cv(text):
            print("The PDF file appears to be a CV.")
            return pdf_path, text, True
        else:
            print("The PDF file does not appear to be a CV.")
            return pdf_path, text, False


def pre_process(path):
    start_time = time.time()
    pdf_files = [
        os.path.join(path, file) for file in os.listdir(path) if file.endswith(".pdf")
    ]
    results = []
    for pdf_file in pdf_files:
        result = check_pdf_for_cv(pdf_file)
        # print("pdf_path, text, True",result)
        results.append(result)
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"Execution time: {execution_time} seconds")
    return results


@backoff.on_exception(backoff.expo, openai.RateLimitError)
async def JSON(file_path,user_input):
    details = """can you make it structured as a dictionary format like as following
    {   'file_path' : 'insert file path here with root directory',
        'name' : 'details',
        'profile' : 'details',
        'personal-details' : 'details',
        'location' : 'details',
        'university' : 'details',
        'phone_number' : 'details',
        'email' : 'details',
        'education'   : 'details',
        'skills': 'details',
        'experience': 'details',
        'courses'  : 'details'
    } """
    # print(file_path)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.001,
        messages=[
            {
                "role": "system",
                "content": f"you are a helpful assistant, please provide a structured format of the following text '{user_input}' user provides you and the file path is '{file_path}'. In no way are you allowed to hallucinate or make up answers. Details are :  '{details}' and return response without '```python', '```json' and any extra commentary",
            }
        ],
    )
    response_message = response.choices[0].message.content
    return response_message


################################################################################################
@backoff.on_exception(backoff.expo, openai.RateLimitError)
async def openAI(json_text, rules_text):
    out_put_formate = {
        "data": 
            {
            "file_path": "<Find file path from given data>",
            "final_result": "<yes or no>",
            "feed_back": "< provide a brief review , about the evaluation you did>",
            "user_name": "<get it from given data>",
            "email": "<get it from given data>",
            "phone_number": "<get the phone number only from given data>",
            "score": "<on the basis of relevance with the description you have to score it>"
            }
        
    }

    user_input = f"You are a helpful assistant that analyzes CVs for shortlisting. Please rank the relevance of the candidate's qualifications provided in {json_text} , to all the aspects of job requirements criteria provided in {rules_text}, on a scale of 1 to 10 (where 1 is minimum similarity , and 10 is maximum similarity), and for every aspect if you get value greater than 7, the selection should be made as positive but you can't be lenient. Provide your out_put in the same structure as provide here {out_put_formate} regarding the candidate's eligibility for shortlisting based on the analysis. always return the responce in the defined structure of {out_put_formate}, nothing else, please mention the location details in the feedback too, ass this check in also nesessory. 'remember that there is no way that the name and email is missing in the input data, if it is not mentioned return value as null', if the location of candidate is other then the defined location, there is a straight no. Always return the out_put as in double quotes json formate.Don't give '```json' in response simply give response without any commentary. "
    try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.001,
                messages=[
                    {"role": "system", "content": user_input},
                ],
            )
            response_message = response.choices[0].message.content
            # print("Response message from openAI:", response_message)
            response_message = response_message.replace("\n", "").replace("/", "/")
            json_object = json.loads(response_message)
            # print(json_object)
            return json_object
    except Exception as e:
            print(f"Error in openAI function: {e}")
            return {}  # Return an empty dict or handle it as needed

async def process_pdfs_in_loop(path, details):
    num_threads = os.cpu_count()
    # print("Number of threads:", num_threads)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future = executor.submit(pre_process, path)

    resultss = await asyncio.get_event_loop().run_in_executor(None, future.result)
    not_cv_list = []
    # print(resultss)
    for file_path, _ , is_cvv in resultss:
        if not is_cvv:
            not_cv_list.append(file_path)

    print("pass 1")

    tasks = [JSON(file_name,prompt) for file_name, prompt, is_cvv in resultss if is_cvv]
    results = await asyncio.gather(*tasks)
    # print(results)
    print("pass 2")

    async def openAI_wrapper(prompt1, details):
        return await openAI(prompt1, details)  # Assuming openAI is async

    task1 = [openAI_wrapper(prompt1, details) for prompt1 in results]
    print("#########################################################################")
    print("#########################################################################")

    try:
        candidates = await asyncio.gather(*task1)
    except Exception as e:
        print(f"Error while gathering tasks: {e}")
        return [], not_cv_list

    print("#########################################################################")
    print("#########################################################################")
    # print("type(candidates)",candidates[0]['data']['phone_number'])

    print("pass 3")

    return candidates, not_cv_list


# details = """
# We are looking for a Junior AI Developer with a keen interest in artificial intelligence. This role is ideal for those eager to contribute in small AI projects and increase their Python development skills in a dynamic and innovative environment.


# Key Responsibilities:

# Develop and maintain Python code.
# Utilise Object-Oriented Programming principles to create efficient and scalable solutions.
# Design algorithms and build logical solutions to complex problems.
# Apply basic AI/ML concepts to real-world projects and scenarios.
# Work with OpenAI and Langchain APIs to integrate advanced AI functionalities into projects.
# Operate within various frameworks like FastAPI, Flask, or Django, according to project requirements.


# Must-Have Skills:

# Strong proficiency in Python programming and data manipulation.
# Solid understanding of Object-Oriented Programming (OOP).
# Capable of designing algorithms and building logical solutions.
# Fundamental knowledge of AI/ML concepts.
# Basic knowledge of NLP.


# Preferred Skills:

# A Strong grasp of NLP
# Experience or exposure to chatbot development, including understanding Langchain routers, RAGs (Retrieval-Augmented Generation), and other related technologies.
# Knowledge or interest in developing and fine-tuning models for NLP (Natural Language Processing) and image processing tasks.
# Familiarity with image generation APIs such as Stability AI, Imagine.ai, DALL-E.
# Eagerness to delve into deep learning and model creation.

# Qualifications:

# Pursuing or recently completed a degree in Computer Science, Engineering, or a related field.
# Demonstrated passion and interest in Python programming and AI.
# Enthusiasm for learning and staying updated with the latest trends in AI and ML.
# """

# async def main():
#     await process_pdfs_in_loop("cv_folder", details)

# # To run the main function in an asyncio event loop
# if __name__ == "__main__":
#     asyncio.run(main())
