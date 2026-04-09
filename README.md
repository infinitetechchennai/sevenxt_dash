# SevenXT Dashboard

The SevenXT Dashboard is a comprehensive, production-ready admin and e-commerce backend platform built to manage products, orders, customers, and operations for the SevenXT brand. It handles both B2B and B2C operational workflows, providing an end-to-end solution from inventory management to logistics scheduling.

---

## 🏗️ Architecture & Tech Stack

This project is built using modern, highly scalable technologies separated into two distinct components: a robust API backend and a dynamic frontend dashboard.

### **Frontend (Dashboard)**
- **Framework:** React 18 with Vite
- **Language:** TypeScript
- **State Management & Routing:** React Router DOM
- **UI/UX:** Modern dynamic design with Lucide-React icons
- **AI Integration:** Google Gemini AI (used for automated product description generation & insights)

### **Backend (API Core)**
- **Framework:** FastAPI (Python) - High performance, async-capable web framework
- **Database:** PostgreSQL (Relational DB)
- **ORM:** SQLAlchemy with Alembic for database migrations
- **Authentication:** JWT (JSON Web Tokens) with Bcrypt password hashing
- **Server:** Uvicorn (ASGI server)

### **Third-Party Integrations**
- **Logistics & Shipping:** Delhivery API (Automated AWB generation, pickup requests, return handling)
- **Payments:** Razorpay API (Instant payment verification, transaction logging)
- **Email Notifications:** SendGrid (Invoices, OTPs, refund/exchange updates)
- **SMS Notifications:** Twilio (Order updates, B2B verification statuses)
- **Media Storage:** Cloudinary (Product images, profiles)

---

## 📂 Project Structure

```text
sevenxt_dash/
├── Frontend/           # React + Vite admin dashboard
├── backend/            # FastAPI python backend
│   ├── app/            # Main application code
│   │   ├── modules/    # Modular API endpoints (auth, products, refunds, etc.)
│   │   └── utils/      # Shared utilities (e.g., Cloudinary uploads)
│   ├── migrations/     # Alembic database migrations
│   ├── uploads/        # System storage (Invoice PDFs, AWB Labels, Profiles)
│   └── start.py        # Entry point to run backend locally
├── CREDENTIALS_BACKUP.md # Extracted credentials and secrets (Never commit!)
└── nginx.conf          # Reverse proxy configuration for Ubuntu/Production deployment
```

---

## 🚀 Local Development Setup (For Newbies)

### Step 1: Clone & Setup Database
1. Make sure you have **PostgreSQL** installed and running locally.
2. Create a new database named `sevennxt_db`.
3. Provide the database credentials to the `.env` file in the backend.

### Step 2: Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create a Python Virtual Environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   - **Windows:** `.\.venv\Scripts\activate`
   - **Mac/Linux:** `source .venv/bin/activate`
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Create Environment Variables:
   - Copy the `.env.example` file and rename it to `.env`.
   - Update `DATABASE_URL` with your local Postgres credentials.
6. Run Database Migrations (if applicable):
   ```bash
   alembic upgrade head
   ```
7. Start the backend Server:
   ```bash
   python start.py
   # Runs on http://localhost:8000
   ```

### Step 3: Frontend Setup
1. Open a new terminal and navigate to the frontend folder:
   ```bash
   cd Frontend
   ```
2. Install Node modules:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `Frontend/` directory and add your keys (e.g., Gemini API key, Backend URL).
4. Start the frontend development server:
   ```bash
   npm run dev
   # Runs on http://localhost:5173
   ```

---

## 🌐 Production Deployment Guide (Ubuntu / EC2)

Deploying SevenXT requires a Linux environment (Ubuntu 22.04+ recommended) with PostgreSQL, Python, Node.js, and Nginx.

### 1. Server Prerequisites
Run the following on your Linux server:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx
```

### 2. Configure Database
Log into Postgres and set up your production database and user matching what you will put in your production `.env` file.

### 3. Deploy Backend (FastAPI + Systemd)
1. Clone the repository to `/home/ubuntu/sevenxt_dash`.
2. Create and activate a virtual environment in `/backend`, then install `requirements.txt`.
3. Fill out the `backend/.env` file WITH PRODUCTION SECRETS (Twilio, Razorpay, Delhivery, SendGrid, strong JWT secret).
4. Run migrations using Alembic.
5. Create a `systemd` service file `/etc/systemd/system/sevenxt.service`:
   ```ini
   [Unit]
   Description=SevenXT FastAPI Backend
   After=network.target

   [Service]
   User=ubuntu
   Group=www-data
   WorkingDirectory=/home/ubuntu/sevenxt_dash/backend
   Environment="PATH=/home/ubuntu/sevenxt_dash/backend/.venv/bin"
   ExecStart=/home/ubuntu/sevenxt_dash/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

   [Install]
   WantedBy=multi-user.target
   ```
6. Start and enable the service:
   ```bash
   sudo systemctl start sevenxt
   sudo systemctl enable sevenxt
   ```

### 4. Deploy Frontend (Vite)
1. Navigate to the `Frontend` directory.
2. Build the production React bundle:
   ```bash
   npm install
   npm run build
   ```
3. The build process creates a `dist/` folder.
4. Copy the `dist/` contents to your web server root (e.g., `/var/www/dashboard_dist/`).

### 5. Configure Nginx & SSL
1. Copy the provided `nginx.conf` file to the server:
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/sevenxt
   sudo ln -s /etc/nginx/sites-available/sevenxt /etc/nginx/sites-enabled/
   ```
   *(Ensure you remove the default nginx config `sudo rm /etc/nginx/sites-enabled/default`)*
2. Check for syntax errors and restart:
   ```bash
   sudo nginx -t
   sudo systemctl restart nginx
   ```
3. Secure with SSL using Certbot:
   ```bash
   sudo certbot --nginx -d sevenxt.in -d www.sevenxt.in
   ```

## 🔒 Security Best Practices
- **Never commit `.env` or `CREDENTIALS_BACKUP.md` to GitHub.**
- Keep `JWT_SECRET` generated exclusively for your production server using strong entropy (`openssl rand -hex 32`).
- Production APIs must require HTTPS (enforced by Nginx).
- Secure the PostgreSQL server by limiting connections from localhost (`pg_hba.conf`).
