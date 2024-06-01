from bs4 import BeautifulSoup
import random
import os
import json
import google.generativeai as genai
import requests



if os.path.exists("./sandbox"):
    # if it has no files in it, pass
    files = os.listdir("./sandbox")
    if len(files) == 0:
        pass
    else:
       os.remove("./sandbox")
else:
    os.mkdir("./sandbox")

with open("config.txt") as f:
    lines = f.readlines()
    for line in lines:
        if line.startswith("api_key: "):
            GOOGLE_API_KEY = line.split("api_key: ")[1]
            if GOOGLE_API_KEY == "":
                print("Set the API key in config.txt")
                exit()

genai.configure(api_key=GOOGLE_API_KEY)

def generate_plain(query, who):
    prompt = who +": " + query + " Assistant:"
    response = genai.GenerativeModel("models/gemini-1.0-pro").generate_content(prompt)
    if response._done:
        output = ''.join(part.text for part in response._result.candidates[0].content.parts)
        return output
    else:
        return "Generation did not complete."

def web_search(query):
    system = f"You are a assistant, your job is to make a search query that will provide relevant information to {query} when searched on google.Simply provide the search query. If you dont think info is needed simply say \"no info\". Assistant:"
    out = generate_plain(system, "system").replace(" ", "+")
    if out not in ["Generation did not complete.", "no info"]:
        base = "https://www.google.com/search?q="
        print("Researching: " + out.replace("+", " "))
        url = base + out
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        urls = []
        url_amt = 5
        for link in soup.find_all('a'):
            href = link.get('href')
            if href.startswith('/url?q='):
                clean_url = href.split('/url?q=')[1].split('&')[0]
                if clean_url.startswith('http') or clean_url.startswith('https'):
                    urls.append(clean_url)
                    url_amt -= 1
                    if url_amt == 0:
                        break
        x = random.choice(urls)
        print("Researching from URL: " + x)
        x = requests.get(x).text
        x = BeautifulSoup(x, features="html.parser").text
        system = f"Summarize this, if you don't think this infomation would help someone who is trying to {query}, just say \"no info\". if you think its helpful, simply make a summarizatoin and nothing else: " + x + " Assistant:"
        x = generate_plain(system, "system")
        if (x == "Generation did not complete." or x == "no info"):
            print("The AI has not found any relevant information in searching.")
        else:
            return x
    print("The AI has not found any relevant information in searching.")
    return "no info"


def generate_response(prompt, model="models/gemini-1.0-pro"):
    web_data = web_search(prompt)
    web_results = "System: Here is some useful data: " + web_data + "."
    if web_data == "no info":
        web_results = ""
    system = (
        web_results +"System: You are an assistant, you are in control of a sandbox in which "
        "you can develop in. You can use the word '|create (file name)|' to create "
        "a file of that name, and 'delete (file name)' to do the opposite, "
        "'|run (command)|' to run a command in shell. Using '|edit (file)|' will replace "
        "the content of that file with all what you say until '|stop_editing|' "
        "which will save. Your job is to create the user's requested application through making files/editing. All files you make will be in thet sandbox as will as commands. User: " + prompt + " Assistant:"
    )
    response = genai.GenerativeModel(model).generate_content(system)

    if response._done:
        output = ''.join(part.text for part in response._result.candidates[0].content.parts)
        return output
    else:
        return "Generation did not complete."

def generate_summary(prompt, model="gemini-1.5-flash"):
    system = (
        f"System: You are an assistant, you are to summarize and explain what was done in: {prompt} Assistant:"
    )
    response = genai.GenerativeModel(model).generate_content(system)

    if response._done:
        output = ''.join(part.text for part in response._result.candidates[0].content.parts)
        return output
    else:
        return "Generation did not complete."
    
request = input("Enter your request: ")
 
output = generate_response(request)

print("Summary: " + generate_summary(output))

keywords = ["create", "delete", "run", "edit", "stop_editing"]
output = output.splitlines()
cleaned_output = []

for line in output:
    if (line.startswith("```")):
        line = ""
    cleaned_output.append(line)

full = "\n".join(cleaned_output)
edit = False
code = ""
for line in cleaned_output:
    if edit:
        if line.startswith("|stop_editing|"):
            edit = False
            with open("./sandbox/" + name, "w+") as f:
                f.write(code)
                print("Saved: " + name)
            line = ""
        else:
            code += line + "\n"
            continue
        code += line + "\n"

    if line.startswith("|"):
        if line.startswith("|create"):
            x = line.split(" ")
            name = x[1] 
 
            name = name[:-1]
            with open("./sandbox/" + name, "w+") as f:
                pass
            print("Created: " + name)

                
            
        elif line.startswith("|delete"):
            x = line.split(" ")
            name = x[1] 
            # remove last character
            name = name[:-1]
            os.remove("./sandbox/" + name)

            print("Deleted: " + name)

        elif line.startswith("|edit"):
            x = line.split(" ")
            name = x[1] 
            # remove last character
            name = name[:-1]
            edit = True

            print("Editing: " + name)

        elif line.startswith("|run"):
            x = line.split("|run ")
            name = x[1] 
            # remove last character
            name = name[:-1]
            print("Command Run:" + name)
            os.system("cd sandbox && " + name)

            
