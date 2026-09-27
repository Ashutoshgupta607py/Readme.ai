# ReadmeAI

An AI-powered desktop application built with Python and CustomTkinter to automatically scan local project directories and generate detailed, professional `README.md` documentation using various LLM providers.

## Problem & Solution

* **Problem**: Writing comprehensive, accurate project documentation manually is time-consuming and often inconsistent across codebases.
* **Solution**: **ReadmeAI** scans project folder structures and source files, combining file context with built-in prompts to generate detailed, standard-compliant `README.md` files through major LLM provider APIs.

## Features

* **Multi-Provider AI Integration**: Connects with Google Gemini, DeepSeek, Mistral, Meta Llama API, OpenAI, Anthropic, and OpenRouter.
* **Pre-configured Model Catalog**: Includes presets for specific models across providers:
  * **Google Gemini**: Gemini 3.6 Flash, Gemini 3.8 Flash
  * **DeepSeek**: DeepSeek V4 Pro, DeepSeek V4 Flash
  * **Mistral**: Mistral Large, Mistral Small
  * **Meta Llama API**: Llama 4 Maverick, Llama 4 Scout
  * **OpenAI**: ChatGPT 4o mini, ChatGPT 4o
  * **Anthropic**: Claude Opus 4.1, Claude Sonnet 4
  * **OpenRouter**: DeepSeek R1, GPT-4o mini, Claude Opus
* **Dual Prompt Modes**: Includes pre-configured prompt modes for **Advertisement** (promotional READMEs) and **Exhibition** (showcase/exhibition READMEs).
* **Automated Project Scanning**: Recursively scans target directories while filtering out standard build artifacts and environment folders (`.git`, `node_modules`, `.venv`, `__pycache__`, etc.).
* **Detailed API Error Reporting**: Catches and interprets API error responses, formatting specific error messages for status codes like HTTP 401, 402, 403, and 429.
* **Desktop Application**: Graphical UI built using CustomTkinter with PyInstaller executable output (`dist/ReadmeAI.exe`).

## How It Works

1. **Folder Scanning**: The user selects a target project directory. ReadmeAI traverses the tree while skipping excluded development folders.
2. **Context Assembly**: File paths and relative project structures are aggregated into a unified context payload along with the chosen mode prompt.
3. **LLM Querying**: The application initializes the selected provider's SDK client using the provided API key and sends the prompt payload to the requested model.
4. **Markdown Generation**: The generated text is returned and rendered in the GUI for review.

## Technologies

| Category | Technology / Library |
| :--- | :--- |
| **Language** | Python |
| **GUI Framework** | CustomTkinter (`customtkinter`), Tkinter (`tkinter`) |
| **Packaging** | PyInstaller (`dist/ReadmeAI.exe`, `ReadmeAI.spec`) |
| **Supported Provider SDKs** | `google-genai`, `mistralai`, `openai`, `anthropic`, `openrouter` |

## Requirements

* **Executable**: Windows environment for running `dist/ReadmeAI.exe`.
* **Source Execution**: Python 3 runtime along with required dependencies depending on the provider chosen:
  * `customtkinter`
  * `google-genai` (for Google Gemini)
  * `mistralai` (for Mistral)
  * `openai` (for OpenAI, DeepSeek, and Meta Llama API)
  * `anthropic` (for Anthropic)
  * `openrouter` (for OpenRouter)

## Installation & Setup

### Running Pre-Built Executable
Run the pre-compiled binary directly:
```cmd
dist\ReadmeAI.exe
```

### Running Source Code
1. Clone or download the repository files.
2. Install the required Python packages:
   ```bash
   pip install customtkinter google-genai mistralai openai anthropic openrouter
   ```
3. Run the main script:
   ```bash
   python generator.py
   ```

## Configuration

All configuration is managed directly through the graphical user interface:

* **API Key**: Enter the API key associated with your selected provider account.
* **Provider & Model**: Select your preferred AI provider and model from the catalog.
* **Mode**: Choose between `advertisement` and `exhibition` pre-prompt options.
* **Folder Path**: Select the target repository folder to analyze.

## Usage

1. Launch `dist/ReadmeAI.exe` or execute `python generator.py`.
2. Input your API key into the designated field.
3. Choose the provider (e.g., `Google Gemini`) and model (e.g., `Gemini 3.6 Flash`).
4. Select the prompt generation mode (`advertisement` or `exhibition`).
5. Browse and select the project directory you want to generate documentation for.
6. Trigger generation to receive the compiled `README.md` output.

## Practical Demo Flow (30–60 Seconds)

1. **Launch**: Double-click `dist/ReadmeAI.exe` to open the interface.
2. **Credentials & Model**: Enter a Google Gemini API key, leave the provider as `Google Gemini`, and select `Gemini 3.6 Flash`.
3. **Select Target**: Click the folder selection button and pick a local software repository.
4. **Choose Mode**: Select `Exhibition` mode.
5. **Generate**: Click to generate documentation. ReadmeAI processes the project structure, calls the Gemini API, and displays the formatted markdown content in the interface.

## Project Structure

```text
Readme.ai/
├── dist/
│   └── ReadmeAI.exe          # Compiled standalone executable
├── build/
│   └── ReadmeAI/             # PyInstaller compilation files
├── generator.py              # Application source code and GUI engine
├── ReadmeAI.spec             # PyInstaller build specification
├── README.md                 # Project documentation file
├── .gitignore                # Git exclusion rules
└── .gitattributes            # Git tracking settings
```

## Real-World Uses

* **Repository Onboarding**: Quickly produce standardized `README.md` files for new or undocumented projects.
* **Project Exhibition**: Generate showcase-ready documentation formatted specifically for project fairs, hackathons, or software demonstrations.
* **Model Benchmarking**: Compare documentation output across multiple LLM models using identical folder contexts.

## Future Ideas (Clearly Labeled)

*Note: The features listed below are not currently implemented in the codebase and represent future development ideas.*

* **Direct File Export**: Add a button to save the generated README output directly to a file on disk.
* **Custom System Prompts**: Allow users to edit system prompt templates within the GUI.
* **Token Usage Counter**: Display estimated context token counts before making API calls.

## FAQ

**Q: Which directories are excluded during the folder scan?**  
A: ReadmeAI automatically skips `.git`, `.github`, `__pycache__`, `node_modules`, `.venv`, `venv`, `env`, `.idea`, and `.vscode`.

**Q: Is an API key required to run the application?**  
A: Yes, you must supply a valid API key for the AI provider you select in the interface.

**Q: How are API errors handled?**  
A: The application captures HTTP status codes (such as 401 Unauthorized, 402 Payment Required, 403 Forbidden, and 429 Rate Limit Exceeded) and displays user-friendly error explanations.

## Credits

* **CustomTkinter**: GUI library used for modern desktop interface components.
* **PyInstaller**: Packaging tool used to compile the project into `dist/ReadmeAI.exe

**Note:** It works best with gemini 3.6 flash
