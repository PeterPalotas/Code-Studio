from flask import Flask, render_template, jsonify, request
import sys
import os
import json
import subprocess
import code_client as backend

app = Flask(__name__)

#example problem slugs for now, hardcoded as a proof of concept /* will make this dynamic later */
PROBLEM_SLUGS = [
    "two-sum", "best-time-to-buy-and-sell-stock", "contains-duplicate", "product-of-array-except-self",
    "maximum-subarray", "maximum-product-subarray", "find-minimum-in-rotated-sorted-array",
    "search-in-rotated-sorted-array", "3sum", "container-with-most-water", "sum-of-two-integers",
    "number-of-1-bits", "counting-bits", "missing-number", "reverse-bits", "climbing-stairs",
    "coin-change", "longest-increasing-subsequence", "longest-common-subsequence",
    "word-break", "combination-sum", "house-robber", "house-robber-ii", "decode-ways",
    "unique-paths", "jump-game", "clone-graph", "course-schedule", "pacific-atlantic-water-flow",
    "number-of-islands", "longest-consecutive-sequence", "alien-dictionary", "graph-valid-tree",
    "number-of-connected-components-in-an-undirected-graph", "insert-interval", "merge-intervals",
    "non-overlapping-intervals", "meeting-rooms", "meeting-rooms-ii", "rotate-image", "spiral-matrix",
    "set-matrix-zeroes", "reverse-linked-list", "linked-list-cycle", "merge-two-sorted-lists",
    "merge-k-sorted-lists", "remove-nth-node-from-end-of-list", "reorder-list",
    "maximum-depth-of-binary-tree", "same-tree", "invert-binary-tree", "binary-tree-maximum-path-sum",
    "binary-tree-level-order-traversal", "serialize-and-deserialize-binary-tree",
    "subtree-of-another-tree", "construct-binary-tree-from-preorder-and-inorder-traversal",
    "validate-binary-search-tree", "kth-smallest-element-in-a-bst", "lowest-common-ancestor-of-a-binary-search-tree",
    "implement-trie-prefix-tree", "design-add-and-search-words-data-structure", "word-search-ii",
    "merge-sorted-array", "valid-palindrome", "valid-anagram", "group-anagrams", "valid-parentheses",
    "longest-substring-without-repeating-characters", "longest-repeating-character-replacement",
    "minimum-window-substring", "encode-and-decode-strings", "top-k-frequent-elements", "find-median-from-data-stream"
]

def get_cached_slugs():
    #Returns a set of slugs that have their JSON data saved locally, used for caching and offline functionality
    if not os.path.exists(backend.WORKSPACE_DIR):
        return set()
    
    #Below look for .json files (e.g., two_sum.json)
    files = os.listdir(backend.WORKSPACE_DIR)


    #convert filename "two_sum.json" to slug "two-sum"...
    #for now ill just iterate our PROBLEM_SLUGS and check if their filename exists. this is a temp
    #solution until I implement dynamic slugs
    downloaded = set()
    for slug in PROBLEM_SLUGS:
        filename = f"{slug.replace('-', '_')}.json"
        if filename in files:
            downloaded.add(slug)
    return downloaded

@app.route('/')
def index():
    #when the root is visited i just want to pass the downloaded slugs to the front end
    downloaded = get_cached_slugs()
    return render_template('index.html', problems=PROBLEM_SLUGS, downloaded=downloaded)

@app.route('/api/load/<slug>')
def load_problem(slug):
    """
    my smart load system:
    check if slug.json exists locally.
    if YES: Load from disk this is for making the project work offline
    if NO: Fetch the problem online and save  to disk then return
    """


    try:
        if not os.path.exists(backend.WORKSPACE_DIR):
            os.makedirs(backend.WORKSPACE_DIR)

        filename_base = slug.replace('-', '_')
        json_path = os.path.join(backend.WORKSPACE_DIR, f"{filename_base}.json")
        py_path = os.path.join(backend.WORKSPACE_DIR, f"{filename_base}.py")
        
        data = None
        source = "Network"

        #first things first, try the local cache
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                source = "Local Cache"
            except:
                pass # If corrupt, fall back to network

        #if it doesnt have it, fallback to network
        if not data:
            data = backend.fetch_problem(slug)
            if not data:
                return jsonify({"error": "Problem not found"}), 404
            
            #save it to the cache
            with open(json_path, 'w') as f:
                json.dump(data, f)

        # finally, double check if the python file exists
        #(even if we have JSON, the user might have deleted the .py file (whoops :D))
        snippet = next((s['code'] for s in data['codeSnippets'] if s['langSlug'] == 'python3'), None)
        
        msg = f"Loaded from {source}"
        if not os.path.exists(py_path):
            with open(py_path, "w") as f:
                f.write(snippet)
            msg += f" (Created {filename_base}.py)"
        else:
            msg += f" (Using existing {filename_base}.py)"

        return jsonify({
            "title": data['title'],
            "content": data['content'],
            "filepath": py_path,
            "message": msg,
            "testcases_raw": data['exampleTestcases']
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/open', methods=['POST'])
def open_vscode():
    filepath = request.json.get('filepath')
    if not filepath or not os.path.exists(filepath):
        return jsonify({"error": "File not found :((( "}), 400
    
    #I HAVENT TESTED THIS ON WINDOES, ONLY ON ARCH LINUX RUNNING HYPRLAND
    try:
        if sys.platform == "win32":
            subprocess.run(f"cmd /c {backend.VSCODE_BIN} {filepath}", shell=True)
        else:
            subprocess.run([backend.VSCODE_BIN, filepath])
        return jsonify({"status": "opened"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/run', methods=['POST'])
def run_tests():
    data = request.json
    slug = data.get('slug')
    filepath = data.get('filepath')
    raw_testcases = data.get('testcases')

    if not filepath or not os.path.exists(filepath):
        return jsonify({"output": "Error: File not found."})

    logs = []
    
    with open(filepath, 'r') as f:
        code = f.read()

    method_name, arg_count = backend.analyze_code_structure(code)
    if method_name == "unknown":
        return jsonify({"output": "Error: could not find 'class Solution' or method."})

    test_cases = backend.parse_test_inputs(raw_testcases, arg_count)
    logs.append(f"Running {len(test_cases)} test cases...")

    logs.append("Fetching community solution...")
    md_content = backend.fetch_community_solution(slug)
    reference_code = backend.extract_code_block(md_content) if md_content else None
    
    if reference_code:
        logs.append("Ground Truth loaded.")
    else:
        logs.append("Warning: No Ground Truth available.")

    full_script = backend.generate_test_script(filepath, method_name, test_cases, reference_code)

    try:
        res = subprocess.run([sys.executable, "-c", full_script], capture_output=True, text=True)
        output = "\n".join(logs) + "\n\n" + res.stdout
        if res.stderr:
            output += "\nRUNTIME ERROR:\n" + res.stderr
        return jsonify({"output": output})
    except Exception as e:
        return jsonify({"output": f"Execution Error: {e}"})

@app.route('/api/solution/<slug>')
def get_community_solution(slug):
    try:
        md_content = backend.fetch_community_solution(slug)
        if not md_content:
            return jsonify({"error": "Could not fetch solution."}), 404
        code_block = backend.extract_code_block(md_content)
        return jsonify({
            "raw_markdown": md_content,
            "clean_code": code_block if code_block else "Code extraction failed,(this seems to ahppen with some questions, and im working on a fix for this)"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)