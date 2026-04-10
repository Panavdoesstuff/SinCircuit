const TYRE_COLORS = {
  soft: "#E24B4A",
  medium: "#EF9F27",
  hard: "#D3D1C7"
};

export default function PitTimeline({ pitHistory, currentLap, compound }) {
  return (
    <div style={{padding:"1rem", backgroundColor: "#1a1a1a", borderRadius: "12px", border: "1px solid #333"}}>
      <div style={{fontSize:"11px", fontWeight:500,
                    textTransform:"uppercase", letterSpacing:"0.06em",
                    color:"#888", marginBottom:"8px"}}>
        Current Tyre Stint
      </div>
      <div style={{display:"flex", gap:"6px", flexWrap:"wrap"}}>
        {/* Render past pit stops */}
        {pitHistory && pitHistory.map((p, i) => (
          <div key={i} style={{
            background: TYRE_COLORS[p.from] || "#ccc",
            borderRadius:"6px", padding:"4px 10px",
            fontSize:"12px", color:"white", fontWeight:500}}>
            {p.from.toUpperCase()} → lap {p.lap}
          </div>
        ))}
        
        {/* Render current tyre */}
        <div style={{
          background: TYRE_COLORS[compound] || "#ccc",
          borderRadius:"6px", padding:"4px 10px",
          fontSize:"12px", color:"white", fontWeight:500,
          border:"2px solid #fff"}}>
          {compound?.toUpperCase()} (CURRENT)
        </div>
      </div>
    </div>
  );
}