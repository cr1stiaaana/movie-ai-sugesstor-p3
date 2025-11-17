function App() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");

  const handleSubmit = async () => {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ input }),
    });
    const data = await res.json();
    setResponse(data.reply);
  };

  return (
    <div>
      <h1>🎥 Movie Recommender</h1>
      <input value={input} onChange={e => setInput(e.target.value)} placeholder="Tell me what you like..." />
      <button onClick={handleSubmit}>Get Suggestions</button>
      <p>{response}</p>
    </div>
  );
}
