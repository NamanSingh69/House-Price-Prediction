import { z } from 'zod';

// The input schema expected by the Python ML backend
export const PredictionRequestSchema = z.object({
    area: z.number().min(100),
    bedrooms: z.number().min(0),
    bathrooms: z.number().min(0),
    stories: z.number().min(1),
    parking: z.number().min(0),
    mainroad: z.enum(['yes', 'no']),
    guestroom: z.enum(['yes', 'no']),
    basement: z.enum(['yes', 'no']),
    hotwaterheating: z.enum(['yes', 'no']),
    airconditioning: z.enum(['yes', 'no']),
    prefarea: z.enum(['yes', 'no']),
    furnishingstatus: z.enum(['furnished', 'semi-furnished', 'unfurnished'])
});

export type PredictionRequest = z.infer<typeof PredictionRequestSchema>;

// The output schema expected FROM the Python ML backend
export const PredictionResponseSchema = z.object({
    predicted_price: z.number(),
    error: z.string().optional()
});

export type PredictionResponse = z.infer<typeof PredictionResponseSchema>;

// The output schema expected from the Gemini Google Search Agent
export const AgentResponseSchema = z.object({
    analysis: z.string(),
    error: z.string().optional()
});

export type AgentResponse = z.infer<typeof AgentResponseSchema>;
