import { GoogleGenAI } from "@google/genai";
import { Product, SalesData } from "../types";

const ai = new GoogleGenAI({ apiKey: (import.meta as any).env.VITE_GEMINI_API_KEY || "" });

export const generateProductDescription = async (productName: string, category: string): Promise<string> => {
  try {
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `Write a compelling, SEO-friendly product description for an e-commerce item. 
      Product Name: ${productName}
      Category: ${category}
      Target Audience: General consumers looking for quality and style.
      Tone: Professional yet engaging.
      Length: Around 50-75 words.`,
    });
    return response.text || "Description generation failed.";
  } catch (error) {
    console.error("Error generating description:", error);
    return "Unable to generate description at this time. Please try again later.";
  }
};

export const generateDashboardInsights = async (salesData: SalesData[]): Promise<string> => {
  try {
    const dataString = JSON.stringify(salesData);
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: `Analyze the following sales data for an e-commerce store and provide a brief, actionable executive summary (max 3 bullet points) focusing on trends and opportunities.
      Data: ${dataString}`,
    });
    return response.text || "No insights available.";
  } catch (error) {
    console.error("Error generating insights:", error);
    return "AI Insights currently unavailable.";
  }
};