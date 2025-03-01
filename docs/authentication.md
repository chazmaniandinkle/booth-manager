# Authentication System

The Booth Assets Manager now includes a browser-based authentication system that allows you to log in to your Booth account and download your purchased items directly through the application.

## How It Works

The authentication system uses Playwright, a browser automation library, to provide a seamless login experience:

1. When you run `booth-auth login`, a browser window opens.
2. You log into your Booth account normally in this window.
3. Once logged in, the application automatically captures the authentication cookies.
4. These cookies are securely stored for future sessions.
5. The browser window closes automatically after successful login.

This approach is:
- User-friendly: No need to manually export cookies
- Secure: Your login credentials are entered directly in the browser
- Reliable: Works with Booth's authentication system
- Privacy-focused: Credentials are never stored, only session cookies

## Commands

### Login

```bash
booth-auth login
```

This command opens a browser window where you can log in to your Booth account. The window will close automatically after successful login, and your session will be saved for future use.

### Status

```bash
booth-auth status
```

This command checks if you are currently authenticated with Booth and displays your authentication status. It also shows when you last logged in.

### Logout

```bash
booth-auth logout
```

This command logs you out by removing the stored authentication cookies and clearing your session data.

## Purchases

Once authenticated, you can list and download your purchased items:

### List Purchases

```bash
booth-auth purchases [--update-db]
```

This command lists all your purchased items from Booth, including their title, ID, purchase date, and price. If you use the `--update-db` flag, it will also update your local database with this information.

### Download Items

```bash
# Download a specific item
booth-auth download --item-id ITEM_ID

# Download all purchased items
booth-auth download --all

# Specify output directory
booth-auth download --all --output-dir /path/to/directory

# Control concurrent downloads
booth-auth download --all --concurrent 5
```

These commands download your purchased items from Booth. You can download a specific item by ID or all your purchased items. You can also specify an output directory and control the number of concurrent downloads.

## Download Organization

Downloaded files are organized into a folder structure similar to the main item structure:

```
BoothDownloads/
├── {item_id}_{title}/
│   ├── downloads/
│   │   ├── file1.zip
│   │   └── file2.pdf
│   └── extracted/
│       └── file1/
```

Each item gets its own folder named with the item ID and title. Inside this folder, there are two subfolders:
- `downloads/`: Contains the downloaded files
- `extracted/`: Reserved for extracted content from archives

## Database Integration

The authentication system integrates with the database to track your purchases and downloads:

- Purchase information is stored in the Items table
- Download information is stored in the Downloads table
- You can query this information using the database API

## Troubleshooting

### Browser Issues

- **Browser doesn't open**: Ensure Playwright is properly installed with `playwright install`
- **Browser crashes**: Try running `playwright install` again to reinstall the browser binaries
- **Browser hangs**: The login process has a 5-minute timeout; if it exceeds this, the process will terminate

### Authentication Issues

- **Login timeout**: The default timeout is 5 minutes. Try again if needed.
- **Session expires**: Sessions will eventually expire. Run `booth-auth login` to reauthenticate.
- **Login fails**: Make sure you're entering the correct credentials in the browser window.

### Download Issues

- **Download failures**: Check your internet connection and Booth account status.
- **Parallel download errors**: Reduce the concurrency with `--concurrent 2` if you encounter issues.
- **Large file downloads**: Ensure you have sufficient disk space for large downloads.
- **Access denied**: Make sure you have actually purchased the item you're trying to download.

## Security Considerations

- Your login credentials are never stored by the application.
- Only session cookies are stored, which expire after a certain period.
- Cookies are stored in a JSON file in your user configuration directory.
- The application validates your session before performing operations.
- You can log out at any time to remove the stored cookies.

## Technical Details

The authentication system consists of three main components:

1. **BrowserAuth**: Handles browser automation, login, and cookie management.
2. **BoothDownloader**: Handles downloading purchased items and file management.
3. **AuthCLI**: Provides the command-line interface for authentication and downloads.

These components work together to provide a seamless authentication and download experience.
