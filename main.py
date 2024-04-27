import os
import shutil
import click
import http.server
import socketserver
import webbrowser


# HTML code
HTML_CODE = """
<!doctype html>
<html>
    <head>
        <!-- Recommended meta tags -->
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width,initial-scale=1.0">

        <!-- PyScript CSS -->
        <link rel="stylesheet" href="https://pyscript.net/releases/2024.1.1/core.css">
        <!-- CSS for examples -->
        <link rel="stylesheet" href="./assets/css/examples.css" />

        <!-- This script tag bootstraps PyScript -->
        <script type="module" src="https://pyscript.net/releases/2024.1.1/core.js"></script>

        <!-- for splashscreen -->
        <style>
            #loading { outline: none; border: none; background: transparent }
        </style>
        <script type="module">
            const loading = document.getElementById('loading');
            addEventListener('py:ready', () => loading.close());
            loading.showModal();
        </script>

        <title>Todo App</title>
        <link rel="icon" type="image/png" href="./assets/favicon.png" />

        <style>
            .line-through {
                text-decoration: line-through;
            }
        </style>
    </head>

    <body>
        <dialog id="loading">
            <h1>Loading...</h1>
        </dialog>

        <nav class="navbar" style="background-color: #000000">
            <div class="app-header">
                <a href="/">
                    <img src="./assets/logo.png" class="logo" />
                </a>
                <a class="title" href="" style="color: #f0ab3c">Todo App</a>
            </div>
        </nav>

        <section class="pyscript">
            <main>
                <section>
                    <div>
                        <h1>To Do List</h1>
                    </div>
                    <div>
                        <input id="new-task-content" type="text" />
                        <button id="new-task-btn" type="submit" py-click="add_task">
                            Add task
                        </button>
                    </div>

                    <div id="list-tasks-container"></div>

                    <template id="task-template">
                        <section class="task py-li-element">
                            <label class="flex items-center p-2">
                                <input style="vertical-align: middle;" type="checkbox" />
                                <p style="display: inline;"></p>
                            </label>
                        </section>
                    </template>
                </section>
            </main>

            <script type="py" src="./main.py" config="./pyscript.toml"></script>
        </section>
    </body>
</html>
"""

# Python code
PYTHON_CODE = """
from datetime import datetime as dt

from pyscript import document
from pyweb import pydom

tasks = []

def q(selector, root=document):
    return root.querySelector(selector)

# define the task template that will be use to render new templates to the page
# Note: We use JS element here because pydom doesn't fully support template 
#       elements now
task_template = pydom.Element(q("#task-template").content.querySelector(".task"))

task_list = pydom["#list-tasks-container"][0]
new_task_content = pydom["#new-task-content"][0]


def add_task(e):
    # ignore empty task
    if not new_task_content.value:
        return None

    # create task
    task_id = f"task-{len(tasks)}"
    task = {
        "id": task_id,
        "content": new_task_content.value,
        "done": False,
        "created_at": dt.now(),
    }

    tasks.append(task)

    # add the task element to the page as new node in the list by cloning from a
    # template
    task_html = task_template.clone()
    task_html.id = task_id

    task_html_check = task_html.find("input")[0]
    task_html_content = task_html.find("p")[0]
    task_html_content._js.textContent = task["content"]
    task_list.append(task_html)

    def check_task(evt=None):
        task["done"] = not task["done"]
        task_html_content._js.classList.toggle("line-through", task["done"])

    new_task_content.value = ""
    task_html_check._js.onclick = check_task


def add_task_event(e):
    if e.key == "Enter":
        add_task(e)


new_task_content.onkeypress = add_task_event
"""

# Example css code
EXAMPLE_CSS = """"
    body {
    margin: 0;
}

.pyscript {
    margin: 0.5rem;
}

html {
    font-family:
        ui-sans-serif,
        system-ui,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        Roboto,
        "Helvetica Neue",
        Arial,
        "Noto Sans",
        sans-serif,
        "Apple Color Emoji",
        "Segoe UI Emoji",
        "Segoe UI Symbol",
        "Noto Color Emoji";
    line-height: 1.5;
}

nav {
    position: sticky;
    width: 100%;
    top: 0;
    left: 0;
    z-index: 9999;
}

.logo {
    padding-right: 10px;
    font-size: 28px;
    height: 30px;
    max-width: inherit;
}

.title {
    text-decoration: none;
    text-decoration-line: none;
    text-decoration-style: initial;
    text-decoration-color: initial;
    font-weight: 400;
    font-size: 1.5em;
    line-height: 2em;
    white-space: nowrap;
}

.app-header {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
}

"""

#Pyscript.toml code
PYSCRIPTTOML = """
name = "Todo App"
description = "A simple To Do application written in PyScript."
"""

warning_comment = """
/**
 * WARNING: Do not remove the commented annotations above and below the classes.
 * They are used by the script to identify class definitions.
 */
"""

def find_html_files(directory):
    html_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    return html_files

def generate_custom_classes(html_files):
    custom_classes = {}
    for html_file in html_files:
        class_name = os.path.splitext(os.path.basename(html_file))[0].title().replace('_', '') + 'Component'
        with open(html_file, 'r') as file:
            html_content = file.read()
        custom_classes[class_name.lower()] = f"""\
class {class_name} extends HTMLElement {{
    constructor() {{
        super();
        this.innerHTML = `
                {html_content}
        `;
    }}
}}

customElements.define('{os.path.splitext(os.path.basename(html_file))[0].title().replace('_', '').lower()}-component', {class_name});
"""
    return custom_classes

def update_script_file(script_file, custom_classes):
    with open(script_file, 'r') as f:
        script_content = f.read()

    for class_name, class_content in custom_classes.items():
        start_annotation = f'//@ {class_name} start'
        end_annotation = f'//@ {class_name} end'
        start_index = script_content.find(start_annotation)
        end_index = script_content.find(end_annotation)

        if start_index != -1 and end_index != -1:
            class_content_start = start_index + len(start_annotation) + 1
            class_content_end = end_index
            existing_class_content = script_content[class_content_start:class_content_end].strip()
            new_class_content = class_content.strip()
            script_content = script_content.replace(existing_class_content, new_class_content)
        else:
            # If the class does not exist, add it to the end of the file
            script_content += f"\n\n{start_annotation}\n{class_content}\n{end_annotation}\n"

    with open(script_file, 'w') as f:
        f.write(script_content)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--name', prompt='Project name', help='Name of the project')
def generate(name):
    # Create a folder
    folder_name = name
    os.makedirs(folder_name, exist_ok=True)

    # Create assets folder
    assets_path = os.path.join(folder_name, "assets")
    os.makedirs(assets_path, exist_ok=True)

    # Write HTML code to index.html
    with open(os.path.join(folder_name, "index.html"), "w", encoding="utf-8") as f:
        f.write(HTML_CODE)

    # Write Python code to main.py
    with open(os.path.join(folder_name, "main.py"), "w", encoding="utf-8") as f:
        f.write(PYTHON_CODE)

    # Write javascript code to index.html
    with open(os.path.join(folder_name, "script.html"), "w", encoding="utf-8") as f:
        f.write(warning_comment)

    # Write Pyscript.toml code to main.py
    with open(os.path.join(folder_name, "pyscript.toml"), "w", encoding="utf-8") as f:
        f.write(PYSCRIPTTOML)

    # Write example.css
    css_folder_path = os.path.join(assets_path, "css")
    os.makedirs(css_folder_path, exist_ok=True)
    with open(os.path.join(css_folder_path, "examples.css"), "w", encoding="utf-8") as f:
        f.write(EXAMPLE_CSS)

    # Copy images
    # Assuming favicon.png and logo.png are in the same directory as the script
    favicon_source = "favicon.png"
    logo_source = "logo.png"
    favicon_destination = os.path.join(assets_path, "favicon.png")
    logo_destination = os.path.join(assets_path, "logo.png")
    if os.path.exists(favicon_source):
        shutil.copy(favicon_source, favicon_destination)
    if os.path.exists(logo_source):
        shutil.copy(logo_source, logo_destination)

    print("Project created successfully.")

@cli.command()
def run(port=3000):
    project_directory = os.getcwd()
    script_file = os.path.join(project_directory, 'script.js')
    html_files = find_html_files(project_directory)

    custom_classes = generate_custom_classes(html_files)


    update_script_file(script_file, custom_classes)


    index_file = os.path.join(project_directory, 'index.html')
    
    if not os.path.exists(index_file):
        print("Error: index.html file not found in the root directory.")
        return
    
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=project_directory, **kwargs)

    with socketserver.TCPServer(("", port), Handler) as httpd:
        print("Server started at port", port)
        webbrowser.open(f'http://localhost:{port}/index.html')
        httpd.serve_forever()


if __name__ == '__main__':
    cli()
