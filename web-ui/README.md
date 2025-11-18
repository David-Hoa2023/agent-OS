# Codex Prime Web UI

Enterprise-ready React + TypeScript web interface for Codex Prime AI Agent Platform.

## Features

### 💬 **Chat Interface**
- Real-time streaming responses via WebSocket
- Token-by-token streaming visualization
- Session management
- Message history
- HTTP API fallback

### 🧠 **Memory Browser**
- Explore 3-tier memory system (Embers, Runes, Glyphs)
- Semantic + keyword search
- Add new memories with tags
- Filter by memory tier
- View memory metadata and references

### 📊 **Analytics Dashboard**
- Real-time metrics visualization
- Event analytics with charts
- Performance histograms
- Top events tracking
- Auto-refresh every 30 seconds

### ⚙️ **Admin Panel**
- User management (create, edit, list)
- Role-based access control (RBAC)
- Role assignment (admin, developer, operator, viewer)
- Audit log viewer
- Security event monitoring

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **React Router** - Navigation
- **Recharts** - Data visualization
- **Axios** - HTTP client
- **WebSocket API** - Real-time communication

## Installation

### Prerequisites

- Node.js 16+ and npm
- Codex Prime backend running on `http://localhost:8000`
- WebSocket server running on `ws://localhost:8765`

### Setup

```bash
# Navigate to web-ui directory
cd web-ui

# Install dependencies
npm install

# Start development server
npm start
```

The app will open at `http://localhost:3000`

## Project Structure

```
web-ui/
├── public/
│   └── index.html           # HTML template
├── src/
│   ├── api/
│   │   └── client.ts        # API client & types
│   ├── components/
│   │   ├── ChatInterface.tsx     # Chat UI with streaming
│   │   ├── ChatInterface.css
│   │   ├── MemoryBrowser.tsx     # Memory explorer
│   │   ├── MemoryBrowser.css
│   │   ├── AnalyticsDashboard.tsx # Analytics & metrics
│   │   ├── AnalyticsDashboard.css
│   │   ├── AdminPanel.tsx        # User & system admin
│   │   └── AdminPanel.css
│   ├── App.tsx              # Main app with routing
│   ├── App.css
│   ├── index.tsx            # Entry point
│   └── index.css
├── package.json
├── tsconfig.json
└── README.md
```

## Configuration

### Backend URL

Update API base URL in `src/api/client.ts`:

```typescript
const apiClient = new CodexPrimeAPI(
  'http://localhost:8000',  // HTTP API
  'ws://localhost:8765'      // WebSocket
);
```

### Authentication

The app currently uses a demo user. To implement real authentication:

1. Update `App.tsx` to add login/logout functionality
2. Store auth token in localStorage
3. Call `apiClient.setAuthToken(token)` after login
4. Add protected routes with auth guards

## Available Scripts

### `npm start`
Runs the app in development mode at [http://localhost:3000](http://localhost:3000)

### `npm run build`
Builds the app for production to the `build` folder.

```bash
npm run build
```

### `npm test`
Launches the test runner in interactive watch mode.

```bash
npm test
```

## Usage

### 1. Chat Interface

Navigate to `/chat` to interact with the AI agent:

- Type messages in the input field
- Press Enter or click "Send"
- Watch responses stream in real-time
- View full conversation history

### 2. Memory Browser

Navigate to `/memory` to explore memories:

- **Filter by tier**: Click Ember, Rune, or Glyph buttons
- **Search**: Enter semantic or keyword queries
- **Add memory**: Fill in text, select tier, add tags
- View memory metadata, timestamps, and reference counts

### 3. Analytics Dashboard

Navigate to `/analytics` for insights:

- View total events and 24h activity
- See active users and projects
- Explore top events bar chart
- Check counter distribution pie chart
- Monitor performance histograms
- Click "Refresh" to update data

### 4. Admin Panel

Navigate to `/admin` for administration:

**User Management Tab:**
- Create new users with username and email
- Assign roles (admin, developer, operator, viewer)
- Edit existing user roles
- View user creation dates

**Audit Logs Tab:**
- View security events and system logs
- Filter by severity (critical, error, warning, info)
- See user actions and timestamps
- Monitor access attempts and violations

## API Endpoints Used

The web UI connects to these backend endpoints:

- `POST /chat` - Send chat messages
- `GET /memories` - Get memories (with tier filter)
- `POST /memories` - Add new memory
- `POST /memories/search` - Semantic search
- `GET /sessions` - List sessions
- `POST /sessions` - Create session
- `GET /metrics` - Get Prometheus metrics
- `GET /analytics` - Get analytics data
- `GET /admin/users` - List users
- `POST /admin/users` - Create user
- `PUT /admin/users/:id/roles` - Update user roles
- `GET /admin/audit` - Get audit logs

## WebSocket Messages

The UI sends/receives these WebSocket message types:

**Sent:**
```json
{
  "type": "auth",
  "user_id": "user123"
}
```

```json
{
  "type": "chat",
  "message": "Hello!",
  "session_id": "session123"
}
```

**Received:**
```json
{
  "type": "stream_chunk",
  "content": "Hello"
}
```

```json
{
  "type": "stream_complete"
}
```

## Deployment

### Production Build

```bash
# Build for production
npm run build

# Serve the build folder
npx serve -s build
```

### Environment Variables

Create `.env` file for production:

```env
REACT_APP_API_URL=https://api.yourapp.com
REACT_APP_WS_URL=wss://ws.yourapp.com
```

Update `src/api/client.ts` to use environment variables:

```typescript
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8765';

const apiClient = new CodexPrimeAPI(API_URL, WS_URL);
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:

```bash
docker build -t codex-prime-ui .
docker run -p 80:80 codex-prime-ui
```

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Performance

- Initial load: < 2s
- Code splitting for faster loads
- Lazy loading of charts
- Auto-refresh with configurable intervals
- WebSocket for efficient streaming

## Troubleshooting

### WebSocket Connection Failed

- Ensure backend WebSocket server is running on port 8765
- Check CORS settings on backend
- Verify WebSocket URL in `client.ts`

### API Requests Failing

- Confirm backend is running on port 8000
- Check network tab in browser DevTools
- Verify CORS headers on backend

### Charts Not Rendering

- Ensure data is being fetched successfully
- Check console for errors
- Verify recharts is installed: `npm install recharts`

## Future Enhancements

- [ ] Authentication & login page
- [ ] User profile settings
- [ ] Dark mode toggle
- [ ] Notification system
- [ ] Collaborative sessions UI
- [ ] Agent workflow builder
- [ ] Plugin marketplace UI
- [ ] Advanced search filters
- [ ] Export analytics reports
- [ ] Mobile-responsive improvements

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request

## License

Part of Codex Prime - See main project LICENSE
