import { useState, useEffect, useRef, useCallback } from "react";

// ─── Global CSS ───────────────────────────────────────────────────────────────
const FontLoader = () => (
  <style>{`
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500;600&display=swap');
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:       #080a0c;
      --surface:  #0d1117;
      --surface2: #111820;
      --border:   #1e2832;
      --border2:  #2a3848;
      --red:      #e8002d;
      --red-dim:  #8c0018;
      --amber:    #f5a623;
      --green:    #00d47e;
      --blue:     #0099ff;
      --text:     #c8d8e8;
      --text-dim: #4a6070;
      --text-mid: #7a9ab0;
      --mono:     'IBM Plex Mono', monospace;
      --display:  'Rajdhani', sans-serif;
    }
    html, body, #root {
      height: 100%; width: 100%;
      background: var(--bg);
      color: var(--text);
      font-family: var(--mono);
      overflow: hidden;
    }
    body::after {
      content: '';
      position: fixed; inset: 0;
      background: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,.03) 2px, rgba(0,0,0,.03) 4px);
      pointer-events: none; z-index: 9999;
    }
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: var(--surface); }
    ::-webkit-scrollbar-thumb { background: var(--border2); }
    @keyframes pulse-red  { 0%,100%{opacity:1} 50%{opacity:.4} }
    @keyframes blink      { 0%,100%{opacity:1} 50%{opacity:0} }
    @keyframes slide-in   { from{transform:translateY(8px);opacity:0} to{transform:translateY(0);opacity:1} }
    @keyframes sc-flash   { 0%,100%{background:#f5a62322;border-color:var(--amber)} 50%{background:#f5a62344;border-color:#ffd700} }
    @keyframes pause-pulse{ 0%,100%{box-shadow:0 0 8px rgba(245,166,35,.2)} 50%{box-shadow:0 0 24px rgba(245,166,35,.5)} }
    @keyframes glow-in    { from{opacity:0;transform:scale(.9)} to{opacity:1;transform:scale(1)} }
    @keyframes float3d    { 0%,100%{transform:perspective(600px) rotateX(10deg) rotateY(-18deg) translateY(0px)} 50%{transform:perspective(600px) rotateX(10deg) rotateY(-18deg) translateY(-14px)} }
    @keyframes splash-up  { from{opacity:0;transform:translateY(24px)} to{opacity:1;transform:translateY(0)} }
    @keyframes light-pop  { 0%{transform:scale(.8);opacity:.4} 100%{transform:scale(1);opacity:1} }
  `}</style>
);

// ─── Utility ──────────────────────────────────────────────────────────────────
const fmt    = (n, d = 3) => (typeof n === "number" ? n.toFixed(d) : "—");
const fmtGap = (g) => g === 0 ? "LEADER" : `+${fmt(g, 3)}s`;
const COMPOUND_COLOR = { soft:"#e8002d", medium:"#f5c518", hard:"#e8e8e8", inter:"#00c853", wet:"#0099ff" };
const COMPOUND_SHORT = { soft:"S", medium:"M", hard:"H", inter:"I", wet:"W" };

// ─── F1 Car SVG (side profile) ────────────────────────────────────────────────
function F1CarSVG({ color = "#e8002d", width = 340, style = {} }) {
  const height = Math.round(width * 0.445);
  return (
    <svg viewBox="0 0 380 169" width={width} height={height}
      style={{ display:"block", overflow:"visible", ...style }}>
      {/* Front wing */}
      <rect x="8"  y="119" width="84" height="9"  rx="3.5" fill={color} opacity=".96"/>
      <rect x="14" y="114" width="72" height="5"  rx="2"   fill={color} opacity=".55"/>
      <rect x="8"  y="111" width="5"  height="17" rx="2"   fill={color} opacity=".82"/>
      <rect x="87" y="111" width="5"  height="17" rx="2"   fill={color} opacity=".82"/>
      <line x1="30" y1="119" x2="40"  y2="102" stroke={color} strokeWidth="2.5" opacity=".6"/>
      <line x1="72" y1="119" x2="62"  y2="102" stroke={color} strokeWidth="2.5" opacity=".6"/>
      {/* Nose */}
      <path d="M 14 107 Q 12 103 39 96 L 43 107 Z" fill={color} opacity=".72"/>
      <path d="M 39 96 L 83 89 L 83 103 L 43 107 Z" fill={color} opacity=".92"/>
      {/* Body */}
      <path d="M 75 73 Q 102 54 168 47 Q 224 41 282 47 Q 330 51 357 71 L 360 101 Q 342 115 282 118 L 85 118 Q 75 113 75 101 Z" fill={color} opacity=".87"/>
      <rect x="75" y="113" width="285" height="5" rx="2" fill={color} opacity=".5"/>
      {/* Cockpit */}
      <path d="M 192 76 L 197 47 Q 210 33 230 31 Q 250 33 260 47 L 262 73 Z" fill="#04070d" opacity=".92"/>
      <path d="M 200 64 Q 206 41 230 39 Q 250 41 254 62 L 250 70 Q 242 57 230 55 Q 214 57 208 70 Z" fill="#091422" opacity=".75"/>
      {/* Halo */}
      <path d="M 197 73 Q 197 29 230 27 Q 264 29 264 73" stroke={color} strokeWidth="5.5" fill="none" opacity=".93"/>
      <rect x="227" y="25" width="6" height="21" rx="2.5" fill={color}/>
      {/* Sidepod */}
      <path d="M 148 71 Q 162 61 182 59 L 182 97 Q 162 99 148 91 Z" fill="#040710" opacity=".72"/>
      <rect x="152" y="64" width="26" height="31" rx="5" fill="#020407" opacity=".82"/>
      {/* Engine cover */}
      <rect x="264" y="41" width="74" height="15" rx="5" fill={color} opacity=".65"/>
      {/* Rear wing */}
      <rect x="345" y="37" width="5.5" height="80" rx="2.5" fill={color} opacity=".87"/>
      <rect x="325" y="37" width="5.5" height="80" rx="2.5" fill={color} opacity=".6"/>
      <rect x="317" y="37"  width="55" height="12" rx="3"   fill={color}/>
      <rect x="319" y="52"  width="51" height="7"  rx="2.5" fill={color} opacity=".55"/>
      <rect x="330" y="101" width="32" height="5"  rx="2"   fill={color} opacity=".6"/>
      {/* Diffuser */}
      <path d="M 340 118 L 374 118 L 377 138 L 337 138 Z" fill={color} opacity=".42"/>
      {/* Front wheel */}
      <circle cx="90"  cy="133" r="28" fill="#0d0d1a"/>
      <circle cx="90"  cy="133" r="18" fill="#141420"/>
      <circle cx="90"  cy="133" r="10" fill={color} opacity=".42"/>
      <circle cx="90"  cy="133" r="25" fill="none" stroke={color} strokeWidth="1.2" opacity=".18"/>
      {/* Rear wheel */}
      <circle cx="318" cy="133" r="32" fill="#0d0d1a"/>
      <circle cx="318" cy="133" r="21" fill="#141420"/>
      <circle cx="318" cy="133" r="12" fill={color} opacity=".42"/>
      <circle cx="318" cy="133" r="29" fill="none" stroke={color} strokeWidth="1.2" opacity=".18"/>
      {/* Suspension */}
      <line x1="90"  y1="107" x2="130" y2="97"  stroke={color} strokeWidth="2.2" opacity=".28"/>
      <line x1="90"  y1="121" x2="130" y2="113" stroke={color} strokeWidth="2.2" opacity=".28"/>
      <line x1="318" y1="103" x2="280" y2="97"  stroke={color} strokeWidth="2.2" opacity=".28"/>
      <line x1="318" y1="117" x2="280" y2="111" stroke={color} strokeWidth="2.2" opacity=".28"/>
      {/* Antenna */}
      <line x1="228" y1="27" x2="228" y2="7" stroke={color} strokeWidth="1.5" opacity=".7"/>
      <circle cx="228" cy="6" r="2.5" fill={color} opacity=".8"/>
    </svg>
  );
}

// ─── SPLASH SCREEN ────────────────────────────────────────────────────────────
function SplashScreen({ onStart }) {
  const [loading, setLoading]   = useState(false);
  const [lightsOn, setLightsOn] = useState([false,false,false,false,false]);

  const handleClick = () => {
    if (loading) return;
    setLoading(true);

    // Sequence the 5 lights on
    [0,1,2,3,4].forEach(i =>
      setTimeout(() =>
        setLightsOn(p => { const n=[...p]; n[i]=true; return n; }), i * 180)
    );

    // Fire the race start immediately
    onStart();
  };

  return (
    <div style={{
      height: "100vh", width: "100vw",
      background: "var(--bg)",
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      position: "relative", overflow: "hidden", gap: 0,
    }}>
      <FontLoader />

      {/* Subtle grid */}
      <div style={{
        position:"absolute", inset:0, opacity:.035,
        backgroundImage:"linear-gradient(var(--border) 1px,transparent 1px),linear-gradient(90deg,var(--border) 1px,transparent 1px)",
        backgroundSize:"44px 44px", pointerEvents:"none",
      }}/>

      {/* Radial glow behind car */}
      <div style={{
        position:"absolute", top:"50%", left:"50%",
        transform:"translate(-50%, -60%)",
        width:600, height:300,
        background:"radial-gradient(ellipse at center, rgba(232,0,45,.12) 0%, transparent 70%)",
        pointerEvents:"none",
      }}/>

      {/* ── Circuit label ── */}
      <div style={{
        fontSize:9, color:"var(--red)", letterSpacing:"0.5em",
        fontFamily:"var(--mono)", marginBottom:16, opacity:.8,
        animation:"splash-up .6s ease both",
      }}>
        SIN CITY // LAS VEGAS STREET CIRCUIT
      </div>

      {/* ── 3D Car ── */}
      <div style={{
        animation: loading ? "none" : "float3d 4s ease-in-out infinite",
        filter:"drop-shadow(0 0 32px rgba(232,0,45,.55)) drop-shadow(0 12px 20px rgba(0,0,0,.95))",
        marginBottom: 6,
        transformOrigin: "center center",
      }}>
        <F1CarSVG color="#e8002d" width={460} />
      </div>

      {/* Reflection */}
      <div style={{
        width:460, height:40, marginBottom:20,
        background:"linear-gradient(to bottom, rgba(232,0,45,.08), transparent)",
        transform:"scaleY(-1)",
        maskImage:"linear-gradient(to bottom, black 0%, transparent 100%)",
        WebkitMaskImage:"linear-gradient(to bottom, black 0%, transparent 100%)",
        filter:"blur(2px)",
        flexShrink:0,
      }}>
        <F1CarSVG color="#e8002d" width={460}
          style={{ opacity:.18, transform:"scaleY(-1)", display:"block" }} />
      </div>

      {/* ── Title ── */}
      <div style={{ textAlign:"center", marginBottom:22, animation:"splash-up .6s ease .1s both" }}>
        <div style={{
          fontFamily:"var(--display)", fontSize:52, fontWeight:700,
          color:"var(--text)", letterSpacing:".06em", lineHeight:1,
        }}>
          PIT WALL AI
        </div>
        <div style={{ fontSize:10, color:"var(--text-dim)", letterSpacing:".14em", marginTop:4 }}>
          MULTI-AGENT F1 STRATEGY COMMAND CENTRE
        </div>
      </div>

      {/* ── F1 Lights ── */}
      <div style={{ display:"flex", gap:10, marginBottom:26, animation:"splash-up .6s ease .2s both" }}>
        {[0,1,2,3,4].map(i => (
          <div key={i} style={{
            width:38, height:38, borderRadius:"50%",
            background: lightsOn[i] ? "#e8002d" : "#160000",
            boxShadow: lightsOn[i]
              ? "0 0 18px #e8002d, 0 0 36px #e8002d99, inset 0 0 10px #ff000055"
              : "inset 0 0 6px rgba(0,0,0,.7)",
            border:`2px solid ${lightsOn[i] ? "#e8002d" : "#280000"}`,
            transition:"all .06s ease",
            animation: lightsOn[i] ? "light-pop .15s ease" : "none",
          }}/>
        ))}
      </div>

      {/* ── Button ── */}
      <button
        onClick={handleClick}
        disabled={loading}
        style={{
          padding:"13px 56px", borderRadius:2, border:"none",
          background: loading ? "var(--surface2)" : "var(--red)",
          color: loading ? "var(--text-dim)" : "#fff",
          fontFamily:"var(--display)", fontSize:15, fontWeight:700,
          letterSpacing:".22em", textTransform:"uppercase",
          cursor: loading ? "default" : "pointer",
          boxShadow: loading ? "none" : "0 0 40px rgba(232,0,45,.45), 0 4px 16px rgba(0,0,0,.5)",
          transition:"all .25s",
          animation:"splash-up .6s ease .3s both",
        }}
      >
        {loading ? "STARTING..." : "▶ LIGHTS OUT — RACE START"}
      </button>
    </div>
  );
}

// ─── Sub-components (race dashboard) ─────────────────────────────────────────
function DataLabel({ children, style }) {
  return <div style={{ fontSize:9, letterSpacing:".15em", color:"var(--text-dim)", textTransform:"uppercase", fontFamily:"var(--mono)", marginBottom:3, ...style }}>{children}</div>;
}
function DataValue({ children, color, size=13, style }) {
  return <div style={{ fontSize:size, fontWeight:500, color:color||"var(--text)", fontFamily:"var(--mono)", lineHeight:1.2, ...style }}>{children}</div>;
}
function Panel({ children, style, glow }) {
  return <div style={{ background:"var(--surface)", border:`1px solid ${glow||"var(--border)"}`, borderRadius:2, boxShadow:glow?`0 0 14px ${glow}22`:"none", ...style }}>{children}</div>;
}
function PanelHeader({ label, accent, right }) {
  return (
    <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"6px 10px", borderBottom:"1px solid var(--border)", background:"var(--surface2)" }}>
      <div style={{ fontSize:9, letterSpacing:".2em", fontWeight:600, color:accent||"var(--text-dim)", textTransform:"uppercase" }}>{label}</div>
      {right && <div style={{ fontSize:9, color:"var(--text-dim)" }}>{right}</div>}
    </div>
  );
}
function TyreDot({ compound, size=18, age }) {
  const c = COMPOUND_COLOR[compound] || "#888";
  return (
    <div style={{ display:"flex", alignItems:"center", gap:4 }}>
      <div style={{ width:size, height:size, borderRadius:"50%", background:c, display:"flex", alignItems:"center", justifyContent:"center", fontSize:size*.45, fontWeight:700, color:"#000", flexShrink:0 }}>
        {COMPOUND_SHORT[compound]||"?"}
      </div>
      {age!==undefined && <span style={{ fontSize:10, color:"var(--text-dim)" }}>{age}L</span>}
    </div>
  );
}

// ─── HEADER ───────────────────────────────────────────────────────────────────
function Header({ lap, totalLaps, weather, safetycar, connected, raceId, paused, onPause, onResume, autoDebate, onToggleAutoDebate }) {
  const sc = safetycar || {};
  const pct = Math.round(((lap||0)/(totalLaps||50))*100);
  return (
    <div style={{
      height:48, background:"var(--surface2)",
      borderBottom:`1px solid ${paused?"var(--amber)":"var(--border)"}`,
      display:"flex", alignItems:"center", padding:"0 16px", gap:20, flexShrink:0,
      transition:"border-color .3s",
      boxShadow: paused?"0 2px 20px rgba(245,166,35,.18)":"none",
    }}>
      <div style={{ fontFamily:"var(--display)", fontSize:18, fontWeight:700, color:"var(--red)", letterSpacing:".1em", display:"flex", alignItems:"center", gap:8 }}>
        <span style={{ color:"var(--text-dim)", fontSize:11 }}>◆</span>PIT WALL AI
      </div>
      <div style={{ width:1, height:20, background:"var(--border)" }}/>
      <div>
        <DataLabel>Circuit</DataLabel>
        <DataValue size={11}>LAS VEGAS STREET CIRCUIT</DataValue>
      </div>
      <div>
        <DataLabel>Lap</DataLabel>
        <DataValue size={11}>
          <span style={{ color:"var(--amber)", fontSize:16, fontWeight:700 }}>{lap||"—"}</span>
          <span style={{ color:"var(--text-dim)" }}> / {totalLaps||50}</span>
        </DataValue>
      </div>
      <div style={{ width:80, flexShrink:0 }}>
        <div style={{ height:3, background:"var(--border)", borderRadius:2, overflow:"hidden", marginBottom:3 }}>
          <div style={{ height:"100%", width:`${pct}%`, background:"linear-gradient(90deg,var(--amber),var(--red))", borderRadius:2, boxShadow:"0 0 6px rgba(245,166,35,.5)", transition:"width 1s ease" }}/>
        </div>
        <div style={{ fontSize:7, color:"var(--text-dim)", letterSpacing:".15em" }}>{pct}% COMPLETE</div>
      </div>
      <div>
        <DataLabel>Conditions</DataLabel>
        <DataValue size={11} color={weather?.is_wet?"var(--blue)":"var(--green)"}>
          {(weather?.state||"DRY").toUpperCase()}
          {weather?.rain_prob_next_10>0.2 && <span style={{ color:"var(--amber)", marginLeft:6 }}>☂ {Math.round(weather.rain_prob_next_10*100)}%</span>}
        </DataValue>
      </div>
      {sc.active && (
        <div style={{ padding:"3px 10px", borderRadius:2, border:"1px solid var(--amber)", animation:"sc-flash 1s ease-in-out infinite", fontSize:10, fontWeight:600, color:"var(--amber)", letterSpacing:".1em" }}>
          {sc.type} DEPLOYED — {sc.laps_remaining} LAPS
        </div>
      )}
      <div style={{ marginLeft:"auto", display:"flex", alignItems:"center", gap:10 }}>
        {/* ── Auto-debate toggle ── */}
        <button onClick={onToggleAutoDebate} style={{
          padding:"5px 14px", borderRadius:2, cursor:"pointer",
          border:`1px solid ${autoDebate?"var(--amber)":"var(--border2)"}`,
          background:autoDebate?"rgba(245,166,35,.12)":"var(--surface)",
          color:autoDebate?"var(--amber)":"var(--text-dim)",
          fontSize:9, fontWeight:600, fontFamily:"var(--mono)",
          letterSpacing:".1em", textTransform:"uppercase",
          transition:"all .2s",
          display:"flex", alignItems:"center", gap:6,
        }}>
          <span style={{ width:7, height:7, borderRadius:"50%", background:autoDebate?"var(--amber)":"var(--border2)", display:"inline-block", transition:"background .2s" }}/>
          AUTO DEBATE
        </button>

        <button onClick={paused?onResume:onPause} style={{
          padding:"5px 16px", borderRadius:2, cursor:"pointer",
          border:`1px solid ${paused?"var(--amber)":"var(--border2)"}`,
          background:paused?"rgba(245,166,35,.12)":"var(--surface)",
          color:paused?"var(--amber)":"var(--text-mid)",
          fontSize:10, fontWeight:600, fontFamily:"var(--mono)", letterSpacing:".1em", textTransform:"uppercase",
          transition:"all .2s", animation:paused?"pause-pulse 1.8s ease-in-out infinite":"none",
        }}>
          {paused?"▶ RESUME":"⏸ PAUSE"}
        </button>
        <div style={{ width:1, height:20, background:"var(--border)" }}/>
        <div style={{ fontSize:9, color:connected?"var(--green)":"var(--red)", display:"flex", alignItems:"center", gap:5 }}>
          <span style={{ width:6, height:6, borderRadius:"50%", background:connected?"var(--green)":"var(--red)", animation:connected?"none":"pulse-red 1s infinite", display:"inline-block" }}/>
          {connected?"LIVE":"OFFLINE"}
        </div>
        {raceId && <div style={{ fontSize:9, color:"var(--text-dim)" }}>ID: {raceId}</div>}
      </div>
    </div>
  );
}

// ─── STANDINGS ────────────────────────────────────────────────────────────────
function Standings({ standings=[], playerPos }) {
  return (
    <Panel style={{ display:"flex", flexDirection:"column", overflow:"hidden" }}>
      <PanelHeader label="Live Timing" accent="var(--blue)" right={`P${playerPos||"—"}`}/>
      <div style={{ overflow:"auto", flex:1 }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:10 }}>
          <thead>
            <tr style={{ background:"var(--surface2)" }}>
              {["P","Driver","Gap","Tyre","Age","Cliff","Pits"].map(h=>(
                <th key={h} style={{ padding:"4px 6px", textAlign:"left", color:"var(--text-dim)", fontWeight:400, letterSpacing:".08em", fontSize:8, borderBottom:"1px solid var(--border)", fontFamily:"var(--mono)" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {standings.slice(0,20).map((car,i)=>{
              const isPlayer=car.is_player, isPitting=car.is_pitting;
              // New: laps_to_cliff on each car
              const cliff=car.laps_to_cliff ?? 99;
              const cliffColor=cliff<=3?"var(--red)":cliff<=8?"var(--amber)":"var(--text-dim)";
              // New: driver_id field (not 'driver')
              const driverLabel = car.name || car.driver_id || car.driver || "?";
              return (
                <tr key={car.driver_id||car.driver||i} style={{ background:isPlayer?"rgba(232,0,45,.08)":i%2===0?"transparent":"rgba(255,255,255,.01)", borderLeft:isPlayer?"2px solid var(--red)":"2px solid transparent", animation:"slide-in .3s ease" }}>
                  <td style={{ padding:"5px 6px", color:"var(--text-dim)", fontWeight:isPlayer?600:400 }}>{car.position}</td>
                  <td style={{ padding:"5px 6px", color:isPlayer?"var(--red)":"var(--text)", fontWeight:isPlayer?600:400 }}>
                    {driverLabel}
                    {isPitting&&<span style={{ marginLeft:4, fontSize:8, color:"var(--amber)", animation:"pulse-red .8s infinite" }}>▶ PIT</span>}
                  </td>
                  <td style={{ padding:"5px 6px", color:car.position===1?"var(--green)":"var(--text-mid)", fontFamily:"var(--mono)" }}>{fmtGap(car.gap_to_leader)}</td>
                  <td style={{ padding:"5px 6px" }}><TyreDot compound={car.compound} size={14}/></td>
                  <td style={{ padding:"5px 6px", color:"var(--text-mid)" }}>{car.tyre_age}</td>
                  <td style={{ padding:"5px 6px", color:cliffColor, fontWeight:cliff<=5?600:400 }}>{cliff===0?"CLIFF":cliff}</td>
                  <td style={{ padding:"5px 6px", color:"var(--text-dim)" }}>{car.pits_done}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

// ─── PLAYER TELEMETRY ─────────────────────────────────────────────────────────
function PlayerTelemetry({ player, analysis, drsEnabled }) {
  if (!player) return null;
  const a=analysis||{};
  // New backend: ers fields are flat on player, not nested
  const ersMode   = player.ers_mode   || "balanced";
  const ersBatt   = player.ers_battery_pct  ?? 100;
  const ersGain   = player.ers_time_gain_s  ?? 0;
  const fuelKg    = player.fuel_load_kg ?? 105;
  const fuelCost  = player.fuel_time_cost_s ?? 0;
  const ltc       = player.laps_to_cliff ?? 99;
  const pastCliff = player.past_cliff ?? false;

  const statBox=(label,value,color,sub)=>(
    <div style={{ background:"var(--surface2)", border:"1px solid var(--border)", borderRadius:2, padding:"8px 10px" }}>
      <DataLabel>{label}</DataLabel>
      <DataValue size={14} color={color}>{value}</DataValue>
      {sub&&<div style={{ fontSize:9, color:"var(--text-dim)", marginTop:2 }}>{sub}</div>}
    </div>
  );
  const cliffColor=pastCliff?"var(--red)":ltc<=3?"var(--red)":ltc<=8?"var(--amber)":"var(--green)";
  const ersColors={harvest:"var(--amber)",balanced:"var(--text-mid)",attack:"var(--green)",overtake:"var(--red)"};
  return (
    <Panel>
      <PanelHeader label="Your Telemetry" accent="var(--red)"/>
      <div style={{ padding:10, display:"flex", flexDirection:"column", gap:8 }}>
        <div style={{ display:"flex", gap:8, alignItems:"center", background:pastCliff?"rgba(232,0,45,.12)":"var(--surface2)", border:`1px solid ${pastCliff?"var(--red)":"var(--border)"}`, borderRadius:2, padding:"8px 10px", animation:pastCliff?"pulse-red 1s infinite":"none" }}>
          <TyreDot compound={player.compound} size={28}/>
          <div style={{ flex:1 }}>
            <DataLabel>Active Tyre</DataLabel>
            <DataValue size={13} color={COMPOUND_COLOR[(player.compound||"").toLowerCase()]}>{(player.compound||"").toUpperCase()} — {player.tyre_age}L</DataValue>
            <div style={{ fontSize:9, color:cliffColor, marginTop:2, fontWeight:600 }}>
              {pastCliff ? `⚠ ${player.tyre_age - (player.cliff_lap || 24)} LAPS PAST CLIFF` : `CLIFF IN ${ltc} LAPS`}
            </div>
          </div>
          <div style={{ textAlign:"right" }}>
            <DataLabel>Pits done</DataLabel>
            <DataValue size={13} color="var(--text-mid)">{player.pits_done || 0}</DataValue>
          </div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:6 }}>
          {statBox("Fuel",`${fuelKg}kg`,"var(--amber)",`-${fmt(fuelCost,2)}s time`)}
          {statBox("Position",`P${a.player_position||"—"}`,"var(--text)",player.two_compound_rule?"✓ 2-cmpd":"⚡ rule pending")}
          {statBox("Last Lap",`${fmt(player.last_lap_time,2)}s`,"var(--text-mid)")}
        </div>
        <div style={{ background:"var(--surface2)", border:"1px solid var(--border)", borderRadius:2, padding:"8px 10px" }}>
          <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:6 }}>
            <DataLabel style={{ marginBottom:0 }}>ERS — {ersMode.toUpperCase()}</DataLabel>
            <DataValue size={11} color={ersColors[ersMode]||"var(--text-dim)"}>{ersGain>0?"+":""}{fmt(ersGain,2)}s</DataValue>
          </div>
          <div style={{ height:4, background:"var(--border)", borderRadius:2, overflow:"hidden" }}>
            <div style={{ height:"100%", borderRadius:2, width:`${ersBatt}%`, background:ersBatt>40?"var(--green)":ersBatt>15?"var(--amber)":"var(--red)", transition:"width .5s ease" }}/>
          </div>
          <div style={{ fontSize:9, color:"var(--text-dim)", marginTop:3 }}>{fmt(ersBatt,0)}% BATTERY</div>
        </div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:6 }}>
          <div style={{ background:a.player_drs_active?"rgba(0,212,126,0.1)":"var(--surface2)", border:`1px solid ${a.player_drs_active?"var(--green)":"var(--border)"}`, borderRadius:2, padding:"8px 10px" }}>
            <DataLabel>DRS</DataLabel>
            <DataValue size={13} color={a.player_drs_active?"var(--green)":"var(--text-dim)"}>{a.player_drs_active?"OPEN":"CLOSED"}</DataValue>
            {a.gap_to_car_ahead_s!==undefined&&<div style={{ fontSize:9, color:"var(--text-dim)", marginTop:2 }}>Δ ahead: {fmt(a.gap_to_car_ahead_s,3)}s</div>}
          </div>
          <div style={{ background:"var(--surface2)", border:"1px solid var(--border)", borderRadius:2, padding:"8px 10px" }}>
            <DataLabel>Gap to leader</DataLabel>
            <DataValue size={13}>{a.gap_to_leader_s===0?"LEADER":`+${fmt(a.gap_to_leader_s,3)}s`}</DataValue>
          </div>
        </div>
        {a.sc_pit_opportunity&&(
          <div style={{ padding:"8px 10px", borderRadius:2, border:"1px solid var(--amber)", background:"rgba(245,166,35,.1)", fontSize:11, color:"var(--amber)", fontWeight:600, animation:"sc-flash 1s infinite" }}>
            ⚡ SC PIT WINDOW OPEN — FREE STOP AVAILABLE
          </div>
        )}
      </div>
    </Panel>
  );
}


// ─── LAP SPARKLINE ────────────────────────────────────────────────────────────
function LapSparkline({ lapTimes=[] }) {
  if (lapTimes.length<2) return null;
  const w=200,h=40,min=Math.min(...lapTimes),max=Math.max(...lapTimes),range=max-min||1;
  const pts=lapTimes.map((t,i)=>`${(i/(lapTimes.length-1))*w},${h-((t-min)/range)*h}`).join(" ");
  return (
    <Panel>
      <PanelHeader label="Lap Time Trend" accent="var(--amber)"/>
      <div style={{ padding:"8px 10px" }}>
        <svg width={w} height={h} style={{ display:"block", overflow:"visible" }}>
          <polyline points={pts} fill="none" stroke="var(--amber)" strokeWidth={1.5} strokeLinejoin="round"/>
          {lapTimes.map((t,i)=>{ const x=(i/(lapTimes.length-1))*w, y=h-((t-min)/range)*h; return <circle key={i} cx={x} cy={y} r={2.5} fill="var(--amber)"/>; })}
        </svg>
        <div style={{ display:"flex", justifyContent:"space-between", marginTop:4 }}>
          <span style={{ fontSize:9, color:"var(--text-dim)" }}>best: {fmt(Math.min(...lapTimes),3)}s</span>
          <span style={{ fontSize:9, color:"var(--text-dim)" }}>latest: {fmt(lapTimes[lapTimes.length-1],3)}s</span>
        </div>
      </div>
    </Panel>
  );
}

// ─── STRATEGY THREATS ─────────────────────────────────────────────────────────
function StrategyThreats({ analysis }) {
  const a=analysis||{}, threats=a.undercut_threats||[], targets=a.overcut_targets||[];
  if (!threats.length&&!targets.length) return null;
  return (
    <Panel>
      <PanelHeader label="Strategic Alerts" accent="var(--red)"/>
      <div style={{ padding:8, display:"flex", flexDirection:"column", gap:4 }}>
        {threats.map((t,i)=>(
          <div key={i} style={{ padding:"6px 8px", borderRadius:2, background:"rgba(232,0,45,.08)", border:"1px solid var(--red-dim)", fontSize:10 }}>
            <span style={{ color:"var(--red)", fontWeight:600 }}>⚠ UNDERCUT</span>
            <span style={{ color:"var(--text-mid)", marginLeft:6 }}>{t.driver} — {t.gap_behind_s}s behind, {t.threat_in_laps}L</span>
          </div>
        ))}
        {targets.map((t,i)=>(
          <div key={i} style={{ padding:"6px 8px", borderRadius:2, background:"rgba(0,153,255,.08)", border:"1px solid #004480", fontSize:10 }}>
            <span style={{ color:"var(--blue)", fontWeight:600 }}>↑ OVERCUT</span>
            <span style={{ color:"var(--text-mid)", marginLeft:6 }}>{t.driver} — {t.gap_ahead_s}s ahead, {t.window_laps}L</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ─── ADVICE HISTORY LOG ───────────────────────────────────────────────────────
function AdviceHistory({ adviceLog=[] }) {
  if (!adviceLog || adviceLog.length === 0) return null;
  
  const outcomeColors = {
    "gained_position_or_time": "var(--green)",
    "neutral": "var(--text-dim)",
    "marginal_loss": "var(--amber)",
    "player_correct": "var(--green)",
    "position_loss": "var(--red)"
  };

  const outcomeLabels = {
    "gained_position_or_time": "✓ Brilliant move (gained track position)",
    "neutral": "— No net gain",
    "marginal_loss": "⚠ Costly call (slight time loss)",
    "player_correct": "✓ Good instincts (ignoring advice paid off)",
    "position_loss": "✗ Poor call (lost time/position by ignoring)"
  };

  // Only show resolved advice or explicitly followed choices
  const history = adviceLog.filter(a => a.outcome || a.followed !== null).reverse().slice(0, 4);

  if (history.length === 0) return null;

  return (
    <Panel>
      <PanelHeader label="Strategy Impact Log" accent="var(--blue)"/>
      <div style={{ padding:8, display:"flex", flexDirection:"column", gap:6 }}>
        {history.map((adv, i) => (
          <div key={i} style={{ 
            padding: "8px 10px", borderRadius: 2, 
            background: "var(--surface2)",
            borderLeft: `2px solid ${adv.followed ? "var(--blue)" : "var(--border2)"}`,
            fontSize: 10
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, letterSpacing: "0.05em", color: "var(--text-mid)" }}>
              <span>LAP {adv.lap} • {adv.recommendation}</span>
              <span style={{ fontWeight: 600, color: adv.followed ? "var(--blue)" : "var(--text-dim)" }}>
                {adv.followed ? "FOLLOWED" : "IGNORED"}
              </span>
            </div>
            {adv.outcome ? (
               <div style={{ color: outcomeColors[adv.outcome] || "var(--text)", fontWeight: 500 }}>
                 {outcomeLabels[adv.outcome] || adv.outcome.replace(/_/g, " ")}
               </div>
            ) : (
               <div style={{ color: "var(--text-dim)", fontStyle: "italic" }}>Awaiting outcome...</div>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ─── CONTROLS ─────────────────────────────────────────────────────────────────
function Controls({ onPit, onErs, onDebate, debating, ersMode }) {
  const [compound, setCompound] = useState("hard");
  const compounds=["soft","medium","hard","inter","wet"];
  const ersModes=["harvest","balanced","attack","overtake"];
  return (
    <Panel>
      <PanelHeader label="Controls" accent="var(--text-dim)"/>
      <div style={{ padding:10, display:"flex", flexDirection:"column", gap:10 }}>
        <div>
          <DataLabel>Pit Stop — Compound</DataLabel>
          <div style={{ display:"flex", gap:4, marginBottom:6 }}>
            {compounds.map(c=>(
              <button key={c} onClick={()=>setCompound(c)} style={{
                flex:1, padding:"5px 0", borderRadius:2, cursor:"pointer",
                border:`1px solid ${compound===c?COMPOUND_COLOR[c]:"var(--border)"}`,
                background:compound===c?`${COMPOUND_COLOR[c]}22`:"var(--surface2)",
                color:compound===c?COMPOUND_COLOR[c]:"var(--text-dim)",
                fontSize:10, fontWeight:600, fontFamily:"var(--mono)", transition:"all .15s",
              }}>{COMPOUND_SHORT[c]}</button>
            ))}
          </div>
          <button onClick={()=>onPit(compound)} style={{
            width:"100%", padding:"8px 0", borderRadius:2, background:"var(--red)", border:"none",
            color:"#fff", fontSize:11, fontWeight:700, fontFamily:"var(--display)",
            letterSpacing:".1em", cursor:"pointer", textTransform:"uppercase",
            boxShadow:"0 0 16px rgba(232,0,45,.3)",
          }}>▶ BOX BOX BOX</button>
        </div>
        <div>
          <DataLabel>ERS Mode</DataLabel>
          <div style={{ display:"flex", gap:4 }}>
            {ersModes.map(m=>{
              const colors={harvest:"var(--amber)",balanced:"var(--text-mid)",attack:"var(--blue)",overtake:"var(--green)"};
              return (
                <button key={m} onClick={()=>onErs(m)} style={{
                  flex:1, padding:"5px 0", borderRadius:2, cursor:"pointer",
                  border:`1px solid ${ersMode===m?colors[m]:"var(--border)"}`,
                  background:ersMode===m?`${colors[m]}22`:"var(--surface2)",
                  color:ersMode===m?colors[m]:"var(--text-dim)",
                  fontSize:8, fontFamily:"var(--mono)", textTransform:"uppercase", transition:"all .15s",
                }}>{m}</button>
              );
            })}
          </div>
        </div>
        <button onClick={onDebate} disabled={debating} style={{
          width:"100%", padding:"8px 0", borderRadius:2,
          background:debating?"var(--surface2)":"transparent",
          border:`1px solid ${debating?"var(--border)":"var(--amber)"}`,
          color:debating?"var(--text-dim)":"var(--amber)",
          fontSize:10, fontWeight:600, fontFamily:"var(--display)",
          letterSpacing:".12em", cursor:debating?"not-allowed":"pointer",
          textTransform:"uppercase", transition:"all .2s",
        }}>{debating?"⟳ AGENTS DELIBERATING...":"⬡ REQUEST STRATEGY DEBATE"}</button>
      </div>
    </Panel>
  );
}

// ─── AGENT PANEL ──────────────────────────────────────────────────────────────
function AgentPanel({ debate, nextDebateLap, currentLap }) {
  const d=debate||{};
  const agents=[
    { key:"engineer_rec", label:"Race Engineer",   icon:"🔧", color:"var(--amber)" },
    { key:"tyre_rec",     label:"Tyre Strategist", icon:"🏎", color:"var(--red)"   },
    { key:"weather_rec",  label:"Race Director",   icon:"📡", color:"var(--blue)"  },
    { key:"rival_rec",    label:"Field Analyst",   icon:"👁", color:"var(--green)" },
  ];
  const confColor={ HIGH:"var(--green)", MEDIUM:"var(--amber)", LOW:"var(--red)" };
  const hasData=agents.some(a=>d[a.key]);
  const lapsToDebate=nextDebateLap>currentLap?nextDebateLap-currentLap:5;

  return (
    <Panel style={{ display:"flex", flexDirection:"column", overflow:"hidden" }}>
      <PanelHeader label="Pit Wall Agents" accent="var(--amber)"
        right={d.confidence?<span style={{ color:confColor[d.confidence]||"var(--text-dim)" }}>{d.confidence} CONFIDENCE</span>:<span style={{ fontSize:8 }}>AUTO IN {lapsToDebate}L</span>}
      />
      <div style={{ overflow:"auto", flex:1, padding:8, display:"flex", flexDirection:"column", gap:6 }}>
        {agents.map(agent=>{
          const text=d[agent.key]||"";
          const isActive=d.streaming_agent===agent.label;
          return (
            <div key={agent.key} style={{ background:"var(--surface2)", border:`1px solid ${isActive?agent.color:text?agent.color+"44":"var(--border)"}`, borderRadius:2, boxShadow:isActive?`0 0 10px ${agent.color}44`:"none", transition:"all .3s" }}>
              <div style={{ display:"flex", alignItems:"center", gap:6, padding:"5px 8px", borderBottom:text?"1px solid var(--border)":"none" }}>
                <span style={{ fontSize:12 }}>{agent.icon}</span>
                <span style={{ fontSize:9, color:agent.color, fontWeight:600, letterSpacing:".1em" }}>{agent.label.toUpperCase()}</span>
                {isActive&&<span style={{ marginLeft:"auto", fontSize:9, color:agent.color, animation:"blink .8s infinite" }}>●</span>}
                {text&&!isActive&&<span style={{ marginLeft:"auto", fontSize:8, color:agent.color, opacity:.6 }}>✓</span>}
              </div>
              {text&&<div style={{ padding:"6px 8px", fontSize:10, color:"var(--text-mid)", lineHeight:1.6, fontFamily:"var(--mono)", animation:"slide-in .3s ease", whiteSpace:"pre-wrap" }}>{text}</div>}
            </div>
          );
        })}

        {d.final_decision&&(
          <div style={{ background:"rgba(232,0,45,.06)", border:"1px solid var(--red-dim)", borderRadius:2, padding:"10px 12px", animation:"slide-in .4s ease" }}>
            <div style={{ fontSize:9, color:"var(--red)", fontWeight:600, letterSpacing:".15em", marginBottom:6 }}>◆ PIT WALL DIRECTOR — FINAL CALL</div>
            <div style={{ fontSize:11, color:"var(--text)", lineHeight:1.6, marginBottom:8 }}>{d.final_decision}</div>
            {d.dominant_factor&&<div style={{ fontSize:9, color:"var(--text-dim)", marginBottom:4 }}><span style={{ color:"var(--amber)" }}>DOMINANT: </span>{d.dominant_factor}</div>}
            {d.risk&&<div style={{ fontSize:9, color:"var(--text-dim)", marginBottom:4 }}><span style={{ color:"var(--red)" }}>RISK: </span>{d.risk}</div>}
            {d.contingency&&<div style={{ fontSize:9, color:"var(--text-dim)" }}><span style={{ color:"var(--blue)" }}>CONTINGENCY: </span>{d.contingency}</div>}
          </div>
        )}

        {/* Idle: car graphic */}
        {!hasData&&!d.final_decision&&(
          <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:12, paddingTop:16, paddingBottom:16 }}>
            <div style={{ filter:"drop-shadow(0 0 14px rgba(232,0,45,.4))", animation:"float3d 4s ease-in-out infinite" }}>
              <F1CarSVG color="#e8002d" width={230}/>
            </div>
            <div style={{ textAlign:"center" }}>
              <div style={{ fontSize:9, color:"var(--text-dim)", letterSpacing:".05em", marginBottom:3 }}>Awaiting agent debate</div>
              <div style={{ fontSize:8, color:"var(--text-dim)", opacity:.5 }}>Auto-triggers every 5 laps</div>
            </div>
            <div style={{ padding:"5px 14px", borderRadius:2, border:"1px solid rgba(232,0,45,.3)", background:"rgba(232,0,45,.06)", fontSize:8, fontFamily:"var(--mono)", color:"var(--text-dim)", textAlign:"center" }}>
              <span style={{ color:"var(--red)" }}>NEXT DEBATE</span> — LAP {nextDebateLap}<br/>
              <span style={{ fontSize:7 }}>{lapsToDebate} LAPS TO GO</span>
            </div>
          </div>
        )}
      </div>
    </Panel>
  );
}

// ─── PAUSE OVERLAY ────────────────────────────────────────────────────────────
function PauseOverlay({ onResume }) {
  return (
    <div style={{ position:"absolute", inset:0, zIndex:50, background:"rgba(8,10,12,.88)", backdropFilter:"blur(3px)", display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", border:"1px solid var(--amber)", animation:"pause-pulse 2s ease-in-out infinite" }}>
      <div style={{ fontSize:9, color:"var(--amber)", letterSpacing:".4em", fontFamily:"var(--mono)", marginBottom:10, opacity:.8 }}>⏸ RACE PAUSED</div>
      <div style={{ fontFamily:"var(--display)", fontSize:30, fontWeight:700, color:"var(--text)", letterSpacing:".05em", marginBottom:6 }}>STRATEGY WINDOW</div>
      <div style={{ fontSize:10, color:"var(--text-dim)", letterSpacing:".1em", textAlign:"center", marginBottom:24 }}>Analyse telemetry · Consult agents · Plan your move</div>
      <button onClick={onResume} style={{ padding:"10px 36px", borderRadius:2, background:"var(--amber)", border:"none", color:"#000", fontFamily:"var(--display)", fontSize:14, fontWeight:700, letterSpacing:".2em", cursor:"pointer", textTransform:"uppercase" }}>▶ RESUME RACE</button>
    </div>
  );
}

// ─── RADIO MESSAGE ────────────────────────────────────────────────────────────
function RadioMessage({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div onClick={onDismiss} style={{ position:"fixed", bottom:20, left:"50%", transform:"translateX(-50%)", background:"var(--red)", color:"#fff", padding:"12px 24px", borderRadius:2, fontFamily:"var(--display)", fontSize:14, fontWeight:700, letterSpacing:".08em", textAlign:"center", maxWidth:600, zIndex:1000, cursor:"pointer", boxShadow:"0 0 40px rgba(232,0,45,.5)" }}>
      <span style={{ fontSize:10, opacity:.8, display:"block", marginBottom:4 }}>◀ TEAM RADIO ▶</span>
      {message}
    </div>
  );
}

// ─── RACE SUMMARY DEBRIEF ───────────────────────────────────────────────────
function RaceSummary({ summary, onNewRace }) {
  if (!summary) return null;
 
  const gradeColor = {
    A: "var(--green)", B: "var(--amber)",
    C: "var(--amber)", D: "var(--red)", F: "var(--red)"
  };
 
  const posColor = (p) => p > 0 ? "var(--green)" : p < 0 ? "var(--red)" : "var(--text-dim)";
 
  return (
    <div style={{
      position: "fixed", inset: 0,
      background: "rgba(8,10,12,0.97)",
      display: "flex", alignItems: "center", justifyContent: "center",
      zIndex: 500, padding: 24, overflow: "auto",
    }}>
      <div style={{ maxWidth: 780, width: "100%", maxHeight: "100vh", padding: "40px 0" }}>
 
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            fontFamily: "var(--display)", fontSize: 11, fontWeight: 600,
            color: "var(--red)", letterSpacing: "0.4em", marginBottom: 8,
          }}>
            RACE DEBRIEF
          </div>
          <div style={{
            fontFamily: "var(--display)", fontSize: 42, fontWeight: 700,
            color: "var(--text)",
          }}>
            P{summary.final_position} — {summary.strategy_grade} STRATEGY
          </div>
          <div style={{
            fontFamily: "var(--mono)", fontSize: 12, color: "var(--text-dim)",
            marginTop: 8, lineHeight: 1.7,
          }}>
            {summary.verdict}
          </div>
        </div>
 
        {/* Stats grid */}
        <div style={{
          display: "grid", gridTemplateColumns: "repeat(4, 1fr)",
          gap: 8, marginBottom: 20,
        }}>
          {[
            ["Final Position",    `P${summary.final_position}`,
             summary.final_position <= 8 ? "var(--green)" : "var(--text)"],
            ["Positions Gained",
             `${summary.positions_gained_total >= 0 ? "+" : ""}${summary.positions_gained_total}`,
             posColor(summary.positions_gained_total)],
            ["Strategy Grade",    summary.strategy_grade,
             gradeColor[summary.strategy_grade] || "var(--text)"],
            ["Advice Follow Rate",`${summary.advice_follow_rate_pct ?? summary.advice_follow_rate ?? 0}%`,
             (summary.advice_follow_rate_pct ?? summary.advice_follow_rate ?? 0) >= 70 ? "var(--green)" : "var(--amber)"],
            ["Best Lap",          `${summary.best_lap_time}s`,   "var(--text)"],
            ["Avg Lap",           `${summary.average_lap_time}s`, "var(--text-dim)"],
            ["Total Pit Stops",   summary.total_pit_stops,        "var(--text)"],
            ["From Strategy",     `${summary.positions_from_strategy >= 0 ? "+" : ""}${summary.positions_from_strategy || 0} pos`, "var(--blue)"],
          ].map(([label, value, color]) => (
            <div key={label} style={{
              background: "var(--surface)", border: "1px solid var(--border)",
              borderRadius: 2, padding: "10px 12px",
            }}>
              <div style={{
                fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.12em",
                textTransform: "uppercase", marginBottom: 4,
              }}>{label}</div>
              <div style={{
                fontSize: 18, fontWeight: 600, color: color || "var(--text)",
                fontFamily: "var(--display)",
              }}>{value}</div>
            </div>
          ))}
        </div>
 
        {/* Pit stop breakdown — new backend uses pit_history */}
        {(summary.pit_stop_details || summary.pit_history || []).length > 0 && (
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 2, padding: "12px 14px", marginBottom: 16,
          }}>
            <div style={{
              fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.15em",
              textTransform: "uppercase", marginBottom: 10,
            }}>Pit Stop Breakdown</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {(summary.pit_stop_details || summary.pit_history || []).map((pit, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 12,
                  fontSize: 11, padding: "5px 0",
                  borderBottom: i < (summary.pit_stop_details || summary.pit_history || []).length - 1
                    ? "1px solid var(--border)" : "none",
                }}>
                  <span style={{ color: "var(--text-dim)", minWidth: 50 }}>
                    Lap {pit.lap}
                  </span>
                  <span style={{ color: "var(--text-mid)" }}>
                    {pit.from?.toUpperCase()} → {pit.to?.toUpperCase()}
                  </span>
                  <span style={{ color: "var(--amber)" }}>
                    {pit.stationary_s}s stationary
                  </span>
                  <span style={{ color: "var(--text-dim)" }}>
                    ({pit.cost_s}s total cost)
                  </span>
                  <span style={{
                    marginLeft: "auto", fontSize: 9, fontWeight: 600,
                    color: pit.followed_advice ? "var(--green)" : "var(--red)",
                  }}>
                    {pit.followed_advice ? "✓ FOLLOWED ADVICE" : "✗ IGNORED ADVICE"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
 
        {/* Key moments */}
        {summary.key_moments && summary.key_moments.length > 0 && (
          <div style={{
            background: "var(--surface)", border: "1px solid var(--border)",
            borderRadius: 2, padding: "12px 14px", marginBottom: 20,
          }}>
            <div style={{
              fontSize: 9, color: "var(--text-dim)", letterSpacing: "0.15em",
              textTransform: "uppercase", marginBottom: 10,
            }}>Key Race Moments</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              {summary.key_moments.map((m, i) => (
                <div key={i} style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "6px 8px", borderRadius: 2,
                  background: m.position_impact > 0
                    ? "rgba(0,212,126,0.05)"
                    : m.position_impact < 0
                    ? "rgba(232,0,45,0.05)"
                    : "transparent",
                  border: `1px solid ${
                    m.position_impact > 0 ? "rgba(0,212,126,0.2)"
                    : m.position_impact < 0 ? "rgba(232,0,45,0.2)"
                    : "var(--border)"
                  }`,
                }}>
                  <span style={{
                    fontSize: 9, color: "var(--text-dim)", minWidth: 44,
                  }}>
                    LAP {m.lap}
                  </span>
                  <span style={{ fontSize: 11, color: "var(--text)", flex: 1 }}>
                    {m.event}
                  </span>
                  {m.position_impact !== 0 && (
                    <span style={{
                      fontSize: 11, fontWeight: 600,
                      color: m.position_impact > 0 ? "var(--green)" : "var(--red)",
                      minWidth: 40, textAlign: "right",
                    }}>
                      {m.position_impact > 0 ? `+${m.position_impact}` : m.position_impact} pos
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
 
        {/* SC deployments */}
        {summary.sc_deployments && summary.sc_deployments.length > 0 && (
          <div style={{
            background: "rgba(245,166,35,0.05)",
            border: "1px solid rgba(245,166,35,0.2)",
            borderRadius: 2, padding: "10px 14px", marginBottom: 20,
            fontSize: 11,
          }}>
            <span style={{ color: "var(--amber)", fontWeight: 600 }}>SC DEPLOYMENTS: </span>
            <span style={{ color: "var(--text-dim)" }}>
              {summary.sc_deployments.map(d => `${d.type} lap ${d.lap}`).join(" • ")}
            </span>
          </div>
        )}
 
        <button onClick={onNewRace} style={{
          width: "100%", padding: "14px 0", borderRadius: 2,
          background: "var(--red)", border: "none",
          color: "#fff", fontSize: 13, fontWeight: 700,
          fontFamily: "var(--display)", letterSpacing: "0.2em",
          cursor: "pointer", textTransform: "uppercase",
        }}>
          ▶ NEW RACE
        </button>
      </div>
    </div>
  );
}

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
const WS_BASE  = import.meta.env.VITE_WS_URL  || "ws://localhost:8000";
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [raceId,      setRaceId]      = useState(null);
  const [state,       setState]       = useState(null);
  const [autoDebate,  setAutoDebate]  = useState(true);
  const [connected,setConnected]= useState(false);
  const [debate,   setDebate]   = useState({});
  const [debating, setDebating] = useState(false);
  const [paused,   setPaused]   = useState(false);
  const [radioMsg, setRadioMsg] = useState(null);

  const wsRef            = useRef(null);
  const sseRef           = useRef(null);
  const lastDebateLapRef = useRef(0);

  const currentLap    = state?.lap || 0;
  const nextDebateLap = currentLap + (5 - ((currentLap % 5) || 5));

  // ── Start Race ──────────────────────────────────────────────────────────────
  const startRace = useCallback(async () => {
    try {
      const res  = await fetch(`${API_BASE}/race/start`, { method:"POST" });
      const data = await res.json();
      const id   = data.race_id;

      setState(data.state);     // set data first
      setDebate({});
      setRadioMsg(null);
      setDebating(false);
      setPaused(false);
      lastDebateLapRef.current = 0;

      const ws = new WebSocket(`${WS_BASE}/race/${id}/live`);
      wsRef.current = ws;
      ws.onopen    = () => setConnected(true);
      ws.onclose   = () => setConnected(false);
      ws.onmessage = (evt) => {
        const msg = JSON.parse(evt.data);
        if (msg.type === "tick" || msg.type === "connected") setState(msg.state);
        if (msg.type === "race_finished") { setState(msg.state); setConnected(false); }
      };

      setRaceId(id);            // this flips the screen
    } catch (e) {
      console.error("startRace failed:", e);
    }
  }, []);

  // ── Auto-debate every 5 laps (only when toggle is on) ───────────────────
  useEffect(() => {
    if (!raceId || !state || !autoDebate) return;
    const lap = state.lap || 0;
    if (lap > 0 && lap % 5 === 0 && lap !== lastDebateLapRef.current && !debating) {
      lastDebateLapRef.current = lap;
      triggerDebate(raceId);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state?.lap, raceId]);

  // ── Pit ──────────────────────────────────────────────────────────────────
  const handlePit = useCallback(async (compound) => {
    if (!raceId) return;
    try {
      const res  = await fetch(`${API_BASE}/race/${raceId}/pit?compound=${compound}`, { method:"POST" });
      const data = await res.json();
      if (data.state) setState(data.state);
    } catch (e) { console.error("Pit failed", e); }
  }, [raceId]);

  // ── ERS ──────────────────────────────────────────────────────────────────
  const handleErs = useCallback(async (mode) => {
    if (!raceId) return;
    try { await fetch(`${API_BASE}/race/${raceId}/ers?mode=${mode}`, { method:"POST" }); }
    catch (e) { console.error("ERS failed", e); }
  }, [raceId]);

  // ── Pause / Resume ────────────────────────────────────────────────────────
  const handlePause = useCallback(async () => {
    if (!raceId) return;
    try { await fetch(`${API_BASE}/race/${raceId}/pause`, { method:"POST" }); setPaused(true); }
    catch (e) { console.error("Pause failed", e); }
  }, [raceId]);

  const handleResume = useCallback(async () => {
    if (!raceId) return;
    try { await fetch(`${API_BASE}/race/${raceId}/resume`, { method:"POST" }); setPaused(false); }
    catch (e) { console.error("Resume failed", e); }
  }, [raceId]);

  // ── Debate (SSE) ──────────────────────────────────────────────────────────
  const triggerDebate = useCallback((id) => {
    if (!id || debating) return;
    setDebating(true);
    setDebate({});
    if (sseRef.current) sseRef.current.close();

    const sse = new EventSource(`${API_BASE}/race/${id}/stream`);
    sseRef.current = sse;

    const keyMap = {
      "Race Engineer":"engineer_rec","Tyre Strategist":"tyre_rec",
      "Race Director":"weather_rec","Field Analyst":"rival_rec",
    };

    sse.onmessage = (evt) => {
      const msg = JSON.parse(evt.data);
      if (msg.type === "agent_start") setDebate(p=>({...p, streaming_agent:msg.agent}));
      if (msg.type === "token") {
        const key = keyMap[msg.agent];
        if (key) setDebate(p=>({...p, [key]:(p[key]||"")+msg.token, streaming_agent:msg.agent}));
      }
      if (msg.type === "agent_done") setDebate(p=>({...p, streaming_agent:null}));
      if (msg.type === "summary") {
        setDebate(p=>({...p, final_decision:msg.decision, streaming_agent:null}));
        if (msg.radio) { setRadioMsg(msg.radio); setTimeout(()=>setRadioMsg(null), 6000); }
      }
      if (msg.type === "done") { setDebating(false); sse.close(); }
    };
    sse.onerror = () => { setDebating(false); sseRef.current?.close(); };
  }, [debating]);

  const handleDebate = useCallback(() => triggerDebate(raceId), [raceId, triggerDebate]);

  // ── Cleanup ───────────────────────────────────────────────────────────────
  useEffect(() => () => { wsRef.current?.close(); sseRef.current?.close(); }, []);

  // ══ SCREENS ════════════════════════════════════════════════════════════════

  // Splash — shown until raceId + state are ready
  if (!raceId || !state) {
    return <SplashScreen onStart={startRace} />;
  }

  // Race Dashboard
  const s        = state || {};
  const player   = s.player || {};
  const analysis = s.analysis || {};
  // New backend shape: sc fields are top-level, not nested under safety_car
  const sc       = { active: s.sc_active, deployments: s.sc_deployments || [], laps_remaining: s.sc_laps_remaining };
  const ersMode  = player.ers_mode || player.ers?.mode || "balanced";

  return (
    <>
      <FontLoader />
      <div style={{ height:"100vh", display:"flex", flexDirection:"column", background:"var(--bg)", overflow:"hidden" }}>

        <Header
          lap={s.lap} totalLaps={s.total_laps}
          weather={s.weather} safetycar={sc}
          connected={connected} raceId={raceId}
          circuit={s.circuit} scriptId={s.script_id}
          paused={paused} onPause={handlePause} onResume={handleResume}
          autoDebate={autoDebate} onToggleAutoDebate={()=>setAutoDebate(v=>!v)}
        />

        <div style={{ flex:1, display:"grid", overflow:"hidden", gridTemplateColumns:"260px 1fr 300px", gap:6, padding:6 }}>

          {/* LEFT */}
          <div style={{ display:"flex", flexDirection:"column", gap:6, overflow:"auto" }}>
            <PlayerTelemetry player={player} analysis={analysis} drsEnabled={s.drs_enabled}/>
            <StrategyThreats analysis={analysis}/>
            <AdviceHistory adviceLog={s.advice_log} />
            <LapSparkline lapTimes={player.recent_lap_times||[]}/>
            <Controls onPit={handlePit} onErs={handleErs} onDebate={handleDebate} debating={debating} ersMode={ersMode}/>
          </div>

          {/* CENTRE */}
          <div style={{ display:"flex", flexDirection:"column", gap:6, overflow:"hidden", position:"relative" }}>
            <Standings standings={s.standings||[]} playerPos={analysis.player_position}/>

            <Panel style={{ padding:"8px 12px", flexShrink:0 }}>
              <div style={{ display:"flex", gap:24, flexWrap:"wrap" }}>
                {[
                  ["Track Temp",  `${s.track_temp_c?.toFixed(1)}°C`],
                  ["Track Evo",   `-${s.track_evolution_s?.toFixed(3)}s`],
                  ["Pit Delta",   `${s.circuit_info?.pit_lane_delta_s}s`],
                  ["SC Active",   sc.active ? "⚠ YES" : "No"],
                  ["SC Deploys",  sc.deployments?.length || 0],
                  ["Advice Log",  player.advice_followed != null ? `${player.advice_followed}✓ ${player.advice_ignored}✗` : "—"],
                ].map(([l,v])=>(
                  <div key={l}>
                    <div style={{ fontSize:9, color:"var(--text-dim)", textTransform:"uppercase", letterSpacing:".1em" }}>{l}</div>
                    <div style={{ fontSize:11, fontFamily:"var(--mono)", color: l==="SC Active" && sc.active ? "var(--amber)" : undefined }}>{v}</div>
                  </div>
                ))}
              </div>
            </Panel>

            {paused && <PauseOverlay onResume={handleResume}/>}
          </div>

          {/* RIGHT */}
          <AgentPanel debate={debate} nextDebateLap={nextDebateLap} currentLap={currentLap}/>
        </div>

        {/* Finish overlay */}
        {s.finished && (
          <RaceSummary summary={s.race_summary} onNewRace={()=>{ setRaceId(null); setState(null); }} />
        )}

        <RadioMessage message={radioMsg} onDismiss={()=>setRadioMsg(null)}/>
      </div>
    </>
  );
}