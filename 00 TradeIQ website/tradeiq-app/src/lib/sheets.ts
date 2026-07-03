import { google } from 'googleapis';

// 1. Module-level cached client to prevent re-authenticating on every request
let cachedAuth: any = null;

/**
 * Initialize and authenticate the Google Sheets API client.
 * Supports GOOGLE_SERVICE_ACCOUNT_JSON (stringified JSON) OR individual credentials.
 */
function getGoogleAuth() {
  if (cachedAuth) {
    return cachedAuth;
  }

  const {
    GOOGLE_SERVICE_ACCOUNT_JSON,
    GOOGLE_CLIENT_EMAIL,
    GOOGLE_PRIVATE_KEY,
  } = process.env;

  let credentials;

  // Try parsing the full JSON string first
  if (GOOGLE_SERVICE_ACCOUNT_JSON) {
    try {
      credentials = JSON.parse(GOOGLE_SERVICE_ACCOUNT_JSON);
    } catch (error) {
      throw new Error("Failed to parse GOOGLE_SERVICE_ACCOUNT_JSON environment variable.");
    }
  }
  // Fallback to individual email/key pairs
  else if (GOOGLE_CLIENT_EMAIL && GOOGLE_PRIVATE_KEY) {
    credentials = {
      client_email: GOOGLE_CLIENT_EMAIL,
      // Replace literal \n in the env var string to actual newlines
      private_key: GOOGLE_PRIVATE_KEY.replace(/\\n/g, '\n'),
    };
  } else {
    throw new Error(
      "Missing Google Service Account credentials. Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_CLIENT_EMAIL & GOOGLE_PRIVATE_KEY."
    );
  }

  // Authenticate the client with the required scopes for Google Sheets
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });

  cachedAuth = auth;
  return auth;
}

/**
 * Appends a single row of data to the specified Google Sheet.
 * 
 * @param row - A flat array of strings representing the data columns.
 */
export async function appendRegistration(row: string[]) {
  const spreadsheetId = process.env.GOOGLE_SHEET_ID;

  if (!spreadsheetId) {
    throw new Error("Missing GOOGLE_SHEET_ID in environment variables.");
  }

  const auth = getGoogleAuth();
  const sheets = google.sheets({ version: 'v4', auth });

  try {
    const response = await sheets.spreadsheets.values.append({
      spreadsheetId,
      // The range is typically the sheet name. 'Registrations!A:Z' captures the whole sheet.
      range: 'Registrations!A:Z',
      valueInputOption: 'RAW',
      insertDataOption: 'INSERT_ROWS',
      requestBody: {
        values: [row],
      },
    });

    return response.data;
  } catch (error: any) {
    console.error("Error appending to Google Sheets:", error.message);
    throw new Error(`Google Sheets API Error: ${error.message}`);
  }
}

/**
 * Appends a single row of data to the Newsletter Subscription sheet.
 */
export async function appendNewsletterSubscription(row: string[]) {
  const spreadsheetId = process.env.GOOGLE_SHEET_ID;

  if (!spreadsheetId) {
    throw new Error("Missing GOOGLE_SHEET_ID in environment variables.");
  }

  const auth = getGoogleAuth();
  const sheets = google.sheets({ version: 'v4', auth });

  try {
    const response = await sheets.spreadsheets.values.append({
      spreadsheetId,
      range: 'Newsletter Subscription!A:Z',
      valueInputOption: 'RAW',
      insertDataOption: 'INSERT_ROWS',
      requestBody: {
        values: [row],
      },
    });

    return response.data;
  } catch (error: any) {
    console.error("Error appending newsletter to Google Sheets:", error.message);
    throw new Error(`Google Sheets API Error: ${error.message}`);
  }
}
