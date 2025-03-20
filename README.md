# Dockerized Flask File Upload App

HEROKU-DOCKER LIVE DEMO: https://uploadfile-47843913ee68.herokuapp.com/

## Task
Create a web application that on the homepage allows users to upload a file and enter a password. The application should store the file, the file name, the password, and the UUID4 of the file which will be used for accessing the file.

After a successful upload, the user should be presented with a URL to access the file in the format /get-file/<UUID4>. When this URL is opened, the user should be presented with a form to enter the password. If the password is correct, the app should send the uploaded file to the user.

Implement the solution using the Flask framework with a PostgreSQL database.

## Overview
This application allows users to upload a file with a password. The file is stored on disk, and its metadata (file name, file path, password hash, and UUID4) is stored in a PostgreSQL database. After uploading, a unique URL is generated to allow users to retrieve the file after providing the correct password.

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed on your machine.
- Python 3.x installed on your machine (if running without Docker).
- PostgreSQL installed and running (if using PostgreSQL as your database without Docker).
- `pip` (Python package installer) installed (if running without Docker).

## Running the Application with Docker Compose

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Build and Run the Application:**
   ```bash
   docker-compose up --build
   ```

3. **Access the Application:**
   Open your web browser and navigate to `http://localhost:5000`.

## Running the Application Locally (Without Docker)

If you prefer to run the application without Docker, follow these steps:

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
   ```

2. **Create a Virtual Environment:**
   It is recommended to use a virtual environment to manage dependencies.
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies:**
   Install the required packages using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set Up the Database:**
   - Create a PostgreSQL database:
     ```sql
     CREATE DATABASE fileupload_db;
     ```
   - Update the database URI in your application configuration (if necessary):
     ```python
     app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/fileupload_db'
     ```

6. **Run Database Migrations:**
   If you are using Flask-Migrate, run the following commands to set up your database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

7. **Run the Application:**
   Start the Flask development server:
   ```bash
   flask run
   ```

   The application will be accessible at `http://127.0.0.1:5000`.

## Usage
- Open your web browser and navigate to `http://127.0.0.1:5000` (or `http://localhost:5000` if using Docker).
- Follow the instructions on the web interface to upload files and manage them.


## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

