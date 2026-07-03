import { NextResponse } from 'next/server';
import { z } from 'zod';
import { appendRegistration } from '@/lib/sheets';

// ----------------------------------------------------------------------
// Zod Schema Validation
// ----------------------------------------------------------------------
const registerSchema = z.object({
  // Basic Details
  fullName: z.string().min(2, "Full name is required"),
  whatsappNumber: z.string().min(7, "Valid WhatsApp number is required"),
  emailAddress: z.string().email("Invalid email address"),
  cityCountry: z.string().min(2, "City and Country are required"),

  // Trading Background
  tradingExperience: z.string().min(1, "Trading experience is required"),
  tradingStyle: z.string().min(1, "Trading style is required"),

  // Readiness & Challenges
  algoExperience: z.string().min(1, "Algo experience is required"),
  biggestChallenge: z.string().min(1, "Biggest challenge is required"),

  // Goals
  reasonToJoin: z.string().min(1, "Reason to join is required"),
  capitalSize: z.string().min(1, "Capital size is required"),

  // Final Thoughts
  purchasedCourseBefore: z.enum(["Yes", "No"]),
  missingFromCourse: z.string().optional(),
  successOutcome: z.string().min(3, "Your ideal outcome description is too short. Please type something reasonable so we can understand your goals better."),

  // Spam Protection (Honeypot)
  // If a bot fills this field, the validation passes but we intercept it in the handler
  website: z.string().optional(),
});

// ----------------------------------------------------------------------
// Basic In-Memory Rate Limiter Map (IP -> Timestamp)
// Includes a cleanup mechanism to prevent Memory Leaks (OOM Crashes)
// ----------------------------------------------------------------------
const rateLimitMap = new Map<string, number>();
const RATE_LIMIT_MS = 60 * 1000; // 1 request per minute per IP

// Cleanup sweep every 10 minutes to prevent map growing indefinitely
setInterval(() => {
  const now = Date.now();
  rateLimitMap.forEach((timestamp, ip) => {
    if (now - timestamp > RATE_LIMIT_MS) {
      rateLimitMap.delete(ip);
    }
  });
}, 10 * 60 * 1000);

// ----------------------------------------------------------------------
// Helper: Format Date to Readable String (e.g. 8:00 AM 23rd June 2026)
// ----------------------------------------------------------------------
function formatReadableDate() {
  const date = new Date();
  const time = date.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  const day = date.getDate();
  const suffix = ["th", "st", "nd", "rd"][day % 10 > 3 ? 0 : (day % 100 - day % 10 != 10) ? day % 10 : 0];
  const month = date.toLocaleString('en-US', { month: 'long' });
  return `${time} ${day}${suffix} ${month} ${date.getFullYear()}`;
}

// ----------------------------------------------------------------------
// POST Handler: Process Form Submissions
// ----------------------------------------------------------------------
export async function POST(req: Request) {
  try {
    // 1. Rate Limiting Check
    const ip = req.headers.get('x-forwarded-for') || 'unknown';
    const now = Date.now();
    const lastRequest = rateLimitMap.get(ip);

    if (lastRequest && (now - lastRequest) < RATE_LIMIT_MS) {
      return NextResponse.json({ error: "Too many requests. Please try again later." }, { status: 429 });
    }
    rateLimitMap.set(ip, now);

    // 2. Parse and Validate Request Body safely
    let body;
    try {
      body = await req.json();
    } catch (parseError) {
      return NextResponse.json({ error: "Invalid JSON format in request body" }, { status: 400 });
    }

    const parsed = registerSchema.safeParse(body);

    if (!parsed.success) {
      // Map Zod errors to a cleaner format
      const errors = parsed.error.issues.map(issue => ({
        field: issue.path[0],
        message: issue.message
      }));
      return NextResponse.json({ error: "Validation failed", details: errors }, { status: 400 });
    }

    const data = parsed.data;

    // 3. Spam Protection (Honeypot) Check
    // Bots scan for generic fields like 'website' and fill them automatically.
    if (data.website && data.website.length > 0) {
      console.warn(`[Spam Blocked] Honeypot filled by IP: ${ip}`);
      // Return 200 OK so the bot thinks it succeeded
      return NextResponse.json({ success: true, message: "Registration successful" }, { status: 200 });
    }

    // 4. Format Data for Google Sheets
    // Map the validated data to a flat array corresponding to the columns in the Sheet.
    const row = [
      formatReadableDate(), // Timestamp formatted cleanly
      data.fullName,
      data.whatsappNumber,
      data.emailAddress,
      data.cityCountry,
      data.tradingExperience,
      data.tradingStyle,
      data.algoExperience,
      data.biggestChallenge,
      data.reasonToJoin,
      data.capitalSize,
      data.purchasedCourseBefore,
      data.missingFromCourse || "N/A", // Default to N/A if optional
      data.successOutcome
    ];

    // 5. Append to Google Sheets
    await appendRegistration(row);

    return NextResponse.json({ success: true, message: "Registration successful" }, { status: 200 });

  } catch (error: any) {
    console.error("[API Error] Registration failed:", error);
    return NextResponse.json({ error: "Internal Server Error", details: error.message }, { status: 500 });
  }
}

// ----------------------------------------------------------------------
// GET Handler: Health Check & Environment Verification
// ----------------------------------------------------------------------
export async function GET() {
  const hasSheetId = !!process.env.GOOGLE_SHEET_ID;
  const hasServiceJson = !!process.env.GOOGLE_SERVICE_ACCOUNT_JSON;
  const hasEmailKey = !!(process.env.GOOGLE_CLIENT_EMAIL && process.env.GOOGLE_PRIVATE_KEY);

  const isConfigured = hasSheetId && (hasServiceJson || hasEmailKey);

  return NextResponse.json({
    status: isConfigured ? "healthy" : "misconfigured",
    message: "TradeIQ Registration API",
    config: {
      googleSheetIdSet: hasSheetId,
      credentialsSet: hasServiceJson || hasEmailKey,
    }
  }, {
    status: isConfigured ? 200 : 500
  });
}
