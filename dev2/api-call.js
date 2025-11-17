import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY, // store in .env
});

async function getMovieSuggestions(userInput) {
  const response = await client.chat.completions.create({
    model: "gpt-4o-mini", // or gpt-4-turbo
    messages: [
      { role: "system", content: "You are a movie recommendation assistant." },
      { role: "user", content: `I like ${userInput}. Suggest similar shows or movies.` },
    ],
  });

  console.log(response.choices[0].message.content);
}

getMovieSuggestions("Inception and Interstellar");
