
import os
import sys
import threading
from tkinter import messagebox, filedialog
import customtkinter as ctk


def _set_app_icon(window):
    """Apply the bundled app icon in both source and PyInstaller builds."""
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    icon_path = os.path.join(base_dir, "logo.ico")
    if os.path.exists(icon_path):
        window.iconbitmap(icon_path)

try:
    from google import genai
except ImportError:
    genai = None

try:
    import mistralai.client as mistral_sdk
except ImportError:
    mistral_sdk = None

try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import openrouter
except ImportError:
    openrouter = None


# ============================================================
# VARIABLES
# ============================================================

# Advertisement-friendly pre-prompt
x = """
Write a polished, advertiser-friendly README.md for this project. Inspect the supplied files and use them as the source of truth. Never invent features, dependencies, commands, models, compatibility, screenshots, URLs, statistics, or security claims; do not expose secrets.

Make it engaging and easy to scan, with a strong title/tagline, concise project description, real features, requirements, accurate installation and usage instructions, configuration, relevant screenshots/assets, project structure, troubleshooting, license, and credits where supported. Include other sections only when useful and verifiable. Use concise headings, short paragraphs, lists, tables, and code blocks. Keep the tone professional and trustworthy, with restrained visual styling and a natural call to action.

Check that names, paths, commands, dependencies, and claims match the files. Return only complete README.md content, without an outer code fence.
""".strip()


# Exhibition-friendly pre-prompt
y = """
Write a clear, visually engaging README.md for an exhibition or project showcase. Inspect the supplied files and describe only what they verify; never invent features, technologies, commands, screenshots, URLs, statistics, results, or security claims. Do not expose secrets.

Explain the problem, solution, actual features, how it works, technologies, setup, configuration, usage, and a practical 30-60 second demo flow. Include relevant screenshots, project structure, real-world uses, future ideas (clearly labeled), FAQ, license, and credits only when supported. Make it understandable to technical and non-technical readers, using concise sections, short paragraphs, tables, and code blocks without excessive decoration.

Verify claims, file paths, and commands against the supplied files. Return only complete README.md content, without an outer code fence.
""".strip()


# User API key
api = ""

# Final message sent to the selected provider
message = ""


MODEL_CATALOG = {
    "Google Gemini": {"Gemini 3.6 Flash": "gemini-3.6-flash", "Gemini 3.8 Flash": "gemini-3.8-flash"},
    "DeepSeek": {"DeepSeek V4 Pro": "deepseek-v4-pro", "DeepSeek V4 Flash": "deepseek-v4-flash"},
    "Mistral": {"Mistral Large": "mistral-large-latest", "Mistral Small": "mistral-small-latest"},
    "Meta Llama API": {"Llama 4 Maverick": "Llama-4-Maverick-17B-128E-Instruct-FP8", "Llama 4 Scout": "Llama-4-Scout-17B-16E-Instruct-FP8"},
    "OpenAI": {"ChatGPT 4o mini": "gpt-4o-mini", "ChatGPT 4o": "gpt-4o"},
    "Anthropic": {"Claude Opus 4.1": "claude-opus-4-1", "Claude Sonnet 4": "claude-sonnet-4-0"},
    "OpenRouter": {"DeepSeek R1 (OpenRouter)": "deepseek/deepseek-r1", "GPT-4o mini (OpenRouter)": "openai/gpt-4o-mini", "Claude Opus (OpenRouter)": "anthropic/claude-opus-4"},
}
MODEL_ID = MODEL_CATALOG["Google Gemini"]["Gemini 3.6 Flash"]
selected_provider = "Google Gemini"
MAX_RETRIES = 3


# Currently selected mode
selected_mode = "advertisement"

# Currently selected folder
selected_folder = ""


# ============================================================
# PROVIDER CLIENTS
# ============================================================

def _format_api_error(provider, status, detail):
    """Make common API errors easier to act on."""
    if status == 429:
        if provider == "Google Gemini":
            reason = (
                "Gemini rate/quota limit reached (429). Limits are attached to your "
                "Google AI Studio project, not an individual API key. Wait for the "
                "limit to reset or check the project's Rate Limits page in AI Studio."
            )
        else:
            reason = (
                f"{provider} rate limit reached (429). Wait and retry, reduce "
                "request frequency, or check the provider's usage and limits page."
            )
        return f"{reason}\n\nProvider details: {detail}"
    if status in (401, 403):
        return (
            f"{provider} rejected the API key or its permissions (HTTP {status}). "
            f"Check the key and selected model.\n\nProvider details: {detail}"
        )
    if status == 402:
        return (
            f"{provider} requires available credits or an active billing plan. "
            f"Check your provider account.\n\nProvider details: {detail}"
        )
    return f"{provider} API error ({status}): {detail}"


def _raise_provider_error(provider, exc):
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status is None and getattr(exc, "code", None) == 429:
        status = 429
    if status in (401, 402, 403, 429):
        raise RuntimeError(_format_api_error(provider, status, str(exc))) from None
    raise RuntimeError(f"{provider} API error: {exc}") from None


def _require_response_text(value, provider):
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(f"{provider} returned an empty response.")
    return value


def _response_text(content, provider):
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
            else:
                parts.append(getattr(item, "text", ""))
        content = "".join(parts)
    return _require_response_text(content, provider)


def generate_response(api_key, prompt_text):
    provider = selected_provider
    model = MODEL_ID

    if provider == "Google Gemini":
        if genai is None:
            raise RuntimeError("Gemini support requires: pip install google-genai")
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model, contents=prompt_text)
            return _require_response_text(getattr(response, "text", None), provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    elif provider == "Mistral":
        if mistral_sdk is None:
            raise RuntimeError("Mistral support requires: pip install mistralai")
        try:
            client = mistral_sdk.Mistral(api_key=api_key)
            response = client.chat.complete(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
            )
            choices = getattr(response, "choices", None)
            if not choices:
                raise RuntimeError("Mistral returned an invalid response.")
            message = getattr(choices[0], "message", None)
            return _response_text(getattr(message, "content", None), provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    elif provider == "Anthropic":
        if anthropic is None:
            raise RuntimeError("Anthropic support requires: pip install anthropic")
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model,
                max_tokens=8192,
                messages=[{"role": "user", "content": prompt_text}],
            )
            text_blocks = [
                getattr(block, "text", "")
                for block in response.content
                if getattr(block, "type", None) == "text"
            ]
            return _response_text(text_blocks, provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    elif provider == "DeepSeek":
        if openai is None:
            raise RuntimeError("DeepSeek support requires: pip install openai")
        try:
            client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
            )
            return _response_text(response.choices[0].message.content, provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    elif provider == "Meta Llama API":
        if openai is None:
            raise RuntimeError("Meta Llama API support requires: pip install openai")
        try:
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.llama.com/compat/v1",
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
            )
            return _response_text(response.choices[0].message.content, provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    elif provider == "OpenAI":
        if openai is None:
            raise RuntimeError("OpenAI support requires: pip install openai")
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt_text}],
            )
            return _response_text(response.choices[0].message.content, provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    elif provider == "OpenRouter":
        if openrouter is None:
            raise RuntimeError("OpenRouter support requires: pip install openrouter")
        try:
            with openrouter.OpenRouter(api_key=api_key) as client:
                response = client.chat.send(
                    model=model,
                    messages=[{"role": "user", "content": prompt_text}],
                )
            return _response_text(response.choices[0].message.content, provider)
        except Exception as exc:
            _raise_provider_error(provider, exc)

    else:
        raise RuntimeError(f"No API integration is configured for {provider}.")


# ============================================================
# FOLDER SCANNER
# ============================================================

def scan_folder(folder_path):

    files = []

    ignored_directories = {
        ".git",
        ".github",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".idea",
        ".vscode",
    }

    for root, directories, filenames in os.walk(folder_path):

        # Prevent scanning unnecessary folders
        directories[:] = [
            directory
            for directory in directories
            if directory not in ignored_directories
        ]

        for filename in filenames:

            full_path = os.path.join(
                root,
                filename
            )

            relative_path = os.path.relpath(
                full_path,
                folder_path
            )

            files.append(
                relative_path
            )

    return files


# ============================================================
# READ TEXT FILES FROM PROJECT
# ============================================================

def read_project_files(folder_path):

    supported_extensions = {
        ".py",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".scss",
        ".json",
        ".md",
        ".txt",
        ".yaml",
        ".yml",
        ".xml",
        ".toml",
        ".ini",
        ".cfg",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".swift",
        ".kt",
        ".kts",
        ".sql",
        ".sh",
        ".bat",
        ".ps1",
    }

    ignored_directories = {
        ".git",
        ".github",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".idea",
        ".vscode",
    }

    project_content = []
    max_total_chars = 40_000
    max_file_chars = 12_000
    total_chars = 0

    for root, directories, filenames in os.walk(folder_path):

        directories[:] = [
            directory
            for directory in directories
            if directory not in ignored_directories
        ]

        for filename in filenames:

            extension = os.path.splitext(
                filename
            )[1].lower()

            if extension not in supported_extensions:
                continue

            full_path = os.path.join(
                root,
                filename
            )

            relative_path = os.path.relpath(
                full_path,
                folder_path
            )

            try:

                with open(
                    full_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:

                    content = file.read(max_file_chars + 1)

                if len(content) > max_file_chars:
                    content = content[:max_file_chars] + "\n[File truncated]"

                remaining_chars = max_total_chars - total_chars
                if remaining_chars <= 0:
                    project_content.append("\n[Project content limit reached; remaining files omitted]\n")
                    return "\n".join(project_content)

                if len(content) > remaining_chars:
                    content = content[:remaining_chars] + "\n[Project content limit reached]"

                total_chars += len(content)

                project_content.append(
                    f"\n--- FILE: {relative_path} ---\n"
                    f"{content}\n"
                )

            except Exception:
                continue

    return "\n".join(project_content)


# ============================================================
# CREATE README PROMPT
# ============================================================

def create_readme_prompt(folder_path, mode_prompt):

    file_list = scan_folder(
        folder_path
    )

    project_content = read_project_files(
        folder_path
    )

    max_listed_files = 100
    listed_files = file_list[:max_listed_files]
    filename_text = "\n".join(
        f"- {filename}"
        for filename in listed_files
    )
    if len(file_list) > max_listed_files:
        filename_text += f"\n- ... and {len(file_list) - max_listed_files} more files"

    prompt = f"""
{mode_prompt}

You are generating a professional README.md for a software/project folder.

IMPORTANT:
- Analyze the project files provided below.
- Understand what the project actually does.
- Do not invent features that are not supported by the project files.
- Do not claim that something works if the code does not support it.
- Create a clean, professional README.md.
- Return ONLY the README.md contents.
- Do NOT wrap the answer in ```markdown or ```.

The README should include appropriate sections such as:

# Project Name

A short description.

## Features

List the actual features found in the project.

## Requirements

List required software, packages, dependencies, or environment requirements when they can be determined.

## Installation

Explain how to install and configure the project.

## Usage

Explain how to use the project.

## Configuration

Explain important configuration options.

## Project Structure

Show the important project files and folders.

## Examples

Include useful examples if the project supports them.

## Notes

Include relevant limitations or important information.

## License

Only include a license section if a license can be identified.
Do not invent a license.

PROJECT FILES:

{filename_text}

PROJECT SOURCE CONTENT:

{project_content}
"""

    return prompt


# ============================================================
# API KEY WINDOW
# ============================================================

class ApiKeyDialog(ctk.CTkToplevel):

    def __init__(self, master):

        super().__init__(master)

        _set_app_icon(self)

        self.title("Choose AI provider and model")

        self.geometry(
            "460x390"
        )

        self.resizable(
            False,
            False
        )

        self.result_api_key = None
        self.provider_var = ctk.StringVar(value="Google Gemini")
        self.model_var = ctk.StringVar(value="Gemini 3.6 Flash")

        self.transient(
            master
        )

        self.grab_set()

        ctk.CTkLabel(
            self,
            text="AI Provider and Model",
            font=ctk.CTkFont(
                size=18,
                weight="bold"
            )
        ).pack(
            pady=(25, 5)
        )

        ctk.CTkLabel(
            self,
            text="Choose a provider and model",
            text_color="gray"
        ).pack(
            pady=(0, 15)
        )

        self.provider_menu = ctk.CTkOptionMenu(self, variable=self.provider_var,
            values=list(MODEL_CATALOG), command=self._provider_changed, width=340)
        self.provider_menu.pack(pady=6)
        self.model_menu = ctk.CTkOptionMenu(self, variable=self.model_var,
            values=list(MODEL_CATALOG["Google Gemini"]), width=340)
        self.model_menu.pack(pady=6)
        self.api_entry = ctk.CTkEntry(
            self,
            width=340,
            show="*",
            placeholder_text="Selected provider API key"
        )

        self.api_entry.pack(
            pady=8
        )

        self.error_label = ctk.CTkLabel(
            self,
            text="",
            text_color="tomato"
        )

        self.error_label.pack()

        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        button_frame.pack(
            pady=20
        )

        ctk.CTkButton(
            button_frame,
            text="Continue",
            width=140,
            command=self._on_continue
        ).pack(
            side="left",
            padx=8
        )

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=100,
            fg_color="gray30",
            hover_color="gray20",
            command=self._on_cancel
        ).pack(
            side="left",
            padx=8
        )

        self.api_entry.bind(
            "<Return>",
            lambda _event: self._on_continue()
        )

        self.after(
            100,
            self.api_entry.focus
        )

    def _on_continue(self):

        key = self.api_entry.get().strip()

        if not key:

            self.error_label.configure(
                text="API key cannot be empty."
            )

            return

        global selected_provider, MODEL_ID
        selected_provider = self.provider_var.get()
        MODEL_ID = MODEL_CATALOG[selected_provider][self.model_var.get()]
        self.result_api_key = key

        self.grab_release()

        self.destroy()

    def _on_cancel(self):

        self.result_api_key = None

        self.grab_release()

        self.destroy()

    def _provider_changed(self, provider):
        models = list(MODEL_CATALOG[provider])
        self.model_menu.configure(values=models)
        self.model_var.set(models[0])


# ============================================================
# GENERATOR WINDOW
# ============================================================

class GeneratorApp(ctk.CTk):

    def __init__(self):

        super().__init__()

        _set_app_icon(self)

        self.title(
            f"{selected_provider} Generator"
        )

        self.geometry(
            "760x700"
        )

        self.minsize(
            700,
            650
        )

        self._build_ui()

    # --------------------------------------------------------
    # BUILD UI
    # --------------------------------------------------------

    def _build_ui(self):

        ctk.CTkLabel(
            self,
            text=f"{selected_provider} Generator",
            font=ctk.CTkFont(
                size=21,
                weight="bold"
            )
        ).pack(
            pady=(20, 5)
        )

        ctk.CTkLabel(
            self,
            text=f"Provider: {selected_provider} | Model: {MODEL_ID}",
            text_color="gray"
        ).pack(
            pady=(0, 12)
        )

        # ====================================================
        # MODE SELECTOR
        # ====================================================

        ctk.CTkLabel(
            self,
            text="Generation Style",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(
            pady=(5, 5)
        )

        mode_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        mode_frame.pack(
            pady=5
        )

        self.mode_var = ctk.StringVar(
            value="advertisement"
        )

        self.ad_button = ctk.CTkRadioButton(
            mode_frame,
            text="Advertisement Friendly",
            variable=self.mode_var,
            value="advertisement",
            command=self._change_mode
        )

        self.ad_button.pack(
            side="left",
            padx=15
        )

        self.exhibition_button = ctk.CTkRadioButton(
            mode_frame,
            text="Exhibition Friendly",
            variable=self.mode_var,
            value="exhibition",
            command=self._change_mode
        )

        self.exhibition_button.pack(
            side="left",
            padx=15
        )

        self.mode_status = ctk.CTkLabel(
            self,
            text="Advertisement Friendly selected",
            text_color="gray"
        )

        self.mode_status.pack(
            pady=(2, 10)
        )

        # ====================================================
        # FOLDER
        # ====================================================

        folder_frame = ctk.CTkFrame(
            self
        )

        folder_frame.pack(
            fill="x",
            padx=30,
            pady=5
        )

        ctk.CTkButton(
            folder_frame,
            text="Select Project Folder",
            width=180,
            command=self._select_folder
        ).pack(
            side="left",
            padx=10,
            pady=10
        )

        self.folder_label = ctk.CTkLabel(
            folder_frame,
            text="No folder selected",
            text_color="gray",
            anchor="w"
        )

        self.folder_label.pack(
            side="left",
            padx=5
        )

        # ====================================================
        # NORMAL PROMPT
        # ====================================================

        ctk.CTkLabel(
            self,
            text="Prompt",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(
            anchor="w",
            padx=30,
            pady=(12, 3)
        )

        self.prompt_box = ctk.CTkTextbox(
            self,
            width=690,
            height=120
        )

        self.prompt_box.pack(
            padx=30
        )

        # ====================================================
        # BUTTONS
        # ====================================================

        button_frame = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        button_frame.pack(
            pady=15
        )

        self.generate_button = ctk.CTkButton(
            button_frame,
            text="Generate",
            width=150,
            command=self._on_generate
        )

        self.generate_button.pack(
            side="left",
            padx=8
        )

        self.readme_button = ctk.CTkButton(
            button_frame,
            text="Generate README.md",
            width=180,
            command=self._on_generate_readme
        )

        self.readme_button.pack(
            side="left",
            padx=8
        )

        # ====================================================
        # STATUS
        # ====================================================

        self.status_label = ctk.CTkLabel(
            self,
            text="",
            text_color="gray"
        )

        self.status_label.pack()

        # ====================================================
        # RESPONSE
        # ====================================================

        ctk.CTkLabel(
            self,
            text="Response",
            font=ctk.CTkFont(
                size=14,
                weight="bold"
            )
        ).pack(
            pady=(10, 5)
        )

        self.response_box = ctk.CTkTextbox(
            self,
            width=690,
            height=190
        )

        self.response_box.pack(
            padx=30,
            pady=(0, 20)
        )

        self.response_box.configure(
            state="disabled"
        )

    # ========================================================
    # MODE
    # ========================================================

    def _change_mode(self):

        global selected_mode

        selected_mode = self.mode_var.get()

        if selected_mode == "advertisement":

            self.mode_status.configure(
                text="Advertisement Friendly selected"
            )

        else:

            self.mode_status.configure(
                text="Exhibition Friendly selected"
            )

    # ========================================================
    # FOLDER SELECTION
    # ========================================================

    def _select_folder(self):

        global selected_folder

        folder = filedialog.askdirectory(
            title="Select Project Folder"
        )

        if not folder:
            return

        selected_folder = folder

        self.folder_label.configure(
            text=folder,
            text_color="white"
        )

        self.status_label.configure(
            text="Project folder selected.",
            text_color="lightgreen"
        )

    # ========================================================
    # GET CURRENT PRE-PROMPT
    # ========================================================

    def _get_pre_prompt(self):

        if selected_mode == "advertisement":
            return x

        return y

    # ========================================================
    # NORMAL GENERATION
    # ========================================================

    def _on_generate(self):

        global message

        user_prompt = self.prompt_box.get(
            "1.0",
            "end"
        ).strip()

        if not user_prompt:

            self.status_label.configure(
                text="Prompt cannot be empty.",
                text_color="tomato"
            )

            return

        pre_prompt = self._get_pre_prompt()

        message = (
            pre_prompt
            + "\n\n"
            + user_prompt
        )

        self.generate_button.configure(
            state="disabled"
        )

        self.readme_button.configure(
            state="disabled"
        )

        self.status_label.configure(
            text="Generating...",
            text_color="gray"
        )

        self._set_response("")

        thread = threading.Thread(
            target=self._run_generate,
            daemon=True
        )

        thread.start()

    # ========================================================
    # README GENERATION
    # ========================================================

    def _on_generate_readme(self):

        global message

        if not selected_folder:

            self.status_label.configure(
                text="Please select a project folder first.",
                text_color="tomato"
            )

            return

        self.generate_button.configure(
            state="disabled"
        )

        self.readme_button.configure(
            state="disabled"
        )

        self.status_label.configure(
            text="Scanning project and generating README...",
            text_color="gray"
        )

        self._set_response("")

        pre_prompt = self._get_pre_prompt()

        message = create_readme_prompt(
            selected_folder,
            pre_prompt
        )

        thread = threading.Thread(
            target=self._run_readme,
            daemon=True
        )

        thread.start()

    # ========================================================
    # NORMAL API THREAD
    # ========================================================

    def _run_generate(self):

        global api, message

        try:

            result = generate_response(
                api,
                message
            )

            self.after(
                0,
                self._on_success,
                result
            )

        except RuntimeError as e:

            self.after(
                0,
                self._on_error,
                str(e)
            )

    # ========================================================
    # README API THREAD
    # ========================================================

    def _run_readme(self):

        global api, message

        try:

            result = generate_response(
                api,
                message
            )

            # Remove accidental Markdown code fences
            result = result.strip()

            if result.startswith(
                "```markdown"
            ):

                result = result[
                    len("```markdown"):
                ].strip()

            elif result.startswith(
                "```"
            ):

                result = result[
                    len("```"):
                ].strip()

            if result.endswith(
                "```"
            ):

                result = result[
                    :-3
                ].strip()

            readme_path = os.path.join(
                selected_folder,
                "README.md"
            )

            with open(
                readme_path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write(result)

            self.after(
                0,
                self._on_readme_success,
                result,
                readme_path
            )

        except Exception as e:

            self.after(
                0,
                self._on_error,
                str(e)
            )

    # ========================================================
    # SUCCESS
    # ========================================================

    def _on_success(self, result):

        self.status_label.configure(
            text="Done.",
            text_color="lightgreen"
        )

        self._set_response(
            result
        )

        self.generate_button.configure(
            state="normal"
        )

        self.readme_button.configure(
            state="normal"
        )

    # ========================================================
    # README SUCCESS
    # ========================================================

    def _on_readme_success(
        self,
        result,
        readme_path
    ):

        self.status_label.configure(
            text=f"README.md created successfully!",
            text_color="lightgreen"
        )

        self._set_response(
            result
        )

        self.generate_button.configure(
            state="normal"
        )

        self.readme_button.configure(
            state="normal"
        )

        messagebox.showinfo(
            "README Created",
            "README.md has been created successfully.\n\n"
            f"Location:\n{readme_path}"
        )

    # ========================================================
    # ERROR
    # ========================================================

    def _on_error(self, error_text):

        self.status_label.configure(
            text="Error",
            text_color="tomato"
        )

        self._set_response(
            error_text
        )

        self.generate_button.configure(
            state="normal"
        )

        self.readme_button.configure(
            state="normal"
        )

    # ========================================================
    # RESPONSE BOX
    # ========================================================

    def _set_response(self, text):

        self.response_box.configure(
            state="normal"
        )

        self.response_box.delete(
            "1.0",
            "end"
        )

        self.response_box.insert(
            "1.0",
            text
        )

        self.response_box.configure(
            state="disabled"
        )


# ============================================================
# MAIN
# ============================================================

def main():

    global api

    ctk.set_appearance_mode(
        "dark"
    )

    ctk.set_default_color_theme(
        "blue"
    )

    # --------------------------------------------------------
    # API KEY WINDOW
    # --------------------------------------------------------

    root = ctk.CTk()

    root.withdraw()

    dialog = ApiKeyDialog(
        root
    )

    root.wait_window(
        dialog
    )

    api = dialog.result_api_key

    root.destroy()

    # User cancelled
    if not api:
        return

    # --------------------------------------------------------
    # NEW GENERATOR WINDOW
    # --------------------------------------------------------

    app = GeneratorApp()

    app.mainloop()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()

