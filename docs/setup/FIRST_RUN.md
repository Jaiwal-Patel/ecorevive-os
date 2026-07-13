# First Run in GitHub Codespaces

## 1. Create the repository

Create a **private** GitHub repository named `ecorevive-os`. Do not add an automatic README or license because this repository already contains both.

Upload the project or use the included push script:

```bash
./scripts/push_to_github.sh https://github.com/YOUR_USERNAME/ecorevive-os.git
```

## 2. Open a Codespace

From the repository, choose **Code → Codespaces → Create codespace on main**.

The development container includes Python, Node.js and Docker. When the terminal is ready:

```bash
./scripts/bootstrap.sh
```

The script:

1. Copies `.env.example` to `.env`.
2. Builds PostgreSQL, Redis, Django, Celery and React containers.
3. Applies database migrations.
4. Seeds item categories and public impact metrics.
5. Creates the Founder Guardian identity for `ujaiwal@outlook.com`.
6. Prints a one-time temporary password.

Open the forwarded frontend port `5173`. Sign in and immediately change the temporary password under **Account**.

## 3. Confirm the installation

```bash
./scripts/run_checks.sh
```

Expected checks:

- Django system check
- backend lint
- backend tests and coverage
- frontend lint
- frontend tests
- frontend production build

## 4. Initial administration

The Founder Guardian also has Django admin access at `/admin/`. Use the normal EcoRevive interface for operations and reserve Django admin for controlled setup or recovery.

## 5. Create other roles

Use `/admin/` initially to create:

- a Principal Administrator;
- one Operations Administrator;
- volunteer user accounts and profiles;
- corporate coordinator accounts.

Do not create a Founder Recovery identity using an ordinary user form. See `docs/governance/EXECUTIVE_GOVERNANCE.md`.
