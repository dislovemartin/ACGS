# ACGS - Advanced Cloud Governance System

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Next.js](https://img.shields.io/badge/Next.js-13.5.6-black?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.1.5-06B6D4?logo=tailwindcss&logoColor=white)](https://tailwindcss.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2.2-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

## Overview

ACGS (Advanced Cloud Governance System) is a modern web application built with Next.js, TypeScript, and Tailwind CSS. The application provides comprehensive cloud governance solutions with features like user authentication, role-based access control, and various financial management modules.

## ✨ Features

- 🔐 Authentication & Authorization with Supabase
- 📱 Responsive design with Tailwind CSS
- 🏗️ Modern React with TypeScript
- 📊 Financial Management Modules
  - Bookkeeping
  - Estate Planning
  - Personal Tax Filing
  - Admin Dashboard
- 🚀 Optimized for production

## 🚀 Getting Started

### Prerequisites

- Node.js 18.0.0 or later
- npm or yarn
- Supabase account and project

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/acgs.git
   cd acgs
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   ```

3. Set up environment variables:
   Create a `.env.local` file in the root directory and add your Supabase credentials:
   ```
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   ```

4. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## 🛠️ Project Structure

```
ACGS/
├── app/                  # Next.js 13+ app directory
├── components/           # Reusable UI components
│   ├── auth/            # Authentication components
│   └── page-specific/   # Page-specific components
├── lib/                  # Utility functions and configurations
├── public/               # Static files
└── styles/               # Global styles
```

## 📝 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📬 Contact

For any questions or feedback, please open an issue on GitHub.

---

Built with ❤️ using Next.js, TypeScript, and Tailwind CSS
