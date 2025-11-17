import express from "express";
import OpenAI from "openai";
import dotenv from "dotenv";
dotenv.config();

const app = express();
app.use(express.json());

const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

app.post("/api/chat", async (req, res) => {
  const userInput = req.body.input;
  const completion = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [
      { role: "system", content: "You are a helpful movie recommendation assistant." },
      { role: "user", content: userInput },
    ],
  });

  res.json({ reply: completion.choices[0].message.content });
});

app.listen(3000, () => console.log("Server running on http://localhost:3000"));
