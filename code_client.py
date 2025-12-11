import os
import sys
import json
import ast
import subprocess
import requests
import re 
import uuid

#IF RENAMING THE BELOW FOLDER MAKE SURE ITS IN GITIGNORE, ABSOLUTELY CANNOT COMMIT THE QUESIONS TO GITHUB
WORKSPACE_DIR = "code_workspace"
VSCODE_BIN = "code" # make sure 'code' is in your system PATH. this is for VS CODE to open (Works on Arch linux where i tested it on)


#this is the function that gets the problem by the problem slug
def fetch_problem(title_slug):
    url = "https://leetcode.com/graphql"
    
    query = """
    query getQuestionDetail($titleSlug: String!) {
      question(titleSlug: $titleSlug) {
        questionId
        title
        titleSlug
        content  
        codeSnippets { langSlug code }
        exampleTestcases
      }
    }
    """
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": f"https://leetcode.com/problems/{title_slug}/",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            url, 
            json={"query": query, "variables": {"titleSlug": title_slug}}, 
            headers=headers
        )
        
        if resp.status_code != 200:
            print(f"[!] server returned {resp.status_code}")
        
        resp.raise_for_status()
        return resp.json()['data']['question']
        
    except Exception as e:
        print(f"[!]Error fetching problem: {e}")
        return None    


#this is the piece of code that tries to turn the best solution into runnable python code. thsi way we can test the test cases <3
def analyze_code_structure(code):
    """Finds method name and number of arguments from the class definition."""

    #***************************************************
    #Notes if trying to maintain or fix this function:
    #**************************************************


    #LeetCode snippets often end in a definition line (fr example. "def foo():")
    #which is invalid Python syntax because it expects an indented block
    #I append "        pass" to ensure AST can parse it.
    try:
        tree = ast.parse(code + "\n        pass")
    except SyntaxError:
        #if it still fails try parsing just the code as is
        try:
            tree = ast.parse(code)
        except Exception as e:
            print(f"[DEBUG] AST Parsing failed: {e}")
            return "unknown", 0

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == 'Solution':
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    # FOUND THE FUNCTION!!!!!!!!
                    method_name = item.name
                    # tem.args.args includes 'self', so subtract 1 (I couldn't find a better solution to this)
                    arg_count = len(item.args.args) - 1
                    print(f"[DEBUG] Found method '{method_name}' with {arg_count} args")
                    return method_name, arg_count
    
    print("[DEBUG] could not find 'class Solution' or method in snippet.")
    return "unknown", 0


def parse_test_inputs(raw_txt, args_count):
    #hlper function that parses newline separated JSON strings into grouped lists
    lines = raw_txt.strip().split('\n')
    cases = []
    current_case = []
    for line in lines:
        try:
            current_case.append(json.loads(line))
            if len(current_case) == args_count:
                cases.append(current_case)
                current_case = []
        except: pass
    return cases


def generate_test_script(user_file_path, method_name, test_cases, reference_code=None):
    
    #Generates the test script. 
    #If reference_code is provided then it runs a comparison test
    #This function relies on the community solution
    

    with open(user_file_path, 'r') as f:
        user_code = f.read()

    ref_class_def = ""
    run_comparison = False
    
    if reference_code:
        #I have to rename 'class Solution' to 'class ReferenceSolution' to avoid conflict
        #just used simple string replace (a bit hacky but works for almost all solutions)
        ref_code_renamed = reference_code.replace("class Solution", "class ReferenceSolution")
        ref_class_def = f"\n#reference logic is below\n{ref_code_renamed}\n"
        run_comparison = True

    #imports header for all the structures that are nesceccarry, in the future edit this if a problem needs a structure that I dont yet have
    imports_header = """
from typing import List, Optional, Dict, Set, Tuple
import math
import collections
import functools
import heapq
import itertools
import bisect
import copy

# Definitions
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
"""


    harness = f"""
if __name__ == "__main__":
    try:
        sol = Solution()
        { "ref_sol = ReferenceSolution()" if run_comparison else "" }
        
        cases = {test_cases}
        print("-" * 50)
        
        passed_count = 0
        
        for i, args in enumerate(cases):
            # THEDEEP COPIES ARE SUPER IMPORTANTBECAUSE SOME SOLUTIONS MODIFY THE INPUT IN-PLACE!
            args_user = copy.deepcopy(args)
            args_ref  = copy.deepcopy(args)
            
            #first run the users code
            try:
                result_user = sol.{method_name}(*args_user)
            except Exception as e:
                result_user = f"ERROR {{e}}"

            #try run the reference code ONLY IF IT IS AVAILABLE
            expected_output = None
            status = ""
            
            if {run_comparison}:
                try:
                    expected_output = ref_sol.{method_name}(*args_ref)
                except Exception as e:
                    expected_output = f"REF_ERROR: {{e}}"
                

                if result_user == expected_output:
                    #I dont know if my cool tick and cross emojis will work on windows too or only on linux
                    status = "✅ PASS"
                    passed_count += 1
                else:
                    status = "❌ FAIL"
            
            #print logs (add this to flask page later)
            print(f"Test Case {{i+1}}: {{status}}")
            print(f"  Input:    {{args}}")
            print(f"  Output:   {{result_user}}")
            if {run_comparison}:
                print(f"  Expected: {{expected_output}}")
            print("-" * 50)
        
        if {run_comparison}:
            print(f"\\nFINAL RESULT: {{passed_count}}/{{len(cases)}} passed.")

    except Exception as e:
        import traceback
        traceback.print_exc()
"""
    return imports_header + "\n" + user_code + "\n" + ref_class_def + "\n" + harness
def fetch_community_solution(question_slug):
    #Fetches the best python solution from community discussions. will need to hange this when i add multi language support
    url = "https://leetcode.com/graphql"
    
    query = """
    query communitySolutions($questionSlug: String!, $skip: Int!, $first: Int!, $query: String, $orderBy: TopicSortingOption, $languageTags: [String!], $topicTags: [String!]) {
      questionSolutions(
        filters: {
          questionSlug: $questionSlug,
          skip: $skip,
          first: $first,
          query: $query,
          orderBy: $orderBy,
          languageTags: $languageTags,
          topicTags: $topicTags
        }
      ) {
        solutions {
          id
          title
          post {
            content
          }
        }
      }
    }
    """
    
    variables = {
        "questionSlug": question_slug,
        "skip": 0,
        "first": 1,
        "query": "",
        "orderBy": "most_votes",
        "languageTags": ["python3"],
        "topicTags": []
    }

    #create  a dummy CSRF token otherwise they wont return any response and the site starts acting weird
    #its just uuid
    csrf_token = str(uuid.uuid4())
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": f"https://leetcode.com/problems/{question_slug}/solutions/",
        "Content-Type": "application/json",
        "x-csrftoken": csrf_token,
        "Cookie": f"csrftoken={csrf_token};"
    }

    try:
        resp = requests.post(
            url, 
            json={"query": query, "variables": variables}, 
            headers=headers
        )
        
        resp_json = resp.json()
        
        if 'errors' in resp_json:
            print(f"[DEBUG] API error: {resp_json['errors'][0]['message']}")
            return None

        solutions = resp_json.get('data', {}).get('questionSolutions', {}).get('solutions', [])
        
        if not solutions:
            print("[DEBUG] Noo solutions found in response.")
            return None
        
        return solutions[0]['post']['content']
        
    except Exception as e:
        print(f"[DEBUG] problem while fetching community solution: {e}")
        return None


def extract_code_block(markdown_text):
    
    #scans markdown for a python code block
    #the most importnant thing is that it unescapes literal newlines and strips junk
    
    # Regex to capture: ```(optional_lang)\n(code)```
    pattern = r"```(\w*)\s+(.*?)```"
    matches = re.findall(pattern, markdown_text, re.DOTALL)
    
    best_candidate = None

    #in the first pass look for explicit 'python' tags
    for lang, code in matches:
        if lang.lower() in ['python', 'python3']:
            best_candidate = code
            break
            
    #in the second look for untagged blocks that contain 'class Solution'
    if not best_candidate:
        for lang, code in matches:
            if lang.strip() == "": 
                if "class Solution" in code and "def " in code:
                    if "public:" not in code and "vector<" not in code:
                        best_candidate = code
                        break


    if best_candidate:
        best_candidate = best_candidate.replace("\\n", "\n").replace("\\t", "\t")
        
        idx = best_candidate.find("class Solution")
        if idx != -1:
            return best_candidate[idx:]
            
        return best_candidate

    return None

#ctual mainline code
def main():
    if not os.path.exists(WORKSPACE_DIR):
        os.makedirs(WORKSPACE_DIR)

    slug = input("Enter problem slug (e.g., two-sum): ").strip() or "two-sum"
    print(f"[*] Downloading {slug}...")
    
    data = fetch_problem(slug)
    if not data:
        print("[!] Problem not found.")
        return

    snippet = next((s['code'] for s in data['codeSnippets'] if s['langSlug'] == 'python3'), None)
    if not snippet:
        print("[!]no python3 snippet available. :(")
        return

    filename = f"{slug.replace('-', '_')}.py"
    filepath = os.path.join(WORKSPACE_DIR, filename)

    if not os.path.exists(filepath):
        with open(filepath, "w") as f:
            f.write(snippet)
        print(f"[*]Created {filepath}")
    else:
        print(f"[*] File: {filepath} already exists. Using it.")

    try:
        print("[*] Opening VS Code...")
        #untested on windows, no promises for this working :O
        if sys.platform == "win32":
            subprocess.run(f"cmd /c {VSCODE_BIN} {filepath}", shell=True)
        else:
            subprocess.run([VSCODE_BIN, filepath])
    except FileNotFoundError:
        print(f"[!] Could not find '{VSCODE_BIN}'. Please open {filepath} manually.")


    method_name, arg_count = analyze_code_structure(snippet)
    test_cases = parse_test_inputs(data['exampleTestcases'], arg_count)

    #debugging ground truth
    print("\n[*]fetching community solution for verification...")
    md_content = fetch_community_solution(slug)
    
    reference_code = None
    if md_content:
        reference_code = extract_code_block(md_content)
        if reference_code:
            print("[*]the ground truth solution loaded successfully!")
        else:
            print("[!] Downloaded solution, but regex failed to find code.")
            print(f"[DEBUG] Raw Content Snippet: {repr(md_content[:200])}")
    else:
        print("[!]Failed to download any community solution. Sorry :(")

    # ----------------------------------

    #THIS IS REDUNDANT AFTER THE UI BUT IM KEEPING IT HERE FOR TESTING
    print("\n" + "="*40)
    print(f" PROBLEM: {data['questionId']}. {data['title']}")
    print(f" FUNCTION: {method_name}()")
    print("="*40)
    print("\nInstructions:")
    print("1. Write your code in VS Code.")
    print("2. Save the file (Ctrl+S).")
    print("3. Press ENTER here to run tests.")
    print("4. Type 'q' to quit.")

    while True:
        cmd = input("\n[Run] > ")
        if cmd.lower() == 'q':
            break

        print("[*] Running tests...")
        
        full_script = generate_test_script(filepath, method_name, test_cases, reference_code)
        
        try:
            res = subprocess.run([sys.executable, "-c", full_script], capture_output=True, text=True)
            print(res.stdout)
            if res.stderr:
                print("RUNTIME ERROR:")
                print(res.stderr)
        except Exception as e:
            print(f"Error running subprocess: {e}")

if __name__ == "__main__":
    main()
