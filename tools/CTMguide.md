# CTM Task Management Guide

## 1. Text-Based Task Template (`task_00X.txt`)

When CTM generates tasks (e.g., `task_001.txt`, `task_002.txt`), you can overwrite or create your own using this template. It ensures every task has the same structure, making dependencies, subtasks, and acceptance criteria explicit.

```
──────────────────────────────────────────────────────
Task ID:            <Automatically assigned by CTM or manually set, e.g., 3>

Title:              <Short, action‐oriented title (e.g., “Implement user authentication”)>

Description:
  • **Background:** Explain why this task is needed (business or technical context).
  • **Goal:** Describe exactly what must be delivered (functional scope, expected outcome).
  • **Dependencies with other modules:** List any high‐level integration points or related features.

Dependencies:
  - [ ] Task 1    # List any prerequisite Task IDs. If none, write “None” or leave blank.
  - [ ] Task 2

Subtasks:
  3.1: <Subtask 1 title (e.g., “Set up database schema for users”)>
       • <Detailed bullet(s) describing steps or checks for subtask 3.1>
  3.2: <Subtask 2 title (e.g., “Implement password hashing”)>
       • <Detailed bullet(s) describing steps or checks for subtask 3.2>
  …

Acceptance Criteria:
  - [ ] <Condition 1 (e.g., “Registration endpoint writes new user to database and returns userId”)>
  - [ ] <Condition 2 (e.g., “Login endpoint returns a valid JWT and verifies it correctly”)>
  - [ ] <Condition 3 (e.g., “All unit tests pass with ≥ 90% coverage”)>

Test Strategy:
  • **Unit Tests:** Describe which modules to test and what inputs/outputs to verify.  
  • **Integration Tests:** Explain how to simulate each component together (e.g., mock external APIs, run against a test database).  
  • **Performance/Load Tests (optional):** Describe how to validate performance requirements (e.g., response time under load).

Notes:
  • **Tech Stack/Dependencies:** (e.g., “Use bcrypt for hashing, Passport.js for strategy management”).  
  • **Reference Links:** (e.g., internal wiki, official library docs).  
  • **Security or Compliance Considerations:** (e.g., “Ensure no sensitive data is logged, sanitize user input to prevent injection”).  

Status:             todo    # One of: todo / in-progress / done
──────────────────────────────────────────────────────
```

### How to Use This Template

1. **Copy & Paste** the entire block into a new file `tasks/task_00X.txt`.
2. Replace each `<…>` placeholder with your actual content.
3. Check or uncheck each `[ ]` as subtasks or dependencies are completed.
4. Update **Status** as you work on or finish the task.

---

## 2. JSON-Based Task Template (for `tasks.json`)

If you prefer editing `tasks.json` directly (instead of individual text files), use this JSON structure. Paste a new object into the `"tasks"` array and fill out each field.

```jsonc
{
  "tasks": [
    {
      "id": "3",
      "title": "Implement user authentication",
      "description": "• Background: We need to allow users to register, log in, and have secure access control. \n• Goal: Provide email/password registration, store hashed passwords, issue JWTs on login, and protect restricted endpoints. \n• Integration: Validate JWT at API gateway and pass userId downstream.",
      "dependencies": ["1", "2"],

      "subtasks": [
        {
          "id": "3.1",
          "title": "Set up user database schema",
          "description": "• Create `users` table with fields: id (UUID), email (unique), passwordHash (string), role (enum).\n• Write SQL migration scripts and run migrations."
        },
        {
          "id": "3.2",
          "title": "Implement password hashing",
          "description": "• Install `bcrypt` in package.json.\n• Wrap `bcrypt.hash` and `bcrypt.compare` in `src/utils/password.ts`."
        },
        {
          "id": "3.3",
          "title": "Create registration endpoint (POST /api/auth/register)",
          "description": "• Build route handler to accept {email, password}.\n• Hash password, save new user record, return {success: true, userId}."
        },
        {
          "id": "3.4",
          "title": "Create login endpoint (POST /api/auth/login)",
          "description": "• Accept {email, password}, fetch user, compare hash, issue JWT with payload {userId, role}, return {token}."
        },
        {
          "id": "3.5",
          "title": "Add JWT middleware",
          "description": "• In `src/middleware/jwtAuth.ts`, extract Bearer token, verify with `jsonwebtoken.verify`, attach `req.user` or return 401."
        },
        {
          "id": "3.6",
          "title": "Write unit tests for auth flow",
          "description": "• Use Jest + SuperTest to test registration and login success/failure scenarios."
        },
        {
          "id": "3.7",
          "title": "Document API in docs/auth-spec.md",
          "description": "• Write request/response examples, error codes, authentication flow."
        }
      ],

      "acceptanceCriteria": [
        "Registration endpoint writes to database and returns valid userId.",
        "Login endpoint returns a valid JWT, and JWT middleware protects restricted routes.",
        "Unauthorized requests to protected endpoints return HTTP 401.",
        "All unit tests pass with ≥ 90% coverage."
      ],

      "testStrategy": {
        "unitTests": [
          "tests/auth/register.test.ts — test successful registration & duplicate emails",
          "tests/auth/login.test.ts — test successful login & wrong password rejection"
        ],
        "integrationTests": [
          "Use SuperTest to spin up an Express server and call /api/auth/register and /api/auth/login, then verify JWT can access protected routes."
        ]
      },

      "notes": [
        "Use bcrypt for password hashing.",
        "Use jsonwebtoken for JWT creation/verification.",
        "Keep JWT secret in environment variable JWT_SECRET.",
        "Ensure password is at least 8 characters, contains mixed case and numbers."
      ],

      "status": "todo"
    }
    // … add other task objects here …
  ]
}
```

### How to Use This JSON Template

1. Open `tasks/tasks.json`.
2. Inside the top‐level `"tasks"` array, paste a new object following the template above.
3. Replace all placeholder text (e.g., `"Implement user authentication"`, bullet lists inside `"description"`, etc.) with your actual task details.
4. Save the file.
5. Run CTM commands:

   * `task-master list` to confirm CTM sees your new task.
   * `task-master next` to let Gemini Pro recommend the next task.
   * `task-master expand <id>` if you want CTM to augment or refine subtasks.

---

## 3. Example Filled-Out Task

Below is a fully fleshed‐out example of **Task 5: Generate Monthly Sales Report**. Copy it into either `tasks/task_005.txt` (text format) or as the next object in `tasks/tasks.json` (JSON format).

---

### 3.1. Text File Example (`tasks/task_005.txt`)

````text
──────────────────────────────────────────────────────
Task ID:            5

Title:              Generate monthly sales report

Description:
  • Background: The product team needs an automated monthly sales report, stored on Google Drive for management review.
  • Goal: 
    1. Schedule a job that runs on the 1st day of each month.  
    2. Aggregate last month’s sales data from PostgreSQL.  
    3. Render a PDF report (including total revenue, order count, return rate).  
    4. Upload the PDF to a specific Google Drive folder.  
    5. Send notification emails with the report link to stakeholders.
  • Integration: 
    – Relies on the Orders database schema.  
    – Uses Google Drive API (OAuth2) for file upload.  
    – Uses SendGrid (or similar) for email notifications.

Dependencies:
  - [x] Task 1    # “Setup orders table and initial schema”
  - [ ] Task 4    # “Integrate email service (SendGrid)”

Subtasks:
  5.1: Schedule monthly cron job
       • Install `node-cron`.  
       • Create `src/tasks/reportScheduler.ts` with cron pattern `0 0 1 * *` (midnight on day 1).  
  5.2: Query last month’s sales data
       • In `src/services/reportService.ts`, write SQL:  
         ```sql
         SELECT 
           SUM(total_amount) AS totalRevenue,
           COUNT(*) AS orderCount,
           SUM(CASE WHEN status = 'returned' THEN 1 ELSE 0 END) AS returnCount
         FROM orders
         WHERE order_date BETWEEN DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                             AND (DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '1 day');
         ```
       • Validate results with test data.  
  5.3: Generate PDF from template
       • Use `pdfkit` (or `puppeteer` with an HTML template).  
       • Place HTML template in `templates/monthlyReport.html` (with placeholders for data).  
       • In code, load template, replace placeholders, and generate a PDF file.  
  5.4: Upload PDF to Google Drive
       • In `src/utils/googleDrive.ts`, configure OAuth2 client with `googleapis` library.  
       • Upload function must accept local file path and target folder ID (from environment variable `DRIVE_FOLDER_ID`).  
  5.5: Send notification email
       • In `src/utils/email.ts`, configure SendGrid (or nodemailer).  
       • Compose email with subject “Monthly Sales Report” and include the Drive file link.  
  5.6: Write unit & integration tests
       • **Unit Tests:**  
         – `tests/report/query.test.ts`: mock database pool, verify SQL returns correct aggregated values.  
         – `tests/report/pdf.test.ts`: pass sample data, verify PDF file is generated and includes expected text.  
       • **Integration Tests:**  
         – In a staging environment (or local test), run the full flow: query → PDF generation → upload → email send.  
         – Use sandbox credentials for Drive and SendGrid.  
  5.7: Documentation
       • Create `docs/monthly-report-spec.md` describing:  
         – Cron schedule details.  
         – Data fields included in report (metrics definitions).  
         – Drive folder structure and access permissions.  
         – Email content template and recipients list.

Acceptance Criteria:
  - [ ] Cron job runs on the 1st of each month (verify by local simulation with adjusted system clock).  
  - [ ] PDF report includes total revenue, order count, and return rate, formatted per design.  
  - [ ] PDF is successfully uploaded to the specified Google Drive folder (verify file exists and is accessible).  
  - [ ] Notification email is sent and contains a valid Drive link.  
  - [ ] All unit and integration tests pass.

Test Strategy:
  • **Unit Tests:**  
    – `tests/report/query.test.ts`: mock database, verify correct SQL and result mapping.  
    – `tests/report/pdf.test.ts`: use sample JSON data to generate PDF, parse PDF text, assert headers and values.  
    – `tests/report/drive.test.ts`: stub Google Drive API calls, verify correct API arguments and error handling.  
    – `tests/report/email.test.ts`: stub SendGrid, verify email payload.  

  • **Integration Tests:**  
    – In a CI pipeline with sandbox credentials, run end‐to‐end:  
      1. Populate test database with sample orders for previous month.  
      2. Run the cron function manually.  
      3. Check that a PDF appears in the staging Drive folder.  
      4. Confirm that an email was sent to a test inbox (using a mail catcher or test address).  

  • **Performance Tests (Optional):**  
    – Simulate large volumes (e.g., 100k orders) and measure PDF generation time; ensure completion under 30 seconds.  
    – Test Drive upload with large PDF (e.g., >10MB) to confirm no timeouts.

Notes:
  • **Tech Stack/Dependencies:**  
    – Use `node-cron` for scheduling.  
    – Use `pdfkit` (or headless Chrome + `puppeteer`) for report generation.  
    – Use `googleapis` official library for Drive (OAuth2-based).  
    – Use `@sendgrid/mail` for sending email.  
  • **Environment Variables:**  
    – `DB_CONNECTION_URL` (PostgreSQL connection string)  
    – `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN` (for Drive OAuth2)  
    – `DRIVE_FOLDER_ID` (Google Drive folder ID where reports go)  
    – `SENDGRID_API_KEY`  
  • **Security/Compliance:**  
    – Ensure no PII (personally identifiable information) ends up in logs or PDF if policy prohibits.  
    – Limit file permissions in Drive so only authorized users can view.  
    – Sanitize user‐facing fields if any (though this job is automated).  

Status:             todo
──────────────────────────────────────────────────────
````

---

### 3.2. JSON File Example (append to `tasks/tasks.json`)

```jsonc
{
  "tasks": [
    // … existing tasks …

    {
      "id": "5",
      "title": "Generate monthly sales report",
      "description": "• Background: The product team needs an automated monthly sales report stored in Google Drive. \n• Goal: \n  1. Schedule a job that runs on the 1st of each month. \n  2. Aggregate last month’s sales data from PostgreSQL. \n  3. Render a PDF report with total revenue, order count, return rate. \n  4. Upload the PDF to the designated Google Drive folder. \n  5. Send notification emails with the report link to stakeholders.\n• Integration: \n  – Uses Orders database schema. \n  – Uses Google Drive API (OAuth2). \n  – Uses SendGrid for email notifications.",
      "dependencies": ["1", "4"],

      "subtasks": [
        {
          "id": "5.1",
          "title": "Schedule monthly cron job",
          "description": "• Install `node-cron`. \n• Create `src/tasks/reportScheduler.ts` with cron pattern `0 0 1 * *`."
        },
        {
          "id": "5.2",
          "title": "Query last month’s sales data",
          "description": "• In `src/services/reportService.ts`, write SQL to aggregate revenue, order count, return count for the previous month. \n• Validate with test data."
        },
        {
          "id": "5.3",
          "title": "Generate PDF from template",
          "description": "• Use `pdfkit` or `puppeteer` to generate a PDF from `templates/monthlyReport.html`. \n• Replace placeholders with aggregated data."
        },
        {
          "id": "5.4",
          "title": "Upload PDF to Google Drive",
          "description": "• In `src/utils/googleDrive.ts`, configure OAuth2 with `googleapis`. \n• Upload function must accept a local file path and target `DRIVE_FOLDER_ID`."
        },
        {
          "id": "5.5",
          "title": "Send notification email",
          "description": "• In `src/utils/email.ts`, configure SendGrid. \n• Compose email with subject “Monthly Sales Report” and Drive file link."
        },
        {
          "id": "5.6",
          "title": "Write unit & integration tests",
          "description": "• **Unit Tests:** \n  – `tests/report/query.test.ts`: mock database, verify query results. \n  – `tests/report/pdf.test.ts`: use sample data, verify PDF contents. \n  – `tests/report/drive.test.ts`: stub Drive API. \n  – `tests/report/email.test.ts`: stub SendGrid. \n• **Integration Tests:** \n  – In CI environment, run full flow: query → PDF → upload → email. \n  – Use sandbox credentials for Drive and SendGrid."
        },
        {
          "id": "5.7",
          "title": "Documentation",
          "description": "• Create `docs/monthly-report-spec.md` describing cron schedule, data fields in report, Drive folder structure, and email template."
        }
      ],

      "acceptanceCriteria": [
        "Cron job runs on the 1st of each month (local simulation verified).",
        "PDF report includes total revenue, order count, return rate formatted correctly.",
        "PDF is uploaded to specified Google Drive folder and is accessible.",
        "Notification email is sent with a valid Drive link.",
        "Unit and integration tests all pass."
      ],

      "testStrategy": {
        "unitTests": [
          "tests/report/query.test.ts — mock DB, verify correct aggregation.",
          "tests/report/pdf.test.ts — generate PDF from sample data, assert text.",
          "tests/report/drive.test.ts — stub Drive upload, verify correct API usage.",
          "tests/report/email.test.ts — stub SendGrid, verify email payload."
        ],
        "integrationTests": [
          "CI pipeline: populate test DB, run scheduler, verify PDF in Drive and email delivered to test address."
        ]
      },

      "notes": [
        "Use `node-cron` for scheduling.",
        "Use `pdfkit` or `puppeteer` for PDF generation.",
        "Use `googleapis` for Drive OAuth2.",
        "Use `@sendgrid/mail` for email.",
        "Keep secrets (Drive OAuth, JWT_SECRET, SENDGRID_API_KEY) in environment variables."
      ],

      "status": "todo"
    }

    // … you can insert more tasks here …
  ]
}
```

---

## 4. How to Integrate These Templates into Your CTM Workflow

1. **Place the Template File(s):**

   * If CTM already created `tasks/` and you see `task_00X.txt`, open that file and overwrite its contents with your filled‐out template.
   * If you want to add a brand‐new task, create `tasks/task_00X.txt` (where `00X` is the next available number). Paste the **Text-Based Template** and fill in the blanks.

2. **Or Edit `tasks.json` Directly:**

   * Open `tasks/tasks.json` in your code editor.
   * Copy one of the **JSON-Based Task Template** objects and paste it into the `"tasks"` array. Update all placeholder fields.

3. **Run CTM Commands to Synchronize:**

   * `task-master list` → Verify CTM now recognizes your new or updated tasks.
   * `task-master generate` → If you edited `tasks.json`, this will create or refresh the corresponding `task_00X.txt` files.
   * `task-master next` → CTM (Gemini Pro) analyzes dependencies and priorities, then suggests the “next” task.

4. **Update Status as You Work:**

   * When you start Task 5.1, run:

     ```bash
     task-master set-status --id=5.1 --status=in-progress
     ```
   * When you finish Task 5.1, run:

     ```bash
     task-master set-status --id=5.1 --status=done
     ```
   * CTM will confirm the change and often print the next recommended task automatically.

5. **Use MCP in Your Editor (Optional):**

   * If you set up an MCP server (e.g., in VS Code), open the relevant code file (e.g., `src/routes/chat.ts`).
   * In the Chat/Agent pane, type:

     ```
     #implement 5.3
     ```

     Gemini Pro will inject boilerplate or scaffolded code directly into your open file for subtask 5.3 (“Generate PDF from template”).
   * After reviewing, type:

     ```
     #set-status 5.3 done
     ```

     CTM marks it complete and suggests the next subtask in sequence.

6. **Keep Everything in Sync:**

   * Any manual edits you make to `task_00X.txt` or `tasks.json` should be followed by `task-master list` or `task-master generate` to let CTM refresh its internal state.
   * If a dependency is marked done, CTM can automatically update the next tasks’ recommendations.

---

## 5. Tips & Best Practices

* **Consistent IDs:** Let CTM assign numeric IDs, then refer to them exactly (e.g., `3.1`, `3.2`). Don’t skip numbers or duplicate IDs.
* **Clear, Actionable Titles:** Keep each title under \~50 characters, starting with a verb (e.g., “Create,” “Implement,” “Configure,” “Write tests”).
* **Descriptive Bullet Points:** In `Description` and each `Subtask`, use bullet points to break down steps. That way, anyone reading knows exactly what must be done.
* **Dependencies Are Key:** If Task 5 depends on Task 3 finishing first, list `“3”` under `dependencies`. CTM’s `next` command uses that info to avoid recommending tasks whose prerequisites aren’t done.
* **Acceptance Criteria Drive Testing:** Write very specific, verifiable criteria (e.g., “User cannot register with an already‐taken email,” “Uploading an empty file returns HTTP 400”). This ensures QA knows exactly how to confirm completion.
* **Automate Where Possible:** If you can, add a small CI step that runs `task-master list` and fails if any task is marked “in-progress” longer than X days, or reminds the team.
* **Use MCP for Code Scaffolding:** With MCP set up, `#implement 3.4` can produce an initial stub for “Upload PDF to Drive,” saving you time on boilerplate.
* **Version Control:** Treat `tasks/tasks.json` and `tasks/task_00X.txt` like source code. Commit it alongside your application code so the entire team sees the same task list.
* **Revisit & Refine:** As development progresses, you might discover new subtasks or change acceptance criteria. Update the same template block and mark old subtasks done. This keeps everything in one place instead of scattering notes across chat threads.

---

## 6. Summary

* **Text-Based Template**: Copy into `tasks/task_00X.txt`, replace placeholders, check off items, and update `Status`.
* **JSON-Based Template**: Edit `tasks/tasks.json` to add or modify tasks, including subtasks, dependencies, and testing strategies.
* **Example**: Task 5 (“Generate monthly sales report”) shows a fully detailed breakdown from scheduling to testing.
* **Workflow**:

  1. Create or modify a task using the chosen template.
  2. Run `task-master list` or `task-master generate` to sync CTM’s view.
  3. Use `task-master next` to let Gemini Pro recommend the next step.
  4. Update `Status` with `task-master set-status…` as you work.
  5. (Optionally) Use MCP commands in your editor to generate code snippets (`#implement <subtaskID>`).

By following these templates and steps, you’ll have a **consistent, transparent, and CTM-integrated task management process**. Each task is:

* Clearly **numbered** (`id`).
* Titled with a **concise, action-oriented phrase**.
* Explained in a **detailed Description**, including why and what.
* Broken down into **Dependencies** and **Subtasks**.
* Validated by **Acceptance Criteria** and a **Test Strategy**.
* Annotated with **Notes** for libraries, security, or references.
* Tracked via an explicit **Status** field.

Use this guide to craft every new task in your project. In combination with Gemini Pro’s reasoning and CTM’s orchestration, you’ll reduce ambiguity, speed up development, and ensure nothing falls through the cracks. Good luck!
