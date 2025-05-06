# Welcome to Paperlit

A powerful open-source platform for checking document originality and ensuring content integrity. Whether you're an educator, student, or researcher, Paperlit helps you maintain academic standards with ease.

## Key Features

*   **User Authentication:** Secure registration and login.
*   **Document Upload:** Upload documents for originality review.
*   **AI-Powered Similarity Detection:** Advanced AI-based detection of similarities with published materials.
*   **Document Management:** Upload, edit, and delete documents with a user-friendly interface.
*   **PDF Viewer with Highlights:** View documents with color-coded highlights showing similar content.
*   **Similarity Analysis:** Detailed sidebar showing matching content and similarity percentages.
*   **Modern UI:** Clean, responsive design using Tailwind CSS.

## Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/yourusernameKytonThaundi/paperlit.git # Replace with your repo URL if forked
    cd paperlit
    ```

2.  Create a virtual environment and activate it:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  Run the setup script to install dependencies and set up the application:
    ```bash
    python setup.py
    ```
    This will:
    - Install all required Python packages
    - Create necessary directories
    - Download and set up PDF.js for document viewing
    - Configure the application

4.  **Environment Configuration:**
    *   Copy the example environment file: `cp .env.example .env` (Create `.env.example` if it doesn't exist)
    *   Edit the `.env` file to set your `SECRET_KEY`, `DATABASE_URL`, and optionally `UPLOAD_FOLDER`.
    *   The `DATABASE_URL` should look like: `postgresql://user:password@host:port/database`
    *   If `UPLOAD_FOLDER` is not set, it defaults to an `uploads` directory in the project root.

5.  **Database Setup (PostgreSQL):**
    *   Ensure PostgreSQL is installed and running.
    *   Create the database and user specified in your `.env` file.
    ```sql
    -- Example SQL commands (adjust user/db name as needed)
    CREATE DATABASE paperlit_db;
    CREATE USER paperlit_user WITH PASSWORD 'your_secure_password';
    GRANT ALL PRIVILEGES ON DATABASE paperlit_db TO paperlit_user;
    ```

6.  **Initialize the Database:**
    *   Run the database migration script to set up the database schema:
    ```bash
    python migrate_db.py
    ```

7.  Run the application:
    ```bash
    python -m flask --app src.app run --debug
    ```

8.  Access the application in your browser, typically at `http://127.0.0.1:5000`.

## Database Setup

1. Install PostgreSQL:
    ```bash
    sudo apt update
    sudo apt install postgresql postgresql-contrib
    ```

2. Create the database and user:
    ```bash
    sudo -u postgres psql
    CREATE DATABASE paperlit;
    CREATE USER paperlit_user WITH PASSWORD 'securepassword';
    GRANT ALL PRIVILEGES ON DATABASE paperlit TO paperlit_user;
    \q
    ```

3. Configure the database in `app.py`:
    Update the `SQLALCHEMY_DATABASE_URI` in your Flask app:
    ```python
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://paperlit_user:securepassword@localhost/paperlit'
    ```

4. Install required Python packages:
    ```bash
    pip install flask-sqlalchemy psycopg2
    ```

5. Initialize the database:
    ```bash
    python app.py
    ```

## Usage

- Navigate to `http://127.0.0.1:5000/` to access the login page.
- Register a new user at `http://127.0.0.1:5000/register`.
- After logging in, you will be redirected to the home page.
- Logout by navigating to `http://127.0.0.1:5000/logout`.

## Error Handling

- A custom 404 error page is displayed when a page is not found.
- A custom 500 error page is displayed when an internal server error occurs.

## License

This project is licensed under the MIT License.

## Project Structure

```
/paperlit/
├── src/
│   ├── __init__.py
│   ├── app.py                # Main Flask application setup, config, routes
│   ├── models.py             # SQLAlchemy database models
│   ├── blueprints/           # Application modules (e.g., plagiarism)
│   │   ├── __init__.py
│   │   └── plagiarism.py
│   ├── templates/            # HTML templates (Jinja2)
│   │   ├── home.html         # Home page (uses Tailwind CSS via CDN)
│   │   ├── login.html
│   │   ├── register.html
│   │   ├── view_document.html # Document viewer with similarity highlights
│   │   ├── edit_profile.html # (If implemented)
│   │   ├── 404.html
│   │   └── 500.html
│   ├── static/               # Static files
│   │   ├── styles.css        # Basic styles (e.g., for login/register)
│   │   ├── script.js         # Basic JavaScript
│   │   ├── images/           # Images
│   │   └── pdfjs/            # PDF.js viewer (installed by setup.py)
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── file_extract.py
│   └── services/             # Application services
│       ├── __init__.py
│       └── plagiarism_service.py # AI-powered similarity detection
├── uploads/                  # Directory for uploaded documents (ensure it exists)
├── setup.py                  # Main setup script
├── setup_pdfjs.py            # PDF.js setup script
├── migrate_db.py             # Database migration script
├── .env.example              # Example environment variables
├── .env                      # Environment variables (ignored by Git)
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore file
└── venv/                     # Virtual environment (ignored by Git)
