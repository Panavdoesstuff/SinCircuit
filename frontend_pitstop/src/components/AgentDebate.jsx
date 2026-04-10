import { useStream } from "../hooks/useStream";

const AGENT_COLORS = {
  "Race Engineer": "#639922",
  "Tyre Strategist": "#BA7517",
  "Weather Oracle": "#185FA5",
  "Rival Analyst": "#A32D2D",
  "Pit Wall Director": "#533AB7"
};

export default function AgentDebate({ raceId, apiBase }) {
  const { messages, done, startStream } = useStream();

  const handleDebate = () => {
    startStream(`${apiBase}/race/${raceId}/stream`);
  };

  return (
    <div style={{ padding: "1rem" }}>
      <button onClick={handleDebate} className="debate-btn">
        Run Pit Wall Debate
      </button>

      <div className="messages-container">
        {messages.map((msg, i) => (
          <div key={i} className="agent-card" style={{ borderLeft: `3px solid ${AGENT_COLORS[msg.agent] || "#888"}` }}>
            <div className="agent-name" style={{ color: AGENT_COLORS[msg.agent] || "#888" }}>
              {msg.agent}
            </div>
            <div className="agent-text">
              {msg.text}
              {!msg.done && <span className="cursor">▌</span>}
            </div>
          </div>
        ))}
      </div>

      {done && <div className="complete-tag">✓ Strategy Finalized</div>}
    </div>
  );
}