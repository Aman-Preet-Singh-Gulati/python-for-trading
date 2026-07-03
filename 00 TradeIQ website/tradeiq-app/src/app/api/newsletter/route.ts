import { NextResponse } from 'next/server';
import { z } from 'zod';
import { appendNewsletterSubscription } from '@/lib/sheets';

const newsletterSchema = z.object({
  email: z.string().email("Please provide a valid email address."),
  website: z.string().optional(), // Honeypot for bots
});

// Reuse the readable date formatter
function formatReadableDate() {
  const date = new Date();
  const time = date.toLocaleString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  const day = date.getDate();
  const suffix = ["th", "st", "nd", "rd"][day % 10 > 3 ? 0 : (day % 100 - day % 10 != 10) ? day % 10 : 0];
  const month = date.toLocaleString('en-US', { month: 'long' });
  return `${time} ${day}${suffix} ${month} ${date.getFullYear()}`;
}

export async function POST(req: Request) {
  try {
    let body;
    try {
      body = await req.json();
    } catch (parseError) {
      return NextResponse.json({ error: "Invalid JSON format." }, { status: 400 });
    }

    const parsed = newsletterSchema.safeParse(body);
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.issues[0].message }, { status: 400 });
    }

    const { email, website } = parsed.data;

    // Honeypot trap
    if (website && website.length > 0) {
      return NextResponse.json({ success: true, message: "Subscription successful." }, { status: 200 });
    }

    const row = [formatReadableDate(), email];

    await appendNewsletterSubscription(row);

    return NextResponse.json({ success: true, message: "Successfully subscribed!" }, { status: 200 });
    
  } catch (error: any) {
    console.error("[Newsletter API Error]:", error);
    return NextResponse.json({ error: "Server Error. Please try again." }, { status: 500 });
  }
}
