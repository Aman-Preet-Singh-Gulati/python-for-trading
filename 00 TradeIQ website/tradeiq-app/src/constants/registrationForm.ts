import { FormSection } from "@/types/form";

export const registrationFormSections: FormSection[] = [
  {
    id: 1,
    title: "Basic Details",
    fields: [
      {
        id: "fullName",
        label: "FULL NAME",
        type: "text",
        required: true,
        placeholder: "John Doe"
      },
      {
        id: "whatsappNumber",
        label: "WHATSAPP NUMBER",
        type: "tel",
        required: true,
        placeholder: "+91 98765 43210"
      },
      {
        id: "emailAddress",
        label: "EMAIL ADDRESS",
        type: "email",
        required: true,
        placeholder: "john@example.com"
      },
      {
        id: "cityCountry",
        label: "CITY & COUNTRY",
        type: "text",
        required: true,
        placeholder: "Mumbai, India"
      }
    ]
  },
  {
    id: 2,
    title: "Trading Background",
    fields: [
      {
        id: "tradingExperience",
        label: "How long have you been trading?",
        type: "radio",
        required: true,
        options: ["Beginner", "Less than 1 year", "1–3 years", "More than 3 years"]
      },
      {
        id: "tradingStyle",
        label: "What best describes your trading style?",
        type: "radio",
        required: true,
        options: ["Scalping", "Intraday", "Swing Trading", "Positional", "Long-term Investing", "I haven't developed a strategy yet"]
      }
    ]
  },
  {
    id: 3,
    title: "Readiness & Challenges",
    fields: [
      {
        id: "algoExperience",
        label: "What is your current experience with Algo Trading?",
        type: "radio",
        required: true,
        options: ["Never tried it", "Watched videos only", "Built simple strategies", "Already running live algos"]
      },
      {
        id: "biggestChallenge",
        label: "What is your biggest challenge in trading? (Choose one)",
        type: "radio",
        required: true,
        options: ["Emotional trading", "Lack of consistency", "Risk management", "Coding algorithms", "Backtesting", "Strategy execution", "Time management"]
      }
    ]
  },
  {
    id: 4,
    title: "Your Goals",
    fields: [
      {
        id: "reasonToJoin",
        label: "Why do you want to join this bootcamp?",
        type: "radio",
        required: true,
        options: ["Build my first trading bot", "Automate my existing strategy", "Become a full-time trader", "Remove emotions from trading", "Learn Pine Script", "Learn professional backtesting"]
      },
      {
        id: "capitalSize",
        label: "Approximately how much capital do you currently trade with?",
        type: "radio",
        required: true,
        options: ["Not trading yet", "Under ₹50,000", "₹50k–₹2L", "₹2L–₹10L", "Above ₹10L"]
      }
    ]
  },
  {
    id: 5,
    title: "Final Thoughts",
    fields: [
      {
        id: "purchasedCourseBefore",
        label: "Have you ever purchased any trading course before?",
        type: "radio",
        required: true,
        options: ["Yes", "No"]
      },
      {
        id: "missingFromCourse",
        label: "What was missing from that course?",
        type: "textarea",
        required: false,
        placeholder: "Share your thoughts...",
        condition: {
          fieldId: "purchasedCourseBefore",
          equals: "Yes"
        }
      },
      {
        id: "successOutcome",
        label: "What outcome would make this bootcamp a huge success for you?",
        type: "textarea",
        required: true,
        placeholder: "Describe your ideal outcome..."
      }
    ]
  }
];

export const getInitialFormData = (): Record<string, string> => {
  const initialData: Record<string, string> = {};
  registrationFormSections.forEach(section => {
    section.fields.forEach(field => {
      initialData[field.id] = "";
    });
  });
  return initialData;
};
