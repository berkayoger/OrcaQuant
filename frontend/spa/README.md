# OrcaQuant React SPA

Modern React Single Page Application for OrcaQuant Crypto Analysis Platform.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type check
npm run type-check
```

## 📁 Project Structure

```
src/
├── components/          # Reusable components
│   ├── Layout.tsx      # Main layout wrapper
│   ├── ProtectedRoute.tsx
│   └── NotificationManager.tsx
├── pages/              # Page components
│   ├── Login.tsx
│   ├── Dashboard.tsx
│   └── Predictions.tsx
├── store/              # Redux store
│   ├── store.ts
│   └── slices/
│       ├── authSlice.ts
│       └── appSlice.ts
├── services/           # API services
│   └── api.ts
├── hooks/              # Custom hooks
│   ├── useAppDispatch.ts
│   └── useAppSelector.ts
├── types/              # TypeScript types
│   └── index.ts
└── utils/              # Utility functions
```

## 🔧 Configuration

- **Vite** - Build tool and dev server
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **Redux Toolkit** - State management
- **React Router** - Client-side routing
- **Axios** - HTTP client

## 🔐 Authentication

The app uses JWT tokens with automatic refresh:
- Access tokens stored in Redux state
- Refresh tokens for automatic renewal
- Protected routes based on subscription levels

## 🎯 Features

- **Modern SPA Architecture**
- **JWT Authentication with Refresh**
- **Responsive Design**
- **Real-time Notifications**
- **Protected Routes**
- **Subscription-based Access Control**
- **Backward Compatibility with Legacy API**

## 🌐 API Integration

The app automatically detects SPA requests and receives JSON responses with tokens, while maintaining backward compatibility with cookie-based authentication for legacy clients.

## 🏗️ Development

1. **Start Backend**: Ensure the Flask backend is running on `http://localhost:5000`
2. **Start Frontend**: Run `npm run dev` to start the Vite dev server on `http://localhost:3000`
3. **Proxy Setup**: API calls are automatically proxied to the backend during development

## 📦 Production Build

```bash
npm run build
```

The build outputs to the `dist/` directory and includes:
- Code splitting for optimal loading
- Tree shaking for smaller bundles
- Source maps for debugging
- Optimized assets

## 🔄 Migration from Legacy

This SPA replaces the traditional multi-page HTML application with:
- ✅ No page refreshes
- ✅ Faster navigation
- ✅ Better user experience
- ✅ Modern development workflow
- ✅ Maintainable codebase

## 🐛 Troubleshooting

### CORS Issues
- Ensure backend CORS is configured for `http://localhost:3000`
- Check that `X-Requested-With: XMLHttpRequest` header is sent

### Authentication Issues
- Clear localStorage and sessionStorage
- Check token expiry in Redux DevTools
- Verify backend JWT configuration

### API Issues
- Check network tab for request/response details
- Verify API endpoints in backend
- Check Vite proxy configuration