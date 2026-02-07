# Meta OAuth

A simple Flask application that handles the complete Meta (Facebook) OAuth flow for connecting Meta Ads accounts.

## How It Works

1. User clicks **"Connect Meta Ads"** on the home page
2. Redirects to Meta's login/authorization page
3. User grants `ads_management` and `ads_read` permissions
4. Meta redirects back with an authorization code
5. The app exchanges the code for an access token
6. Token is stored and ready for API calls

## Setup

### Prerequisites

- Python 3.8+
- A [Meta Developer App](https://developers.facebook.com/apps/) with Facebook Login enabled

### Installation

```bash
git clone https://github.com/chaitanyaambade/Meta-OAuth.git
cd Meta-OAuth
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
META_APP_ID=your_app_id_here
META_APP_SECRET=your_app_secret_here
REDIRECT_URI=http://localhost:5000/callback
SECRET_KEY=change-this-to-a-random-secret-key
```

> Make sure `http://localhost:5000/callback` is added as a **Valid OAuth Redirect URI** in your Meta App settings.

## Usage

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser and click **Connect Meta Ads**.

## API Endpoints

| Route | Description |
|-------|-------------|
| `/` | Home page with connect button |
| `/login` | Initiates the OAuth flow |
| `/callback` | Handles the Meta OAuth redirect |
| `/token` | View stored token info (preview only) |

## Tech Stack

- **Flask** - Web framework
- **Requests** - HTTP client for Meta Graph API
- **python-dotenv** - Environment variable management
