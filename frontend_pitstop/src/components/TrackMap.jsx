import React, { useEffect, useRef } from "react";

const TRACK_PATH = "M 100 200 Q 100 50 250 50 Q 400 50 400 200 Q 400 350 250 350 Q 100 350 100 200";
const TOTAL_PATH_LENGTH = 800; 

export default function TrackMap({ currentLap = 1, totalLaps = 50, inPit = false }) {
  const dotRef = useRef(null);

  useEffect(() => {
    if (!dotRef.current) return;

    // Fixed math for lap-by-lap movement
    const progress = currentLap / totalLaps;
    const offset = TOTAL_PATH_LENGTH * (1 - progress);
    
    dotRef.current.style.strokeDashoffset = offset;
  }, [currentLap, totalLaps]);

  const lapPercent = ((currentLap / totalLaps) * 100).toFixed(0);

  return (
    <div style={{ padding: "1.5rem", background: "#151515", borderRadius: "16px", border: "1px solid #333", textAlign: "center" }}>
      <div style={{ fontSize: "11px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.1em", color: "#888", marginBottom: "1rem" }}>
        TRACK POSITION — LAP {currentLap}/{totalLaps}
      </div>

      <svg viewBox="0 0 500 400" style={{ width: "100%", maxWidth: "350px", margin: "0 auto" }}>
        {/* Track Outline */}
        <path d={TRACK_PATH} fill="none" stroke="#333" strokeWidth="18" strokeLinecap="round" />
        
        {/* Animated Progress Dot/Line */}
        <path 
          ref={dotRef} 
          d={TRACK_PATH} 
          fill="none" 
          stroke="#e10600" 
          strokeWidth="18" 
          strokeLinecap="round" 
          strokeDasharray={TOTAL_PATH_LENGTH}
          strokeDashoffset={TOTAL_PATH_LENGTH}
          style={{ transition: "stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)" }}
        />

        <text x="250" y="200" textAnchor="middle" fontSize="28" fill="#fff" fontWeight="bold">
          {inPit ? "BOX" : `L${currentLap}`}
        </text>
        <text x="250" y="230" textAnchor="middle" fontSize="12" fill="#666" fontWeight="600">
          {lapPercent}% COMPLETE
        </text>
      </svg>
    </div>
  );
}