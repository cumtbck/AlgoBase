# CLAUDE.md: 

## 1\. Project Overview

**Project Name:** CLAUDE (Code-Library-Aware Unified Development Environment)

**Project Vision:** To create an intelligent codebase management application for the Mac OS platform. This software will be deeply integrated with a local Large Language Model (LLM) capable of understanding and learning the style and structure of a user's codebase. The goal is to provide highly customized code generation, querying, and management capabilities. CLAUDE aims to be a developer's "second brain," significantly boosting coding efficiency and quality while ensuring code privacy.

**Core Features:**

  * **Style-Aware Code Generation:** Generate solutions to programming problems (e.g., algorithm questions) that conform to the style of the existing codebase.
  * **Context-Aware Code Implementation:** When generating code, prioritize the use and reference of existing modules, functions, and patterns within the codebase (Retrieval-Augmented Generation, RAG).
  * **Continuous Evolution:** Automatically or manually synchronize changes from the codebase and use this incremental data to continuously fine-tune the local LLM.
  * **Hybrid Storage:** Support storing the codebase index and metadata either locally or in the cloud to meet diverse user needs for security and collaboration.
  * **Native macOS Experience:** Provide a smooth, aesthetically pleasing user interface that adheres to macOS design principles.

## 2\. Core Requirements & Technical Implementation Analysis

### 2.1 Intelligent Code Generation

#### Requirement 1.1: Style Consistency

  * **Description:** Generated code should align with the target codebase in terms of naming conventions, indentation, commenting style, design patterns, etc.
  * **Technical Implementation:**
    1.  **Code Style Analysis:** During the indexing phase, use static analysis tools (e.g., rule sets from `ESLint`, `Flake8` for Python, `Clang-Format` for C/C++) or custom scripts to extract code style features.
    2.  **Prompt Engineering:** Inject style guidelines directly into the prompt sent to the LLM. For instance, provide a few examples of style-compliant code in a few-shot prompt.
    3.  **LLM Fine-tuning:** This is the most effective approach. Use the existing code in the library as a high-quality dataset to fine-tune a base code model, making it inherently generate code in the desired style.
    4.  **Post-processing:** Apply formatters like `Prettier` or `Black` to the LLM's output to enforce a consistent basic style.

#### Requirement 1.2: Context-Awareness (RAG)

  * **Description:** When a user asks for a specific implementation (e.g., "implement a user authentication middleware for aiohttp"), the result should be primarily based on or reuse similar implementations if they exist in the codebase.
  * **Technical Implementation:** **Retrieval-Augmented Generation (RAG)**
    1.  **Codebase Indexing:**
          * **Chunking:** Split code files into logical units (functions, classes).
          * **Embedding:** Use a code embedding model (e.g., `CodeBERT`, `GraphCodeBERT`, or general-purpose models like `BGE`, `M3E`) to convert code chunks into vectors.
          * **Vector Database:** Store the code chunks and their corresponding vectors in a local vector database.
              * **Choices:** `ChromaDB`, `LanceDB`, or `FAISS` (integrated within LangChain/LlamaIndex) are excellent lightweight options for local deployment.
    2.  **Retrieval:**
          * When a user submits a query, convert the query into a vector as well.
          * Perform a similarity search in the vector database to find the top-N most relevant code chunks.
    3.  **Generation:**
          * Combine the user's original query and the retrieved code chunks into an enhanced prompt.
          * **Example Prompt Structure:**
            ```
            [SYSTEM INSTRUCTION]
            You are a senior software engineer. Based on the user's question and the provided code context, generate a high-quality solution. Prioritize using the functions and classes from the context.

            [CODE CONTEXT]
            {retrieved_code_chunk_1}
            {retrieved_code_chunk_2}
            ...

            [USER QUESTION]
            {user_query}

            [ANSWER]
            ```
          * Send this enhanced prompt to the local LLM for generation.

### 2.2 Continuous Learning & Evolution

  * **Description:** The application must detect updates to the codebase and use these changes to optimize the large model.
  * **Technical Implementation:**
    1.  **Detecting Codebase Changes:**
          * **Git Integration:** Use `git hooks` (e.g., `post-commit`) to trigger update scripts. This is the most precise method.
          * **File System Watching:** Use a library like `watchdog` (Python) or macOS's native FSEvents API to monitor the codebase directory for changes.
    2.  **Incremental Indexing:** When a file change is detected (add, modify, delete), only re-chunk, re-embed, and update the index for the affected files in the vector database.
    3.  **Continuous Fine-tuning:**
          * **Data Preparation:** Periodically (e.g., weekly or monthly), collect high-quality new or modified code snippets and format them into a dataset suitable for fine-tuning (e.g., instruction-response pairs).
          * **Fine-tuning Process:** Launch a background fine-tuning task. Use frameworks like `Hugging Face TRL`, `Axolotl`, or `LoRAX` to perform Parameter-Efficient Fine-tuning (PEFT), such as LoRA or QLoRA. This can be done on consumer hardware without overwriting the entire base model.
          * **Model Versioning:** The fine-tuning process generates a new LoRA adapter. The application should support loading and switching between different model adapters, allowing users to compare results or roll back.

### 2.3 Flexible Storage Solutions

  * **Description:** Data such as the vector index and model adapters can be stored either locally or in the cloud.
  * **Technical Implementation:** **Storage Abstraction Layer**
    1.  **Define a Unified Interface:** Create an abstract base class (or interface) for storage services, defining methods like `save`, `load`, `list`, and `delete`.
    2.  **Implement Concrete Drivers:**
          * **Local Storage Driver:** Implement the interface using local file system APIs. The storage path can be configured in the application's settings (e.g., `~/.claude/data`).
          * **Cloud Storage Driver (Optional):** Implement drivers for major cloud services like Amazon S3 or Google Cloud Storage using their respective SDKs (e.g., `boto3` for AWS). Users would provide API keys and bucket information in the settings.
    3.  **Configuration Switching:** The application will load the appropriate storage driver at startup based on user configuration.

### 2.4 Platform Compatibility: Mac OS

  * **Description:** The application will run as a standard Mac OS desktop application.
  * **Technical Implementation:**
    1.  **Application Framework:**
          * **SwiftUI / AppKit (Native):** The best choice for a seamless user experience, optimal system integration (menu bar, notifications), and the highest performance.
          * **Electron / Tauri (Hybrid):** A faster development option if the team is more familiar with web technologies (React, Vue). Tauri is more lightweight than Electron.
    2.  **Backend & Model Integration:**
          * **Core Logic:** The core LLM inference, RAG, and fine-tuning logic should be implemented in **Python** due to its rich ecosystem (`Hugging Face`, `PyTorch`, `LangChain`, etc.).
          * **Communication:** The front-end UI (Swift/JS) can communicate with the Python backend via:
              * **Local HTTP Server:** Python runs a lightweight web server (e.g., `FastAPI`, `Flask`), and the front end makes HTTP requests.
              * **PythonKit (for Swift):** For a tighter integration with a SwiftUI front end, `PythonKit` allows calling Python code directly from Swift.
              * **gRPC:** For high-performance inter-process communication.
    3.  **Local LLM Deployment:**
          * **Model Selection:** Prioritize code-specialized models available in quantized formats like GGUF. Good candidates include `Code Llama`, `DeepSeek Coder`, or `Mistral` in smaller parameter sizes (7B, 13B).
          * **Inference Engine:**
              * **Llama.cpp:** A C++ implementation with extremely high performance and native Metal support on Apple Silicon, making it the top choice for macOS.
              * **Ollama:** A user-friendly wrapper around Llama.cpp that provides a simple REST API service, greatly simplifying model management. **Highly recommended as the initial solution.**
              * **MLX:** Apple's official machine learning framework optimized for Apple Silicon. It has huge performance potential but a newer ecosystem.

## 3\. Recommended Tech Stack

  * **Frontend (UI):** **SwiftUI** (for a native experience) or **Tauri** (for cross-platform and rapid development).
  * **Backend / Core Logic:** **Python 3.10+**
  * **LLM Orchestration:** **LangChain** or **LlamaIndex**
  * **Local LLM Service:** **Ollama** (which wraps Llama.cpp)
  * **Vector Database:** **ChromaDB** or **LanceDB**
  * **LLM Fine-tuning Framework:** **Hugging Face TRL (Transformer Reinforcement Learning)**
  * **File Monitoring:** **Watchdog** (for Python)
  * **Python-Swift Bridge:** **PythonKit** or a **local FastAPI server**

## 4\. Development Workflow & Agent Guidance

**Phase 1: Core Functionality MVP (Minimum Viable Product)**

  * **Agent Task 1: Environment Setup & Model Execution**
      * [ ] Install Python and required libraries (`Ollama`, `LangChain`, `ChromaDB`).
      * [ ] Use Ollama to download and run a code model (e.g., `codellama:7b`). Test API interaction successfully.
  * **Agent Task 2: Implement Basic RAG Flow (CLI)**
      * [ ] Develop a Python script that targets a local codebase directory.
      * [ ] Implement the indexing function: traverse directory -\> chunk code -\> generate embeddings -\> store in ChromaDB.
      * [ ] Implement the query function: receive user input -\> retrieve relevant code -\> build prompt -\> call Ollama API -\> print result.
      * [ ] Validate the entire core workflow via a Command-Line Interface (CLI) first.
  * **Agent Task 3: Build Basic Mac OS UI**
      * [ ] Create a simple windowed application using SwiftUI or Tauri.
      * [ ] Include an input field for questions, an area to display the codebase path, and a view to show the LLM's response.
      * [ ] Implement communication between the UI and the backend Python script.

**Phase 2: Feature Enhancement & UX Optimization**

  * **Agent Task 4: Implement Automatic Indexing on Code Changes**
      * [ ] Integrate the `watchdog` library.
      * [ ] Start a background thread to monitor the codebase directory.
      * [ ] Automatically update the vector index when files change.
  * **Agent Task 5: Implement Storage Abstraction Layer**
      * [ ] Design the storage interface.
      * [ ] Implement the local file system storage driver.
      * [ ] Add an option in the app settings to allow users to configure the data storage path.
  * **Agent Task 6: Optimize Code Generation Experience**
      * [ ] Add Markdown rendering with syntax highlighting to the UI for displaying code.
      * [ ] Add a "Copy Code" button.
      * [ ] Research prompt engineering techniques to improve context integration and generation quality.

**Phase 3: Advanced Features - Continuous Evolution**

  * **Agent Task 7: Develop the Continuous Fine-tuning Module**
      * [ ] Design a data collection strategy to filter high-quality training samples from codebase changes.
      * [ ] Write a LoRA fine-tuning script based on the `TRL` and `PEFT` libraries.
      * [ ] Add a UI element to manually trigger or schedule the fine-tuning process.
  * **Agent Task 8: Model and Adapter Management**
      * [ ] Implement functionality to load a base model with different LoRA adapters.
      * [ ] Allow users to switch between different fine-tuned versions (adapters).
  * **Agent Task 9: Cloud Storage Sync (Optional)**
      * [ ] Implement a driver for S3 or another cloud storage provider.
      * [ ] Allow users to configure cloud sync to share data across multiple devices.

## 5\. Key Challenges & Solutions

  * **Challenge: Local Model Performance & Resource Consumption**
      * **Solution:**
          * Use quantized models (e.g., 4-bit/5-bit GGUF).
          * Leverage the Metal acceleration provided by Llama.cpp/Ollama/MLX.
          * Provide performance monitoring within the app so users are aware of resource usage.
  * **Challenge: RAG Retrieval Quality**
      * **Solution:**
          * Optimize code chunking strategies (e.g., by function or semantic meaning).
          * Experiment with different code embedding models.
          * Implement more advanced retrieval techniques like HyDE (Hypothetical Document Embeddings) or add a reranking step.
  * **Challenge: Fine-tuning Complexity and Stability**
      * **Solution:**
          * Initially, offer fine-tuning as an advanced, optional feature.
          * Provide clear guidance on the required data volume and potential risks.
          * Ensure the fine-tuning process runs asynchronously in the background so it doesn't disrupt the main application.
  * **Challenge: Code Privacy and Security**
      * **Solution:**
          * Emphasize the "local-first" and "data never leaves your machine" advantages in all project marketing.
          * For the optional cloud storage feature, be transparent about what data is uploaded and offer end-to-end encryption options.
