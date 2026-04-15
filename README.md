# AxonAI - Educational Dashboard

A modern React + Vercel frontend for an AI-powered educational platform. Real-time visualization of student learning data, class mastery metrics, and personalized student insights.

## 🚀 Tech Stack

- **Frontend**: React 19 + React Router 7 + Tailwind CSS 4
- **Deployment**: Vercel (React app)
- **API**: AWS Lambda (Flask backend)
- **Styling**: Tailwind CSS with custom CSS variables

## 📋 Features

### Teacher Dashboard
- Real-time class mastery visualization with interactive charts
- Student roster with search and performance indicators
- Individual student profiles with learning insights
- Knowledge graph visualization by subject
- Settings and notification preferences

### Student Dashboard
- Personal mastery overview by subject
- Learning progress tracking
- Conversation history with AI tutor

### Parent/Whanau Dashboard
- Summary view of child learning progress
- Key performance metrics

## 🎯 User Roles

The app supports three role-based interfaces:
- **Teacher**: Full classroom management and analytics
- **Student**: Personal learning dashboard
- **Parent/Whanau**: Progress overview

## 📁 Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── api/            # API client (axonai.js)
│   ├── components/     # Reusable UI components
│   ├── pages/          # Route pages (teacher, student, parent)
│   ├── constants/      # Demo data and helpers
│   ├── App.jsx         # React Router setup
│   └── index.jsx       # Entry point
├── vercel.json         # Vercel SPA configuration
└── package.json        # Dependencies
```

## 🔧 Setup & Development

### Prerequisites
- Node.js 20+
- npm or yarn

### Install Dependencies
```bash
cd frontend
npm install
```

### Environment Variables
```bash
# .env (optional)
REACT_APP_API_URL=https://your-lambda-api-endpoint
```

### Run Development Server
```bash
npm start
```

The app will open at `http://localhost:3000`

### Local UI workflow (no Vercel deploy needed)
Use this when you want to iterate on UI locally but keep calling the same deployed API.

```bash
cd frontend
copy .env.local.example .env.local
npm install
npm start
```

- `npm start` hosts the UI locally at `http://localhost:3000`
- `.env.local` is ignored by git, so you can tweak local API config safely
- By default, `.env.local.example` points at the current hosted AxonAI API URL

### No-admin setup script (Windows PowerShell)
If you do not have Node/npm installed system-wide, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-local-frontend.ps1
```

Optional: `-ApiUrl "https://..."` to override the default Lambda URL.

What it does:
- Downloads portable Node.js to your user profile (`%USERPROFILE%\tools\node`)
- Writes `frontend/.env.local` with your API URL
- Installs frontend dependencies
- Starts the local dev server on `http://localhost:3000`

### Build for Production
```bash
npm run build
```

## 🚀 Deployment to Vercel

### One-Click Deploy
```bash
# Using Vercel CLI
npm install -g vercel
vercel
```

### Manual Deploy
1. Push to GitHub
2. Connect repo to Vercel
3. Set `Root Directory` to `frontend`
4. Deploy

### Environment Variables
Add to Vercel project settings:
```
REACT_APP_API_URL=https://your-lambda-endpoint.lambda-url.region.on.aws
```

## 📚 Available Routes

| Route | Role | Purpose |
|-------|------|---------|
| `/login` | All | Role selector (entry point) |
| `/teacher` | Teacher | Class dashboard with mastery metrics |
| `/teacher/students` | Teacher | Student roster |
| `/teacher/class/:id` | Teacher | Class-level insights |
| `/teacher/student/:id` | Teacher | Individual student profile |
| `/teacher/knowledge-graph` | Teacher | Subject-wise knowledge graph |
| `/teacher/settings` | Teacher | Preferences |
| `/student` | Student | Student mastery overview |
| `/parent` | Parent | Child progress summary |

## 🔗 API Integration

The frontend fetches data from the AWS Lambda backend via `/frontend/src/api/axonai.js`:

```javascript
import { getClassOverview, getStudentDashboard } from './api/axonai';

// Fetch class data
const data = await getClassOverview(classId);

// Fetch student dashboard
const student = await getStudentDashboard(studentId);
```

### Available Endpoints
- `GET /class/{id}/overview` - Class mastery and roster
- `GET /student/{id}/dashboard` - Student summary
- `GET /student/{id}/mastery` - Detailed mastery data
- `GET /student/{id}/flags` - Learning risk flags
- `GET /student/{id}/pedagogy` - Learning style data
- `GET /student/{id}/conversations` - Chat history
- `GET /concepts/{subject}` - Knowledge graph by subject
- `GET /conversation/{id}/messages` - Conversation messages

## 🎨 Theming

The app uses CSS variables for theming. Edit `/frontend/src/index.css` to customize:
```css
--primary-700, --primary-100
--text-primary, --text-secondary, --text-tertiary
--mastered, --on-track, --in-progress, --needs-attention, --at-risk
```

## 🧪 Testing

### Manual Testing
1. Use the login page to select a role
2. Demo data is automatically loaded and filtered
3. Test different views and interactions

### Role-Based Testing
- **Teacher**: Full access to classes, students, analytics
- **Student**: Personal dashboard only
- **Parent**: Summary view of child progress

## 🛠️ Development Tips

### Adding a New Page
1. Create `src/pages/RouteName.jsx`
2. Import in `App.jsx`
3. Add route in the `<Routes>` element
4. Link from navigation or another page

### Adding Components
1. Create in `src/components/ComponentName.jsx`
2. Import and use in pages
3. Keep reusable across multiple pages

### API Calls
- Import from `/api/axonai.js`
- Always handle loading and error states
- Use the `LoadingSpinner` and `ErrorState` components

## 📊 Key Components

| Component | Purpose |
|-----------|---------|
| `DashboardShell` | Layout wrapper with sidebar |
| `LoadingSpinner` | Loading state display |
| `ErrorState` | Error handling UI |
| `ConversationThread` | Chat history display |
| `KnowledgeGraph` | Interactive concept visualization |
| `StudentTable` | Roster table with sorting |

## 🚨 Common Issues

### "Cannot find module" errors
- Run `npm install` to install all dependencies
- Check that you're in the `frontend` directory

### API connection errors
- Verify `REACT_APP_API_URL` environment variable
- Check that the Lambda backend is running
- Review browser console for detailed errors

### Styling issues
- Ensure `index.css` is imported in `index.jsx`
- Tailwind classes require `npm run build` in production
- Check that Tailwind config includes all template paths

## 📈 Performance

- All images are optimized
- Routes use React Router code splitting
- Charts use Recharts for efficient rendering
- API calls are memoized where appropriate

## 🔐 Security

- No sensitive data in frontend code
- All API calls include proper error handling
- Session-based authentication via backend
- CORS configured on Lambda backend

## 📄 License

MIT License - See LICENSE file for details

---

**AxonAI v2.0** - AI-powered educational insights dashboard
*Deployed on Vercel • Powered by AWS Lambda*
