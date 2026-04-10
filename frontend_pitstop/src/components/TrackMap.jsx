import React, { useEffect, useRef } from "react";

// The path for our circuit
const TRACK_PATH = "M 100 200 Q 100 50 250 50 Q 400 50 400 200 Q 400 350 250 350 Q 100 350 100 200";
const TOTAL_PATH_LENGTH = 800; 

export default function TrackMap({ currentLap = 1, totalLaps = 58, inPit = false }) {
  const dotRef = useRef(null);

  useEffect(() => {
    if (!dotRef.current) return;
    // Calculate progress as a percentage of the total race
    const progress = currentLap / totalLaps;
    // strokeDashoffset: 0 is the end of the line, TOTAL_PATH_LENGTH is the start
    const offset = TOTAL_PATH_LENGTH * (1 - progress);
    dotRef.current.style.strokeDashoffset = offset;
  }, [currentLap, totalLaps]);

  const lapProgress = ((currentLap / totalLaps) * 100).toFixed(0);

  return (
    <div style={{
      padding: "1.5rem",
      background: "#151515",
      borderRadius: "16px",
      border: "1px solid #333",
      textAlign: "center"
    }}>
      <div style={{
        fontSize: "11px",
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.1em",
        color: "#888",
        marginBottom: "1rem"
      }}>
        Track Position — Lap {currentLap}/{totalLaps}
      </div>

      <svg viewBox="0 0 500 400" style={{ width: "100%", maxWidth: "350px", margin: "0 auto" }}>
        {/* Grey Background Track */}
        <path 
          d={TRACK_PATH} 
          fill="none" 
          stroke="#333" 
          strokeWidth="15" 
          strokeLinecap="round" 
        />
        
        {/* Animated Progress Path (The 'Car' Trail) */}
        <path 
          ref={dotRef} 
          d={TRACK_PATH} 
          fill="none" 
          stroke="#E24B4A" 
          strokeWidth="15" 
          strokeLinecap="round" 
          strokeDasharray={TOTAL_PATH_LENGTH}
          strokeDashoffset={TOTAL_PATH_LENGTH}
          style={{ transition: "stroke-dashoffset 0.8s ease-in-out" }}
        />

        {/* Center Labels */}
        <text x="250" y="200" textAnchor="middle" fontSize="24" fill="#fff" fontWeight="bold">
          {inPit ? "PITTING" : `L${currentLap}`}
        </text>
        <text x="250" y="225" textAnchor="middle" fontSize="12" fill="#666" textTransform="uppercase">
          {lapProgress}% Complete
        </text>
      </svg>
    </div>
  );
}