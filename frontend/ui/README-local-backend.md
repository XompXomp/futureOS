# Local Backend Setup

## Overview
The local backend (`local-backend.js`) now uses a simplified architecture that eliminates the need for a separate API server. It directly shares data with the React app through a shared data file.

## Architecture

### Before (Complex)
```
LLM Server → local-backend.js → api-server.js → React App (IndexedDB)
```

### After (Simplified)
```
LLM Server → local-backend.js ←→ shared-data.js ←→ React App (IndexedDB)
```

## Files

### `shared-data.js`
- Contains all the hardcoded data that both the local backend and React app use
- Exports data for both Node.js (local backend) and browser (React app) environments
- Single source of truth for all sample data

### `local-backend.js`
- Express server that runs on port 8002
- Imports data directly from `shared-data.js`
- No longer makes HTTP requests to fetch data
- Handles updates from the LLM server and stores them locally

### `db.ts`
- React app's IndexedDB interface
- Can optionally use shared data from `shared-data.js` if available
- Maintains the same API for the React app

## How to Use

### 1. Start the Local Backend
```bash
cd frontend/ui
node local-backend.js
```

### 2. Start the React App
```bash
cd frontend/ui
npm start
```

### 3. Test the Setup
```bash
cd frontend/ui
node test-local-backend.js
```

## Benefits

1. **Simplified Architecture**: No more separate API server needed
2. **Direct Data Access**: Local backend accesses data directly without HTTP requests
3. **Single Source of Truth**: All data is defined in `shared-data.js`
4. **Better Performance**: No network overhead for data access
5. **Easier Maintenance**: Fewer files and dependencies to manage

## Data Flow

1. **LLM Server** sends updates to `local-backend.js` via `/api/healthcare-updates`
2. **Local Backend** updates its local data directly
3. **React App** polls for updates via `/api/latest-update`
4. **Shared Data** ensures both systems use the same initial data

## Adding New Data

To add new hardcoded data:

1. Edit `shared-data.js` to add your new data
2. Both the local backend and React app will automatically use the new data
3. No need to update multiple files or make HTTP requests

## Testing

The `test-local-backend.js` script tests:
- Local backend connectivity
- Patient profile retrieval
- Updates retrieval
- Healthcare update functionality
- Memory and links retrieval

Run it to verify everything is working correctly. 