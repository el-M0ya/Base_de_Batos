# Base de Batos 🕵🏻‍♂️ — Management System for the Automatic Generation of Workout Plans

> Capstone Project for **Databases II** and **Software Engineering**  
> Academic Year 2026–2027 | Major: Computer Science | University of Havana  
> Status: **In development** 🚧

---

## 📑 Table of Contents

- [Project Description](#-project-description)
- [Team](#-team)
- [Objectives](#-objectives)
- [Key Features](#-key-features)
- [Preliminary Data Model](#-preliminary-data-model)
- [Architecture & Technologies](#-architecture--technologies)
- [Requirements](#-requirements)
- [Installation and Execution](#-installation-and-execution)
- [Testing](#-testing)
- [Repository Structure](#-repository-structure)
- [Best Practices and Git](#-best-practices-and-git)
- [Documentation](#-documentation)
- [Evaluation](#-evaluation)
- [Bibliography](#-bibliography)
- [License](#-license)

---

## 📌 Project Description

This project consists of a **web application** for the **management and automatic generation of workout plans** in a gym. The system must manage:

- Available exercises.
- Training programs.
- Muscle groups and exercise types.
- Trainers responsible for creating and validating routines.
- Clients who execute these routines.
- Workout sessions and progress tracking reports.

Routines must dynamically adapt to parameters such as intensity levels, exercise types, and muscle group distribution throughout the training cycle. Furthermore, the system must support automatic routine generation, review and validation by the floor manager, assignment to clients, and logging of each completed workout session.

This project is developed jointly for **Databases II** and **Software Engineering**, maintaining the logical coherence required by each subject while preventing duplicated effort.

---

## 👥 Team

**Team Name:** Base de Batos 🕵🏻‍♂️

| Member | Group | Telegram | GitHub |
|--------|-------|----------|--------|
| Bryan Ernesto Moya Aquino | C312 | [@BM0ya](https://t.me/BM0ya) | [el-M0ya](https://github.com/el-M0ya) |
| Héctor Duarte Vázquez | C311 | [@hduartev](https://t.me/hduartev) | [HectorDuarte911](https://github.com/HectorDuarte911) |
| Fabio Hernández Piloto | C311 | [@FabioPilot](https://t.me/FabioPilot) | [Fabio-Pilot](https://github.com/Fabio-Pilot) |
| Gabriel Pérez Suárez | C312 | [@GabrielPS1016](https://t.me/GabrielPS1016) | [GaboPS1016](https://github.com/GaboPS1016) |
| Alex Leonardo Cuervo Grillo | C311 | [@cuervogrillo](https://t.me/cuervogrillo) | [AlexCuervo](https://github.com/AlexCuervo) |
| Alejandro Lopez Castro | C312 | [@AlejandroL04](https://t.me/AlejandroL04) | [Kaik0405](https://github.com/Kaik0405) |

**Repository:** `https://github.com/el-M0ya/Proyecto_Conjunto_de_Bases_de_Datos_II_e_Ingenier-a_de_Software`  

---

## 🎯 Objectives

- Consolidate and expand essential concepts, methods, and tools covered in **Databases I**.
- Design, implement, re-engineer, and/or maintain a modern **Database System** following state-of-the-art standards.
- Develop an application allowing end users to interact and exchange information effectively through an intuitive interface.
- Apply **Software Engineering** best practices: version control, planning, decoupled architecture, unit testing, and design patterns.
- Work effectively in multidisciplinary teams by integrating complex requirements into a unified joint project.

---

## ⚙️ Key Features

### Administrator
- Prevent duplicate exercise entries.
- Prevent duplicate routine assignments to clients.
- Manage users, roles, and access permissions.

### Trainer
- Add new exercises to the existing exercise bank.
- Categorize exercises by muscle group and type (strength, cardio, or flexibility).
- Assign intensity levels (low, medium, or high).
- Automatically generate routines based on selected exercises.
- View routines created by other trainers assigned to the same training program.
- View and monitor client progress reports.

### Room Chief
- Review and approve generated routines.
- Request the generation or adjustment of a routine based on specific criteria.
- Log observations, feedback, and validation timestamps.

### Client
- Access assigned workout routines.
- Log each executed training session.
- Track personal progress reports.
- Request virtual routine adjustments and designate the trainer responsible for the revision.

### System
- Automatically generate routines based on configurable constraints: exercise proportion by type, muscle group coverage, total number of exercises, intensity levels, etc.
- Store the variable block structure of each routine (warm-up, circuits, sets, rest intervals).
- Guarantee immediate availability of the client's active routine during workouts.
- Generate comprehensive reports:
  1. List of automatically generated routines for a given program.
  2. Most utilized exercises in finalized routines, categorized by intensity and muscle group.
  3. Routines validated by a specific reviewer, complete with timestamps and review notes.
  4. Client performance reports per routine, including intensity distribution and completion rates.
  5. Program-to-program routine comparison to verify muscle group and intensity balance.
  6. Correlation analysis between intensity level and average performance, including the top 10 exercises with the highest drop-out rates and manual adjustment history.
- Export all generated data and reports to **PDF** format.
- Support multi-column sorting on all data views.

---

## 🗄️ Preliminary Data Model

Identified core entities:

- **User** (Administrator, Trainer, Room Chief, Client)
- **TrainingProgram**
- **Trainer**
- **Client**
- **Exercise**
- **MuscleGroup**
- **ExerciseType**
- **IntensityLevel**
- **Routine**
- **RoutineBlock** / **RoutineStructure**
- **WorkoutSession**
- **AdjustmentRequest**
- **RoutineValidation**
- **RoutineParameter**
- **Branch** (Gym location)

> The complete Enhanced Entity-Relationship (EER) conceptual model will be documented in the **Database Design** report corresponding to Week 5.

---

## 🏗️ Architecture & Technologies

| Layer | Technology |
|---|---|
| Frontend | **React 19** + **TypeScript 6** (strict mode) + **Vite 8** |
| Styling | **Tailwind CSS v4** + **shadcn/ui** built on Radix UI |
| State Management | **TanStack Query 5** (server state) + React Context (auth session & theme) |
| Backend | To be defined — scheduled for the next iteration |
| Database | **PostgreSQL 17** (relational core) + **MongoDB 8** (variable block structure) + **Redis 8** (active routine cache) |
| Containerization | Docker + Docker Compose (multi-stage frontend build with Nginx) |
| Testing | **Vitest 5** + Testing Library + **MSW 2** |
| Quality & Tooling | ESLint 10 (with `eslint-plugin-jsdoc`) + Prettier 3 |
| Version Control | Git + GitHub (with CI pipelines in `.github/workflows/`) |

**Architectural Highlights:**

- Layered **hexagonal architecture**: `app → features → domain`, keeping domain logic pure with zero dependencies on React or network layers.
- **Nine design patterns** implemented: Repository, Adapter, Strategy, Factory, Chain of Responsibility, Facade, Provider, Compound Components, and Guard (detailed in [`frontend/README.md`](frontend/README.md)).
- Unit, component, and integration tests for the frontend, with **strict coverage thresholds** enforced by CI.
- Mandatory JSDoc across code, verified by ESLint.
- Runtime environment variable validation using Zod during application boot.
- Zero secrets committed to the repository: configuration managed purely via environment variables and `.env.example`.

> **Database Design Note:** Project requirements state that each routine's block hierarchy has a variable schema and *must not be modeled together with the rest of the relational tables*. Furthermore, the active routine must be available with near-zero latency regardless of concurrent load. Consequently, the architecture incorporates a relational database (PostgreSQL), a document store for variable block trees (MongoDB), and an in-memory cache (Redis). The relational engine will be finalized upon delivery of the EER design (Week 5).

---

## 📋 Requirements

- **Node.js 20.19+** (tested on 24.x) and npm 10+.
- Docker and Docker Compose.
- Git.

---

## 🚀 Installation and Execution

### Frontend only, with mock data

```bash
git clone https://github.com/el-M0ya/Proyecto_Conjunto_de_Bases_de_Datos_II_e_Ingenier-a_de_Software
cd Proyecto_Conjunto_de_Bases_de_Datos_II_e_Ingenier-a_de_Software/frontend
npm install
npm run mock        # Runs http://localhost:5173 with MSW mock handlers
```

Test credentials for each user role are documented in [`frontend/README.md`](frontend/README.md).

### Frontend connected to the backend

```bash
cd frontend
npm install
cp .env.example .env.local     # configure VITE_API_PROXY_TARGET
npm run dev                    # Runs http://localhost:5173
```

### Infrastructure services

```bash
cp .env.example .env
docker compose up              # Starts PostgreSQL, Redis, and MongoDB
```

### Containerized production build

```bash
docker compose --profile full up --build
```

### Quality checks

```bash
cd frontend
npm run verify                 # Typecheck + lint + tests
npm run test:coverage          # Run tests with coverage output
```

---

## 🧪 Testing

| Scope | Location | Tools |
|---|---|---|
| Unit | `frontend/src/tests/unit` | Vitest, repository test doubles |
| Component | `frontend/src/tests/components` | Testing Library, `user-event` |
| Integration | `frontend/src/tests/integration` | MSW running against real HTTP repository adapters |
| Backend | `tests/` | To be defined during server implementation |

The frontend test suite enforces a minimum coverage threshold of 60% across statements, branches, functions, and lines, validated on every push by GitHub Actions.

---

## 📁 Repository Structure

```text
.
├── backend/                # Server-side source code
├── frontend/               # Web client application source code
│   ├── src/
│   │   ├── app/            # Composition root: providers, router, route guards, layouts
│   │   ├── core/           # Cross-cutting infrastructure: config, HTTP client, RBAC, DI, storage
│   │   ├── domain/         # Pure business domain: entities and interface contracts (ports)
│   │   ├── features/       # Vertical slices organized by business feature
│   │   ├── infrastructure/ # Adapters: HTTP implementations of domain ports
│   │   ├── shared/         # Reusable UI components, custom hooks, and shared utilities
│   │   ├── mocks/          # Mock data and MSW service worker handlers
│   │   └── tests/          # Unit, component, and integration test suites
│   ├── Dockerfile          # Multi-stage container build published on Nginx
│   └── nginx.conf          # Client-side SPA routing and HTTP security headers
├── db/                     # SQL scripts, schema migrations, and database backups
├── docs/                   # Reports, technical documentation, diagrams
├── docker/                 # Container configuration files and Dockerfiles
├── tests/                  # Backend test suites
├── .github/workflows/      # Continuous Integration (CI) configuration
├── .env.example            # Sample environment variables template
├── .gitignore              # Files ignored by Git
├── docker-compose.yml      # Multi-container service orchestration
├── README.md               # Main repository documentation
└── ...
```

---

## 📖 Bibliography

- García Hernández, L.; Montes de Oca Richardson, M. *Sistemas de Bases de Datos: Modelación y Diseño*. Editorial Félix Varela. Cuba, 2005.
- Date, C. J. *An Introduction to Database Systems*. 7th Edition. Addison-Wesley. USA, 2000.
- Hansen, G. W.; Hansen, J. V. *Database Management and Design*. 2nd Edition. Prentice Hall. UK, 1998.
- Course lectures and supplementary reference material.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

```text
MIT License

Copyright (c) 2025 CETED — Universidad de La Habana

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
```

---

## 📬 Contact

If you have questions, feedback, or suggestions, feel free to reach out to any team member via Telegram or GitHub.
