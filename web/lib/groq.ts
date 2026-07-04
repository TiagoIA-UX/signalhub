import "groq-sdk/shims/web";
import Groq from "groq-sdk";

let client: Groq | null = null;

export function getGroq(): Groq {
  if (!client) {
    const apiKey = process.env.GROQ_API_KEY;
    if (!apiKey) {
      throw new Error("GROQ_API_KEY ausente");
    }
    client = new Groq({ apiKey });
  }
  return client;
}
