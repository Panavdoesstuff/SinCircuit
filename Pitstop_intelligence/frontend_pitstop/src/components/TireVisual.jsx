import React from 'react';

const COMPOUND_COLORS = {
  soft: "#E24B4A",   // Red
  medium: "#EF9F27", // Yellow
  hard: "#D3D1C7",   // White/Silver
};

export default function TireVisual({ compound = "medium", age = 0 }) {
  const tireColor = COMPOUND_COLORS[compound.toLowerCase()] || "#888";

  return (
    <div style={{
      padding: "1.5rem",
      background: "#151515",
      borderRadius: "16px",
      border: "1px solid #333",
      textAlign: "center",
      minWidth: "200px"
    }}>
      <div style={{
        fontSize: "11px",
        fontWeight: 600,
        textTransform: "uppercase",
        letterSpacing: "0.1em",
        color: "#888",
        marginBottom: "1rem"
      }}>
        Tyre Condition
      </div>

      {/* The Tire Graphic */}
      <div style={{
        width: "140px",
        height: "140px",
        borderRadius: "50%",
        border: `20px solid #222`,
        borderTopColor: tireColor,
        borderBottomColor: tireColor,
        boxShadow: `inset 0 0 20px ${tireColor}33`, // Subtle glow
        margin: "0 auto",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        position: "relative"
      }}>
        <span style={{ fontSize: "24px", fontWeight: "bold", color: "#fff" }}>
          {age}
        </span>
        <span style={{ fontSize: "10px", color: "#888", marginTop: "-4px" }}>
          LAPS
        </span>
      </div>

      <div style={{
        marginTop: "1rem",
        fontSize: "14px",
        fontWeight: "bold",
        color: tireColor,
        textTransform: "uppercase"
      }}>
        {compound} Compound
      </div>
    </div>
  );
}