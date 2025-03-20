# Dockerized Flask File Upload App

## Overview
This application allows users to upload a file with a password. The file is stored on disk and its metadata (file name, file path, password, and UUID4) is stored in a PostgreSQL database. After uploading, a unique URL is generated to allow users to retrieve the file after providing the correct password.

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed on your machine.

## Running the Application with Docker Compose

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo-name.git
   cd your-repo-name
